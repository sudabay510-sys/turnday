"""Tests for the Gumroad license-key unlock (Gumroad calls are mocked)."""
from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

import pytest

os.environ.pop("DATABASE_URL", None)
os.environ.pop("DATABASE_SCHEMA", None)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
SLUG = ROOT.name if (ROOT / "brands.py").exists() else "shelfspeak"
UP = SLUG.upper()

from brands import BRANDS  # noqa: E402
from quiz_engine import create_app  # noqa: E402
import unlock as unlock_mod  # noqa: E402

KEY = "ABCD1234-EF567890-12345678-9ABCDEF0"
PID = "test-product-id=="


def purchase(**over):
    p = {
        "product_id": PID, "email": "buyer@example.com", "sale_id": "sale1", "recurrence": "monthly",
        "refunded": False, "chargebacked": False, "disputed": False, "dispute_won": False,
        "subscription_cancelled_at": None, "subscription_ended_at": None, "subscription_failed_at": None,
        "license_key": KEY,
    }
    p.update(over)
    return 200, {"success": True, "uses": 0, "purchase": p}


class Fake:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, data):
        self.calls.append(dict(data))
        r = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(r, Exception):
            raise r
        return r


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_SCHEMA", raising=False)
    monkeypatch.setenv(f"{UP}_DB", str(tmp_path / "app.db"))
    monkeypatch.setenv("GUMROAD_PRODUCT_PERMALINK", "testperm")
    monkeypatch.setenv("GUMROAD_PRODUCT_ID", PID)
    brand = dict(BRANDS[SLUG])
    brand["root"] = str(ROOT)
    application = create_app(brand)
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    with app.test_client() as c:
        yield c


def token(client, path="/unlock"):
    html = client.get(path).data.decode()
    marker = 'name="form_token" value="'
    return html.split(marker, 1)[1].split('"', 1)[0]


def finish_quiz(client):
    client.get("/quiz")
    qs = BRANDS[SLUG]["questions"]
    tok = token(client, "/quiz/1")
    for n, q in enumerate(qs, start=1):
        data = {"form_token": tok, "action": "next"}
        if q.get("options"):
            data["answer"] = [q["options"][0]["id"]] if q.get("multi") else q["options"][0]["id"]
        else:
            data["answer"] = "Sample"
        r = client.post(f"/quiz/{n}", data=data)
        assert r.status_code in (302, 303), (n, r.status_code)
    assert client.get("/results").status_code == 200


def do_unlock(client, key=KEY, email=""):
    return client.post("/unlock", data={"form_token": token(client), "license_key": key, "email": email})


def test_unlock_page_renders(client):
    r = client.get("/unlock")
    assert r.status_code == 200
    assert b"license key" in r.data.lower()
    assert b'name="license_key"' in r.data


def test_unlock_requires_csrf(client):
    client.get("/unlock")
    r = client.post("/unlock", data={"license_key": KEY})
    assert r.status_code == 400


def test_bad_format_key_friendly_error(client):
    r = do_unlock(client, key="not a key!!")
    assert r.status_code == 400
    assert b"look like a license key" in r.data


def test_paywall_and_results_link_to_unlock(client):
    finish_quiz(client)
    assert b"Already paid? Unlock your plan" in client.get("/results").data
    assert b"Already paid? Unlock your plan" in client.get("/paywall").data


def test_terms_mention_license_key(client):
    assert b"license key on your Gumroad receipt" in client.get("/terms").data


def test_valid_key_unlocks_full_plan(app, client, caplog):
    fake = Fake(purchase())
    app.unlocker._verifier = fake
    finish_quiz(client)
    assert b"Your full plan" not in client.get("/results").data
    with caplog.at_level(logging.DEBUG):
        r = do_unlock(client)
    assert r.status_code in (302, 303) and r.headers["Location"].endswith("/results")
    html = client.get("/results").data.decode()
    assert "Your full plan" in html
    assert "Full plan locked" not in html
    assert fake.calls[0]["product_id"] == PID
    assert fake.calls[0]["increment_uses_count"] == "false"
    # full key never logged or stored
    assert KEY not in caplog.text
    rows = app.db_q("SELECT * FROM unlocks")
    assert len(rows) == 1
    row = dict(rows[0])
    assert KEY not in " ".join(str(v) for v in row.values())
    assert row["key_hash"] == unlock_mod.key_hash(KEY)
    assert row["status"] == "active" and row["purchaser_email"] == "buyer@example.com"
    assert row["quiz_session_key"]
    # print view shows full plan too
    assert b"Printable preview only" not in client.get("/plan/print").data


def test_unlock_without_session_asks_to_retake(app, client):
    app.unlocker._verifier = Fake(purchase(email="nobody@example.com"))
    r = do_unlock(client)
    assert r.status_code == 200
    assert b"Retake the quiz" in r.data
    finish_quiz(client)
    assert b"Your full plan" in client.get("/results").data


def test_unlock_matches_purchaser_email_to_saved_plan(app):
    app.unlocker._verifier = Fake(purchase(email="saved@example.com"))
    with app.test_client() as c1:
        finish_quiz(c1)
        tok = token(c1, "/founding")
        c1.post("/founding", data={"form_token": tok, "email": "saved@example.com", "name": "", "tier": BRANDS[SLUG]["pricing"][0]["id"]})
    with app.test_client() as c2:  # new device, no quiz session
        r = do_unlock(c2)
        assert r.status_code in (302, 303)
        assert b"Your full plan" in c2.get("/results").data


