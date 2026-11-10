"""Shared Flask quiz→plan→paywall engine for local quiz-plan SaaS prototypes."""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from db import open_store
from unlock import full_sections_for, register_unlock

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def create_app(brand: dict[str, Any]) -> Flask:
    """brand keys: name, slug, tagline, port, secret_env, admin_env, db_env,
    questions (list), generate_plan(answers)->dict, pricing, colors, fonts,
    disclaimer_short, audience_line, how_steps, faq, sample_peek_bullets.
    """
    app = Flask(
        brand["slug"],
        template_folder=str(Path(brand["root"]) / "templates"),
        static_folder=str(Path(brand["root"]) / "static"),
    )
    app.secret_key = (
        os.environ.get("SECRET_KEY")
        or os.environ.get(brand["secret_env"])
        or f"dev-{brand['slug']}-change-me"
    )
    app.config["BRAND"] = brand
    store = open_store(slug=brand["slug"], root=brand["root"], db_env=brand.get("db_env"))
    store.init()

    def get_db():
        if "db" not in g:
            g.db = store.connect()
        return g.db

    @app.teardown_appcontext
    def close_db(_=None):
        db = g.pop("db", None)
        if db:
            db.close()

    def q(sql, args=(), one=False):
        return store.query(sql, args, one=one, conn=get_db())

    def x(sql, args=()):
        return store.execute(sql, args, conn=get_db())

    def ensure_form_token():
        if "form_token" not in session:
            session["form_token"] = secrets.token_urlsafe(32)
        return session["form_token"]

    def check_form_token():
        token = request.form.get("form_token", "")
        expected = session.get("form_token", "")
        if not token or not expected or not secrets.compare_digest(token, expected):
            abort(400)

    def session_key():
        if "quiz_key" not in session:
            session["quiz_key"] = secrets.token_urlsafe(16)
        return session["quiz_key"]

    def load_answers() -> dict:
        row = q("SELECT answers_json FROM quiz_sessions WHERE session_key=?", (session_key(),), one=True)
        if not row:
            return {}
        return json.loads(row["answers_json"] or "{}")

    def save_answers(answers: dict):
        key = session_key()
        existing = q("SELECT id FROM quiz_sessions WHERE session_key=?", (key,), one=True)
        payload = json.dumps(answers)
        if existing:
            x(
                "UPDATE quiz_sessions SET answers_json=?, updated=? WHERE session_key=?",
                (payload, utc_now(), key),
            )
        else:
            x(
                "INSERT INTO quiz_sessions(session_key, answers_json, created, updated) VALUES(?,?,?,?)",
                (key, payload, utc_now(), utc_now()),
            )

    def save_plan(plan: dict):
        x(
            "UPDATE quiz_sessions SET plan_json=?, updated=? WHERE session_key=?",
            (json.dumps(plan), utc_now(), session_key()),
        )

    def load_plan() -> dict | None:
        row = q("SELECT plan_json FROM quiz_sessions WHERE session_key=?", (session_key(),), one=True)
        if not row or not row["plan_json"]:
            return None
        return json.loads(row["plan_json"])

    def checkout_href(email: str | None = None) -> str:
        base = (brand.get("checkout_url") or "").strip()
        if not base:
            return ""
        parts = urlsplit(base)
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query["wanted"] = "true"
        if email:
            query["email"] = email
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    def current_checkout_email() -> str:
        return (session.get("checkout_email") or session.get("founding_email") or "").strip()

    def priced(email: str | None = None) -> list[dict[str, Any]]:
        href = checkout_href(email)
        rows = []
        for item in brand["pricing"]:
            row = dict(item)
            if "price" not in row and "intro" in row:
                row["price"] = row["intro"]
            row["checkout_href"] = href
            rows.append(row)
        return rows

    @app.context_processor
    def inject_brand():
        ensure_form_token()
        email = current_checkout_email()
        return {
            "brand": brand,
            "form_token": session["form_token"],
            "year": datetime.now().year,
            "checkout_email": email,
            "checkout_href": checkout_href(email or None),
        }

    unlocker = register_unlock(
        app, brand, store, q, x, check_form_token, session_key, load_plan, load_answers,
        verifier=brand.get("gumroad_verifier"),
    )

    questions = brand["questions"]

    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/quiz")
    def quiz_start():
        session.pop("quiz_key", None)
        session_key()
        save_answers({})
        return redirect(url_for("quiz_step", n=1))

    @app.route("/quiz/<int:n>", methods=["GET", "POST"])
    def quiz_step(n: int):
        total = len(questions)
        if n < 1 or n > total:
            return redirect(url_for("quiz_step", n=1))
        answers = load_answers()
        qdef = questions[n - 1]

        if request.method == "POST":
            check_form_token()
            action = request.form.get("action", "next")
            if action == "back":
                return redirect(url_for("quiz_step", n=max(1, n - 1)))
            raw = request.form.getlist("answer") if qdef.get("multi") else request.form.get("answer", "").strip()
            if qdef.get("multi"):
                if not raw:
                    flash("Please choose at least one option.")
                    return render_template(
                        "quiz.html",
                        q=qdef,
                        n=n,
                        total=total,
                        progress=max(3, int((n - 1) / total * 100)) if n > 1 else 3,
                        answers=answers,
                    )
                answers[qdef["id"]] = raw
            else:
                if not raw and not qdef.get("optional"):
                    flash("Please choose an answer to continue.")
                    return render_template(
                        "quiz.html",
                        q=qdef,
                        n=n,
                        total=total,
                        progress=max(3, int((n - 1) / total * 100)) if n > 1 else 3,
                        answers=answers,
                    )
                answers[qdef["id"]] = raw
            if qdef.get("text_followup"):
                follow = request.form.get("followup", "").strip()
                if follow:
                    answers[qdef["id"] + "_detail"] = follow[:200]
            save_answers(answers)
            if n >= total:
                plan = brand["generate_plan"](answers)
                save_plan(plan)
                session["plan_ready"] = True
                return redirect(url_for("computing"))
            return redirect(url_for("quiz_step", n=n + 1))

        # skip ahead guard: require prior answers except optional
        for i in range(n - 1):
            if questions[i]["id"] not in answers and not questions[i].get("optional"):
                return redirect(url_for("quiz_step", n=i + 1))

        return render_template(
            "quiz.html",
            q=qdef,
            n=n,
            total=total,
            progress=max(3, int((n - 1) / total * 100)) if n > 1 else 3,
            answers=answers,
        )

    @app.get("/computing")
    def computing():
        if not session.get("plan_ready"):
            return redirect(url_for("quiz_start"))
        return render_template("computing.html")

    @app.get("/results")
    def results():
        plan = load_plan()
        answers = load_answers()
        if not plan:
            return redirect(url_for("quiz_start"))
        unlocked = unlocker.is_unlocked()
        if unlocked:
            unlocker.link_session(session_key())
        return render_template(
            "results.html",
            plan=plan,
            answers=answers,
            locked=not unlocked,
            unlocked=unlocked,
            full_sections=full_sections_for(brand, answers, plan) if unlocked else [],
            unlock_notice="" if unlocked else unlocker.pop_notice(),
        )

    @app.get("/paywall")
    def paywall():
        plan = load_plan()
        if not plan:
            return redirect(url_for("quiz_start"))
        email = current_checkout_email()
        return render_template("paywall.html", plan=plan, pricing=priced(email or None))

    @app.route("/founding", methods=["GET", "POST"])
    def founding():
        plan = load_plan()
        answers = load_answers()
        if not plan:
            return redirect(url_for("quiz_start"))
        if request.method == "POST":
            check_form_token()
            email = request.form.get("email", "").strip().lower()
            name = request.form.get("name", "").strip()[:80]
            tier = request.form.get("tier", brand["pricing"][0]["id"])
            if "@" not in email or "." not in email.split("@")[-1]:
                flash("Enter a valid email so we can save your plan before checkout.")
                return render_template(
                    "founding.html",
                    plan=plan,
                    pricing=priced(),
                    selected=tier,
                )
            x(
                "INSERT INTO leads(email, name, plan_tier, answers_json, plan_json, source, created) VALUES(?,?,?,?,?,?,?)",
                (email, name, tier, json.dumps(answers), json.dumps(plan), "checkout", utc_now()),
            )
            x(
                "UPDATE quiz_sessions SET email=?, updated=? WHERE session_key=?",
                (email, utc_now(), session_key()),
            )
            session["founding_email"] = email
            session["checkout_email"] = email
            session["checkout_tier"] = tier
            if request.form.get("next") == "paywall":
                return redirect(url_for("paywall"))
            return redirect(url_for("founding_thanks"))
        selected = request.args.get("tier", brand["pricing"][0]["id"])
        email = current_checkout_email()
        return render_template(
            "founding.html",
            plan=plan,
            pricing=priced(email or None),
            selected=selected,
        )

    @app.get("/founding/thanks")
    def founding_thanks():
        email = current_checkout_email()
        return render_template(
            "thanks.html",
            email=email,
            pricing=priced(email or None),
            selected=session.get("checkout_tier", ""),
        )

    @app.get("/plan/print")
    def plan_print():
        plan = load_plan()
        answers = load_answers()
        if not plan:
            return redirect(url_for("quiz_start"))
        # Preview-only printable: preview sections unlocked; full sections marked locked
        unlocked = unlocker.is_unlocked()
        return render_template(
            "print.html",
            plan=plan,
            answers=answers,
            preview_only=not unlocked,
            unlocked=unlocked,
            full_sections=full_sections_for(brand, answers, plan) if unlocked else [],
        )

    @app.get("/privacy")
    def privacy():
        return render_template("legal.html", kind="privacy")

    @app.get("/terms")
    def terms():
        return render_template("legal.html", kind="terms")

    @app.get("/disclaimer")
    def disclaimer():
        return render_template("legal.html", kind="disclaimer")

    def admin_required(f):
        @wraps(f)
        def wrapped(*a, **k):
            pwd = os.environ.get("ADMIN_PASSWORD") or os.environ.get(brand["admin_env"], "")
            provided = request.headers.get("X-Admin-Password") or request.args.get("password") or request.form.get("password") or session.get("admin_ok")
            if not pwd:
                abort(403)
            if provided == pwd or session.get("admin_ok") == pwd:
                session["admin_ok"] = pwd
                return f(*a, **k)
            if request.method == "POST":
                check_form_token()
                if request.form.get("password") == pwd:
                    session["admin_ok"] = pwd
                    return redirect(url_for("admin"))
                flash("Wrong password.")
            return render_template("admin_login.html"), 401

        return wrapped

    @app.route("/admin", methods=["GET", "POST"])
    @admin_required
    def admin():
        leads = q("SELECT * FROM leads ORDER BY id DESC LIMIT 200")
        sessions = q("SELECT id, session_key, email, created, updated FROM quiz_sessions ORDER BY id DESC LIMIT 100")
        return render_template("admin.html", leads=leads, sessions=sessions)

    @app.get("/health")
    def health():
        payload = {"ok": True, "brand": brand["name"], "db": store.backend}
        if store.backend == "postgres":
            payload["schema"] = store.schema
        try:
            store.ping()
            payload["db_ok"] = True
        except Exception:
            payload["db_ok"] = False
        return payload

    # expose helpers for tests
    app.db_q = q
    app.db_x = x
    app.db_store = store
    app.db_path = store.sqlite_path
    return app
