"""Tests for Turnday."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

os.environ.pop("DATABASE_URL", None)  # tests use SQLite
os.environ.pop("DATABASE_SCHEMA", None)

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

os.environ["TURNDAY_DB"] = str(ROOT / "test.db")
os.environ["TURNDAY_ADMIN_PASSWORD"] = "test-admin-password"
os.environ["TURNDAY_SECRET"] = "test-secret"

from brands import BRANDS  # noqa: E402
from quiz_engine import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db = tmp_path / "app.db"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_SCHEMA", raising=False)
    monkeypatch.setenv("TURNDAY_DB", str(db))
    brand = dict(BRANDS["turnday"])
    brand["root"] = str(ROOT)
    application = create_app(brand)
    application.config["TESTING"] = True
    with application.test_client() as c:
        yield c


def test_landing_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    assert BRANDS["turnday"]["name"].encode() in r.data


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["ok"] is True


def test_quiz_flow_and_founding(client):
    r = client.get("/quiz", follow_redirects=False)
    assert r.status_code in (302, 303)
    # step 1
    r = client.get("/quiz/1")
    assert r.status_code == 200
    token = None
    # extract form_token from html
    html = r.data.decode()
    marker = 'name="form_token" value="'
    assert marker in html
    token = html.split(marker, 1)[1].split('"', 1)[0]

    questions = BRANDS["turnday"]["questions"]
    for i, q in enumerate(questions, start=1):
        r = client.get(f"/quiz/{i}")
        html = r.data.decode()
        token = html.split(marker, 1)[1].split('"', 1)[0]
        data = {"form_token": token, "action": "next"}
        if q["type"] == "choice":
            if q.get("multi"):
                data["answer"] = q["options"][0]["id"]
            else:
                data["answer"] = q["options"][0]["id"]
        else:
            data["answer"] = "Test answer"
        r = client.post(f"/quiz/{i}", data=data, follow_redirects=False)
        assert r.status_code in (302, 303)

    r = client.get("/computing")
    assert r.status_code == 200
    r = client.get("/results")
    assert r.status_code == 200
    assert b"plan" in r.data.lower() or b"Plan" in r.data

    r = client.get("/paywall")
    assert r.status_code == 200
    html = r.data.decode()
    assert "Checkout coming soon" not in html
    assert "founding list" not in html.lower()
    brand = BRANDS["turnday"]
    monthly, quarterly = brand["pricing"][0], brand["pricing"][1]
    assert monthly["price"] in html and quarterly["price"] in html
    assert "Monthly" in html and "Quarterly" in html
    assert "Renews automatically. Cancel anytime from your Gumroad library." in html
    href = brand["checkout_url"]
    assert f'href="{href}?wanted=true"' in html
    assert monthly["id"] == "monthly" and quarterly["id"] == "quarterly"

    r = client.get("/founding")
    html = r.data.decode()
    token = html.split(marker, 1)[1].split('"', 1)[0]
    r = client.post(
        "/founding",
        data={"form_token": token, "email": "founder@example.com", "name": "Founder", "tier": BRANDS["turnday"]["pricing"][0]["id"]},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303)
    r = client.get("/founding/thanks")
    assert r.status_code == 200
    thanks = r.data.decode()
    assert f'href="{href}?wanted=true&email=founder%40example.com"' in thanks or f'href="{href}?wanted=true&amp;email=founder%40example.com"' in thanks
    terms = client.get("/terms").data.decode()
    assert "Payments are processed by Gumroad" in terms
    assert "30-day money-back guarantee" not in terms.lower() or "does not offer a separate 30-day" in terms
    landing = client.get("/").data.decode()
    assert "Checkout coming soon" not in landing
    assert "Checkout is not live yet" not in landing
    assert "founding list" not in landing.lower()
    assert "first 4 weeks" not in landing
    assert "first 12 weeks" not in landing


def test_csrf_rejects_bad_token(client):
    client.get("/quiz/1")
    r = client.post("/quiz/1", data={"form_token": "nope", "action": "next", "answer": "x"})
    assert r.status_code == 400


def test_admin_requires_password(client):
    r = client.get("/admin")
    assert r.status_code == 401
    # login
    html = r.data.decode()
    marker = 'name="form_token" value="'
    token = html.split(marker, 1)[1].split('"', 1)[0]
    r = client.post("/admin", data={"form_token": token, "password": "test-admin-password"}, follow_redirects=True)
    assert r.status_code == 200
    assert b"Leads" in r.data


def test_legal_pages(client):
    for path in ("/privacy", "/terms", "/disclaimer"):
        assert client.get(path).status_code == 200


def test_print_requires_plan(client):
    r = client.get("/plan/print", follow_redirects=False)
    assert r.status_code in (302, 303)


from markupsafe import escape


def test_journey_and_honesty_on_landing(client):
    html = client.get("/").data.decode()
    assert 'id="journey"' in html
    for j in BRANDS["turnday"]["journey"]:
        assert str(escape(j["stage"])) in html
    assert "Renews automatically. Cancel anytime from your Gumroad library." in html
    assert "Monthly" in html and "Quarterly" in html
    low = html.lower()
    for banned in ("only 2 spots", "hurry", "act now", "guaranteed results", "only today"):
        assert banned not in low


def test_disclaimer_content(client):
    html = client.get("/disclaimer").data.decode()
    assert "Payments are processed by Gumroad" in html


def test_plan_has_preview_and_locked(client):
    brand = BRANDS["turnday"]
    answers = {}
    for q in brand["questions"]:
        if q["type"] == "choice":
            answers[q["id"]] = [q["options"][-1]["id"]] if q.get("multi") else q["options"][-1]["id"]
        else:
            answers[q["id"]] = "Sample"
    plan = brand["generate_plan"](answers)
    assert plan["title"] and plan["summary"]
    assert len(plan["preview_sections"]) >= 2
    assert len(plan["locked_sections"]) >= 3
    assert 8 <= len(brand["questions"]) <= 12
