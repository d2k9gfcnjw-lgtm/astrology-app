from __future__ import annotations

from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app

client = TestClient(app)


def test_solve_previous_and_next_with_retrograde_passes():
    # Mars at 15 Gemini during its 2022-23 loop: three crossings around December 2022.
    jd_dec = 2459930.5  # 2022-12-17
    r = client.post("/api/transits/solve", json={"body": "mars", "target_lon": 75.0, "jd_ut": jd_dec, "settings": {}})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["previous"]) >= 2 and len(body["next"]) >= 1
    assert body["previous"][-1]["jd_ut"] < jd_dec < body["next"][0]["jd_ut"]
    assert body["nearest"]["jd_ut"] in {x["jd_ut"] for x in body["previous"] + body["next"]}
    assert "utc_datetime" in body["nearest"]


def test_year_ahead_endpoint_for_subject(tmp_path, monkeypatch):
    from app.storage import ChartLibrary
    lib = ChartLibrary(db_path=tmp_path / "c.sqlite", key_path=tmp_path / "k.key")
    monkeypatch.setattr(main_module, "library", lambda: lib)
    s = client.post("/api/subjects", json={"name": "Golden Oslo", "datetime_local": "1992-07-23T04:23:00", "lat": 59.9167, "lon": 10.75,
                                           "timezone": "Europe/Oslo", "place_name": "Oslo"}).json()
    r = client.get(f"/api/subjects/{s['id']}/year-ahead", params={"year": 2026})
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["local_start"].startswith("2026-07-2") and rep["year"] == 2026
    assert rep["hits"] and rep["counts"]
    assert rep["hits"][0]["local_datetime"].endswith("+02:00") or rep["hits"][0]["local_datetime"].endswith("+01:00")


def test_year_ahead_for_unsaved_chart():
    r = client.post("/api/transits/year-ahead", json={"subject": {"datetime_local": "2024-11-03T07:50:00", "lat": 41.85, "lon": -87.65},
                                                     "year": 2025, "settings": {"transits": {"bodies": ["saturn"]}}})
    assert r.status_code == 200, r.text
    assert all(h["body"] == "saturn" for h in r.json()["hits"])
