"""Gumroad license-key unlock for quiz-plan sites.

Flow: a buyer pastes the license key from their Gumroad receipt on /unlock.
We verify it server-side with Gumroad's public endpoint
POST https://api.gumroad.com/v2/licenses/verify (no API token needed), store a
hashed record in the `unlocks` table, and keep the key in the buyer's own
signed session cookie so we can re-check it at most once every 24 hours.
Cancelled, failed, ended, refunded, charged-back, or disputed purchases lock
again. If Gumroad is unreachable we keep access open for up to 72 hours since
the last good check.

Configuration (env vars override the defaults below):
  GUMROAD_PRODUCT_PERMALINK  e.g. "flqzi" (from https://solvfix.gumroad.com/l/flqzi)
  GUMROAD_PRODUCT_ID         Gumroad product id; resolved from the public
                             /l/<permalink>.json page when not set
  GUMROAD_SELLER_URL         default https://solvfix.gumroad.com
When no permalink/id is known, /unlock says checkout is coming soon.

Full license keys are never logged or stored server-side (only a SHA-256 hash
and the last 4 characters).
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from flask import flash, redirect, render_template, request, session, url_for

log = logging.getLogger("unlock")

VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"
DEFAULT_SELLER_URL = "https://solvfix.gumroad.com"
RECHECK_SECONDS = 24 * 3600
FAIL_OPEN_SECONDS = 72 * 3600
ATTEMPT_WINDOW = 15 * 60
MAX_ATTEMPTS = 8
KEY_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")

# Known live listings (public data from each product's /l/<permalink>.json).
PRODUCTS: dict[str, dict[str, str]] = {
    "shelfspeak": {"permalink": "flqzi", "product_id": "y9fl2bZ6Y0g5bdSic5kdAQ=="},
    "signmatch": {"permalink": "udyxf", "product_id": "M19gM9PFlPCGXFAlWnhe0Q=="},
    "cuetrail": {"permalink": "ascykk", "product_id": "hl02TsSJsiwsDtUj5--bCw=="},
    "replypath": {"permalink": "zccwvk", "product_id": "Fm9Tt45v7EeBM7FQrYF0Dg=="},
    "turnday": {"permalink": "gbzwxh", "product_id": "ThFYQQ8cBU4FZDypwSA2dA=="},
    "prooflane": {"permalink": "xugyi", "product_id": "kh0-oMpUp1KhcjCoarv66Q=="},
    "doorwell": {"permalink": "iouqzv", "product_id": "LGvpa5aPo8_6doLk7vx_zQ=="},
    "chalkday": {"permalink": "pvjow", "product_id": "akd7sD5q0fOasKcHi7vLyQ=="},
}


def key_hash(key: str) -> str:
    return hashlib.sha256(key.strip().upper().encode()).hexdigest()


def key_hint(key: str) -> str:
    k = key.strip()
    return f"…{k[-4:]}" if len(k) >= 4 else "…"


def _now() -> float:
    return time.time()


def _iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts is not None else _now(), timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _parse_ts(value: Any) -> float | None:
    if not value:
        return None
    s = str(value).strip().replace("Z", "+00:00")
    for fmt in (None, "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            dt = datetime.fromisoformat(s) if fmt is None else datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    return 0.0  # unparseable but present: treat as already ended


@dataclass
class Result:
    status: str  # active | invalid | inactive | wrong_product | rate_limited | error | not_configured
    reason: str = ""
    email: str = ""
    sale_id: str = ""
    recurrence: str = ""
    access_until: float | None = None
    raw: dict = field(default_factory=dict)


def http_post(url: str, data: dict[str, str], timeout: float = 8.0) -> tuple[int, dict]:
    """POST form data, return (status_code, json). Raises OSError on network failure."""
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={"Accept": "application/json", "User-Agent": "quiz-plans-unlock/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read().decode() or "{}")
        except Exception:
            payload = {}
        return e.code, payload


def http_get_json(url: str, timeout: float = 6.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "quiz-plans-unlock/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")


def interpret(status_code: int, payload: dict, expected_product_id: str = "", now: float | None = None) -> Result:
    now = _now() if now is None else now
    if status_code == 429:
        return Result("rate_limited", "Gumroad is busy right now.")
    if status_code >= 500:
        return Result("error", f"Gumroad returned {status_code}.")
    if status_code == 404 or not payload.get("success"):
        return Result("invalid", payload.get("message") or "License not found.")
    p = payload.get("purchase") or {}
    if expected_product_id and p.get("product_id") and p.get("product_id") != expected_product_id:
        return Result("wrong_product", "Key belongs to a different product.")
    res = Result(
        "active",
        email=(p.get("email") or "").strip().lower(),
        sale_id=str(p.get("sale_id") or p.get("id") or ""),
        recurrence=str(p.get("recurrence") or ""),
        raw={k: p.get(k) for k in ("product_id", "recurrence", "refunded", "chargebacked", "disputed", "dispute_won", "subscription_cancelled_at", "subscription_ended_at", "subscription_failed_at")},
    )
    if p.get("refunded") or p.get("chargebacked") or (p.get("disputed") and not p.get("dispute_won")):
        res.status, res.reason = "inactive", "refunded"
        return res
    ends = [t for t in (_parse_ts(p.get(k)) for k in ("subscription_cancelled_at", "subscription_ended_at", "subscription_failed_at")) if t is not None]
    if ends:
        end = min(ends)
        if end <= now:
            res.status, res.reason = "inactive", "membership_ended"
        else:
            res.access_until = end  # cancelled but paid through `end`
    return res


class Unlocker:
    def __init__(self, brand: dict, store, q: Callable, x: Callable, verifier: Callable | None = None):
        self.brand = brand
        self.slug = brand["slug"]
        self.store = store
        self.q, self.x = q, x
        self._verifier = verifier
        self._lock = threading.Lock()
        self._ip_attempts: dict[str, list[float]] = {}
        self._resolved_id: str | None = None
        self._resolve_failed_at = 0.0

    # ---------- config ----------
    def permalink(self) -> str:
        env = (os.environ.get("GUMROAD_PRODUCT_PERMALINK") or "").strip()
        if env:
            return env.rsplit("/l/", 1)[-1].strip("/")
        if self.brand.get("gumroad_permalink"):
            return self.brand["gumroad_permalink"]
        if PRODUCTS.get(self.slug, {}).get("permalink"):
            return PRODUCTS[self.slug]["permalink"]
        url = (self.brand.get("checkout_url") or "").strip()
        m = re.search(r"/l/([A-Za-z0-9_-]+)", url)
        return m.group(1) if m else ""

    def seller_url(self) -> str:
        return (os.environ.get("GUMROAD_SELLER_URL") or DEFAULT_SELLER_URL).rstrip("/")

    def product_url(self) -> str:
        url = (self.brand.get("checkout_url") or "").strip()
        if url:
            return url
        pl = self.permalink()
        return f"{self.seller_url()}/l/{pl}" if pl else ""

    def product_id(self) -> str:
        env = (os.environ.get("GUMROAD_PRODUCT_ID") or "").strip()
        if env:
            return env
        pl = self.permalink()
        known = PRODUCTS.get(self.slug, {})
        if known.get("product_id") and known.get("permalink") == pl:
            return known["product_id"]
        if self.brand.get("gumroad_product_id"):
            return self.brand["gumroad_product_id"]
        if self._resolved_id:
            return self._resolved_id
        if pl and _now() - self._resolve_failed_at > 600:
            try:
                data = http_get_json(f"{self.seller_url()}/l/{pl}.json")
                if data.get("id"):
                    self._resolved_id = str(data["id"])
                    return self._resolved_id
            except Exception:
                log.warning("unlock: could not resolve product id for %s", self.slug)
            self._resolve_failed_at = _now()
        return ""

    def configured(self) -> bool:
        return bool(self.permalink() or (os.environ.get("GUMROAD_PRODUCT_ID") or "").strip())

    # ---------- Gumroad ----------
    def verify(self, key: str) -> Result:
        if not self.configured():
            return Result("not_configured")
        pid = self.product_id()
        data = {"license_key": key.strip(), "increment_uses_count": "false"}
        if pid:
            data["product_id"] = pid
        else:
            data["product_permalink"] = self.permalink()
        try:
            if self._verifier is not None:
                code, payload = self._verifier(VERIFY_URL, data)
            else:
                code, payload = http_post(VERIFY_URL, data)
        except Exception as e:  # network error, timeout, bad JSON
            log.warning("unlock: gumroad verify network error for %s key %s: %s", self.slug, key_hint(key), type(e).__name__)
            return Result("error", "network")
        res = interpret(code, payload or {}, expected_product_id=pid)
        log.info("unlock: verify %s key %s -> %s %s", self.slug, key_hint(key), res.status, res.reason)
        return res

    # ---------- rate limiting ----------
    def _too_many(self) -> bool:
        now = _now()
        ip = (request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0]).strip()
        with self._lock:
            hits = [t for t in self._ip_attempts.get(ip, []) if now - t < ATTEMPT_WINDOW]
            hits.append(now)
            self._ip_attempts[ip] = hits
            if len(self._ip_attempts) > 5000:
                self._ip_attempts.clear()
        s_hits = [t for t in session.get("unlock_attempts", []) if now - t < ATTEMPT_WINDOW]
        s_hits.append(now)
        session["unlock_attempts"] = s_hits[-MAX_ATTEMPTS * 2:]
        return len(hits) > MAX_ATTEMPTS or len(s_hits) > MAX_ATTEMPTS

    # ---------- storage ----------
    def save(self, key: str, res: Result, quiz_key: str | None):
        h = key_hash(key)
        row = self.q("SELECT id FROM unlocks WHERE key_hash=?", (h,), one=True)
        now = _iso()
        if row:
            self.x(
                "UPDATE unlocks SET purchaser_email=?, quiz_session_key=COALESCE(CAST(? AS TEXT), quiz_session_key), status=?, last_checked_at=?, verified_at=? WHERE key_hash=?",
                (res.email, quiz_key, res.status, now, now, h),
            )
        else:
            self.x(
                "INSERT INTO unlocks(key_hash, key_hint, purchaser_email, quiz_session_key, sale_id, recurrence, status, verified_at, last_checked_at, created) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (h, key_hint(key), res.email, quiz_key, res.sale_id, res.recurrence, res.status, now, now, now),
            )

    def link_session(self, quiz_key: str):
        st = session.get("unlock") or {}
        if not st.get("h") or not quiz_key or st.get("linked") == quiz_key:
            return
        try:
            self.x("UPDATE unlocks SET quiz_session_key=? WHERE key_hash=?", (quiz_key, st["h"]))
            st["linked"] = quiz_key
            session["unlock"] = st
        except Exception:
            log.exception("unlock: could not link session")

    def mark(self, h: str, status: str):
        try:
            self.x("UPDATE unlocks SET status=?, last_checked_at=? WHERE key_hash=?", (status, _iso(), h))
        except Exception:
            log.exception("unlock: could not update status")

    # ---------- session state ----------
    def is_unlocked(self) -> bool:
        st = session.get("unlock")
        if not st or not st.get("k"):
            return False
        now = _now()
        h = st.get("h") or key_hash(st["k"])
        try:
            row = self.q("SELECT status FROM unlocks WHERE key_hash=?", (h,), one=True)
            if row and row["status"] == "revoked":
                session.pop("unlock", None)
                return False
        except Exception:
            pass
        until = st.get("until")
        if until and now >= until:
            st["checked"] = 0  # paid-through date passed; force a re-check
        if now - float(st.get("checked", 0)) < RECHECK_SECONDS:
            return True
        res = self.verify(st["k"])
        if res.status == "active":
            st.update(checked=now, ok=now, until=res.access_until)
            session["unlock"] = st
            self.mark(h, "active")
            return True
        if res.status in ("error", "rate_limited"):
            if now - float(st.get("ok", 0)) < FAIL_OPEN_SECONDS:
                return True
            return False
        # invalid / inactive / wrong product: lock again
        self.mark(h, res.reason or res.status)
        session.pop("unlock", None)
        session["unlock_notice"] = "inactive"
        return False

    def pop_notice(self) -> str:
        return session.pop("unlock_notice", "")


def full_sections_for(brand: dict, answers: dict, plan: dict) -> list[dict]:
    try:
        import full_plan  # type: ignore
    except ImportError:
        full_plan = None
    sections = []
    if full_plan is not None and hasattr(full_plan, "full_sections"):
        try:
            sections = full_plan.full_sections(brand["slug"], answers or {}, plan or {})
        except Exception:
            log.exception("unlock: full plan generation failed")
            sections = []
    if not sections:
        sections = [{"title": s.get("title", ""), "body": s.get("teaser", "")} for s in plan.get("locked_sections", [])]
    return sections


def register_unlock(app, brand: dict, store, q, x, check_form_token, session_key, load_plan, load_answers, verifier=None) -> Unlocker:
    u = Unlocker(brand, store, q, x, verifier=verifier)
    app.unlocker = u

    MESSAGES = {
        "invalid": "We couldn’t find that license key for {name}. Copy it again from your Gumroad receipt email (it looks like XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX) and try once more.",
        "wrong_product": "That key belongs to a different product. Use the key from your {name} receipt.",
        "inactive_refunded": "That purchase was refunded or disputed, so the full plan is locked. If this looks wrong, reply to your Gumroad receipt.",
        "inactive_membership_ended": "That membership has ended or failed to renew. Restart it from your Gumroad library, then unlock again.",
        "rate_limited": "Gumroad is busy right now. Please wait a minute and try again.",
        "error": "We couldn’t reach Gumroad to check your key. Please try again in a minute.",
        "too_many": "Too many attempts. Please wait 15 minutes and try again.",
        "format": "That doesn’t look like a license key. Paste the key from your Gumroad receipt (letters, numbers, and dashes).",
    }

    @app.route("/unlock", methods=["GET", "POST"])
    def unlock():
        ctx = {
            "configured": u.configured(),
            "product_url": u.product_url(),
            "unlocked": False,
            "has_plan": False,
            "error": "",
            "notice": u.pop_notice(),
        }
        try:
            ctx["has_plan"] = bool(load_plan()) if session.get("quiz_key") else False
        except Exception:
            ctx["has_plan"] = False
        if request.method == "GET":
            ctx["unlocked"] = u.is_unlocked() if session.get("unlock") else False
            return render_template("unlock.html", **ctx)

        check_form_token()
        if not ctx["configured"]:
            return render_template("unlock.html", **ctx)
        key = (request.form.get("license_key") or "").strip().replace(" ", "")
        email = (request.form.get("email") or "").strip().lower()[:200]
        if u._too_many():
            ctx["error"] = MESSAGES["too_many"]
            return render_template("unlock.html", **ctx), 429
        if not KEY_RE.fullmatch(key):
            ctx["error"] = MESSAGES["format"]
            return render_template("unlock.html", **ctx), 400
        res = u.verify(key)
        if res.status != "active":
            k = f"inactive_{res.reason}" if res.status == "inactive" else res.status
            ctx["error"] = MESSAGES.get(k, MESSAGES["invalid"]).format(name=brand["name"])
            return render_template("unlock.html", **ctx), (503 if res.status in ("error", "rate_limited") else 400)

        # Link a quiz session: current cookie first, then purchaser email (or typed email) in our records.
        quiz_key = None
        current = session.get("quiz_key")
        if current and load_plan():
            quiz_key = current
        else:
            for addr in [a for a in (res.email, email) if a]:
                row = q(
                    "SELECT session_key FROM quiz_sessions WHERE lower(email)=? AND plan_json IS NOT NULL ORDER BY id DESC LIMIT 1",
                    (addr,), one=True,
                )
                if row:
                    quiz_key = row["session_key"]
                    session["quiz_key"] = quiz_key
                    break
        u.save(key, res, quiz_key)
        now = _now()
        session["unlock"] = {"k": key, "h": key_hash(key), "checked": now, "ok": now, "until": res.access_until}
        session.pop("unlock_attempts", None)
        if res.email:
            session["checkout_email"] = res.email
        if quiz_key:
            flash("Your full plan is unlocked.")
            return redirect(url_for("results"))
        ctx.update(unlocked=True, has_plan=False)
        return render_template("unlock.html", **ctx)

    return u
