from __future__ import annotations

from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app

client = TestClient(app)


def _lib(tmp_path, monkeypatch):
    from app.storage import ChartLibrary
    lib = ChartLibrary(db_path=tmp_path / "c.sqlite", key_path=tmp_path / "k.key")
    monkeypatch.setattr(main_module, "library", lambda: lib)
    return lib


def test_subject_has_home_place(tmp_path, monkeypatch):
    _lib(tmp_path, monkeypatch)
    r = client.post("/api/subjects", json={"name": "Golden Oslo", "datetime_local": "1992-07-23T04:23:00", "lat": 59.9167, "lon": 10.75,
                                           "timezone": "Europe/Oslo", "place_name": "Oslo",
                                           "home_place_name": "Chicago", "home_lat": 41.85, "home_lon": -87.65})
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["home_place_name"] == "Chicago" and s["home_lat"] == 41.85
    r2 = client.post("/api/subjects", json={"name": "No home", "datetime_local": "1992-07-23T04:23:00", "lat": 59.9167, "lon": 10.75})
    assert r2.json()["home_lat"] is None


def test_solar_return_endpoint_defaults_base_to_home(tmp_path, monkeypatch):
    _lib(tmp_path, monkeypatch)
    sid = client.post("/api/subjects", json={"name": "Golden Oslo", "datetime_local": "1992-07-23T04:23:00", "lat": 59.9167, "lon": 10.75,
                                             "timezone": "Europe/Oslo", "home_lat": 41.85, "home_lon": -87.65, "home_place_name": "Chicago"}).json()["id"]
    r = client.get(f"/api/subjects/{sid}/solar-return", params={"year": 2026, "lat": -33.45, "lon": -70.6667})
    assert r.status_code == 200, r.text
    rs = r.json()
    assert rs["chosen"]["timezone"] == "America/Santiago"
    assert rs["base"]["place"]["lat"] == 41.85 and rs["base"]["place"]["name"] == "Chicago"
    assert rs["previous"]["year"] == 2025
    assert "natal_house_of" in rs["chosen"] and "asc" in rs["chosen"]["natal_house_of"]
    assert rs["chosen"]["chart"]["houses"]["system_used"] == "placidus"
    r2 = client.get(f"/api/subjects/{sid}/solar-return", params={"year": 2026})
    assert r2.json()["chosen"]["place"]["lat"] == 41.85  # no place given: home


def test_lunar_return_endpoints(tmp_path, monkeypatch):
    _lib(tmp_path, monkeypatch)
    sid = client.post("/api/subjects", json={"name": "Golden Oslo", "datetime_local": "1992-07-23T04:23:00", "lat": 59.9167, "lon": 10.75,
                                             "timezone": "Europe/Oslo"}).json()["id"]
    r = client.get(f"/api/subjects/{sid}/lunar-returns", params={"year": 2026})
    assert r.status_code == 200, r.text
    items = r.json()
    assert 12 <= len(items) <= 14 and "local_datetime" in items[0] and "jd_ut" in items[0]
    r2 = client.get(f"/api/subjects/{sid}/lunar-return", params={"jd_ut": items[0]["jd_ut"]})
    assert r2.status_code == 200, r2.text
    assert r2.json()["kind"] == "lunar" and r2.json()["place"]["lat"] == 59.9167  # no home: birth place


def test_unsaved_solar_return():
    r = client.post("/api/returns/solar", json={"subject": {"datetime_local": "2024-11-03T07:50:00", "lat": 41.85, "lon": -87.65},
                                                "year": 2025, "lat": 59.9167, "lon": 10.75, "settings": {}})
    assert r.status_code == 200, r.text
    assert r.json()["chosen"]["year"] == 2025 and r.json()["base"]["place"]["lat"] == 41.85