def test_invalid_key(app, client):
    app.unlocker._verifier = Fake((404, {"success": False, "message": "That license does not exist for the provided product."}))
    r = do_unlock(client)
    assert r.status_code == 400
    assert b"couldn\xe2\x80\x99t find that license key" in r.data
    assert app.db_q("SELECT * FROM unlocks") == []


def test_wrong_product(app, client):
    app.unlocker._verifier = Fake(purchase(product_id="other=="))
    r = do_unlock(client)
    assert r.status_code == 400 and b"different product" in r.data


def test_cancelled_membership_is_locked(app, client):
    app.unlocker._verifier = Fake(purchase(subscription_cancelled_at="2020-01-01T00:00:00Z"))
    r = do_unlock(client)
    assert r.status_code == 400 and b"membership has ended" in r.data


def test_cancelled_but_paid_through_future_still_unlocked(app, client):
    app.unlocker._verifier = Fake(purchase(subscription_cancelled_at="2999-01-01T00:00:00Z"))
    finish_quiz(client)
    r = do_unlock(client)
    assert r.status_code in (302, 303)


def test_failed_payment_is_locked(app, client):
    app.unlocker._verifier = Fake(purchase(subscription_failed_at="2021-05-01T00:00:00Z"))
    assert do_unlock(client).status_code == 400


def test_refunded_is_locked(app, client):
    app.unlocker._verifier = Fake(purchase(refunded=True))
    r = do_unlock(client)
    assert r.status_code == 400 and b"refunded" in r.data


def test_chargeback_is_locked(app, client):
    app.unlocker._verifier = Fake(purchase(chargebacked=True))
    assert do_unlock(client).status_code == 400


def test_network_error_on_unlock(app, client):
    app.unlocker._verifier = Fake(OSError("boom"))
    r = do_unlock(client)
    assert r.status_code == 503 and b"couldn\xe2\x80\x99t reach Gumroad" in r.data


def test_rate_limited_by_gumroad(app, client):
    app.unlocker._verifier = Fake((429, {}))
    r = do_unlock(client)
    assert r.status_code == 503 and b"busy" in r.data


def test_too_many_attempts(app, client):
    app.unlocker._verifier = Fake((404, {"success": False}))
    codes = [do_unlock(client).status_code for _ in range(unlock_mod.MAX_ATTEMPTS + 2)]
    assert codes[-1] == 429


def _age(client, seconds, ok_seconds=None):
    with client.session_transaction() as s:
        st = s["unlock"]
        st["checked"] = time.time() - seconds
        st["ok"] = time.time() - (ok_seconds if ok_seconds is not None else seconds)
        s["unlock"] = st


def test_reverify_after_24h_locks_cancelled(app, client):
    fake = Fake(purchase())
    app.unlocker._verifier = fake
    finish_quiz(client)
    do_unlock(client)
    assert b"Your full plan" in client.get("/results").data
    assert len(fake.calls) == 1  # no re-check inside 24h
    _age(client, 25 * 3600)
    app.unlocker._verifier = Fake(purchase(subscription_cancelled_at="2020-01-01T00:00:00Z"))
    html = client.get("/results").data
    assert b"Your full plan" not in html and b"Full plan locked" in html
    assert app.db_q("SELECT status FROM unlocks", one=True)["status"] == "membership_ended"


def test_reverify_network_error_fails_open_then_closes(app, client):
    app.unlocker._verifier = Fake(purchase())
    finish_quiz(client)
    do_unlock(client)
    app.unlocker._verifier = Fake(OSError("down"))
    _age(client, 25 * 3600, ok_seconds=30 * 3600)
    assert b"Your full plan" in client.get("/results").data  # within 72h of last good check
    _age(client, 80 * 3600)
    assert b"Your full plan" not in client.get("/results").data


def test_interpret_one_time_purchase_active():
    code, payload = purchase(recurrence=None)
    for k in ("subscription_cancelled_at", "subscription_ended_at", "subscription_failed_at"):
        payload["purchase"].pop(k)
    assert unlock_mod.interpret(code, payload, PID).status == "active"


def test_not_configured_says_coming_soon(tmp_path, monkeypatch):
    monkeypatch.delenv("GUMROAD_PRODUCT_PERMALINK", raising=False)
    monkeypatch.delenv("GUMROAD_PRODUCT_ID", raising=False)
    monkeypatch.setenv(f"{UP}_DB", str(tmp_path / "nc.db"))
    brand = dict(BRANDS[SLUG])
    brand["root"] = str(ROOT)
    brand.pop("checkout_url", None)
    monkeypatch.setitem(unlock_mod.PRODUCTS, SLUG, {})
    a = create_app(brand)
    with a.test_client() as c:
        r = c.get("/unlock")
        assert r.status_code == 200 and b"coming soon" in r.data


def test_full_plan_has_content_for_every_locked_section():
    import full_plan
    brand = BRANDS[SLUG]
    answers = {}
    for q in brand["questions"]:
        if q.get("options"):
            answers[q["id"]] = [q["options"][0]["id"]] if q.get("multi") else q["options"][0]["id"]
        else:
            answers[q["id"]] = "Sample"
    plan = brand["generate_plan"](answers)
    secs = full_plan.full_sections(SLUG, answers, plan)
    assert len(secs) >= len(plan["locked_sections"])
    for s in secs:
        assert s["title"] and (s.get("bullets") or s.get("body"))
