"""Astrocartography lines, parans and distances, checked against Swiss Ephemeris's own horizon calculation."""
from __future__ import annotations

import math
from datetime import datetime

import pytest
import swisseph as swe

from app.engine.acg import AcgSettings, at_place, distance_to_line_km, gmst_degrees, lines_at, parans_at
from app.engine.chart import calculate_chart
from app.engine.models import ChartInput, Settings
from app.engine.planets import planets_at
from app.engine.solver import jd_from_utc

OSLO = ChartInput(datetime_local=datetime(1992, 7, 23, 4, 23), lat=59.9167, lon=10.75)
S = Settings()


def altitude(jd: float, ra: float, dec: float, lat: float, lon: float) -> float:
    az, alt_true, alt_app = swe.azalt(jd, swe.EQU2HOR, (lon, lat, 0.0), 0.0, 0.0, (ra, dec, 1.0))
    return alt_true


def test_sun_mc_line_at_noon_ut_is_near_greenwich():
    jd = jd_from_utc(datetime(2024, 6, 21, 12, 0))
    lines = lines_at(jd, S, AcgSettings(bodies=["sun"]))
    mc = next(l for l in lines if l.body == "sun" and l.angle == "mc")
    lon = mc.points[0][0][0]
    assert abs(lon) < 4.5  # within the equation of time
    ic = next(l for l in lines if l.body == "sun" and l.angle == "ic")
    assert abs(abs(ic.points[0][0][0]) - 180) < 4.5


def test_mc_line_has_hour_angle_zero():
    natal = calculate_chart(OSLO, S)
    jd = natal.moment.jd_ut
    planets = planets_at(jd, S)
    for line in lines_at(jd, S, AcgSettings()):
        if line.angle != "mc":
            continue
        lon = line.points[0][0][0]
        lst = (gmst_degrees(jd) + lon) % 360
        assert abs(((lst - planets[line.body].right_ascension + 180) % 360) - 180) < 1e-6


@pytest.mark.parametrize("angle", ["asc", "dsc"])
def test_horizon_lines_put_the_body_on_the_horizon(angle):
    natal = calculate_chart(OSLO, S)
    jd = natal.moment.jd_ut
    planets = planets_at(jd, S)
    lines = [l for l in lines_at(jd, S, AcgSettings()) if l.angle == angle]
    assert lines
    checked = 0
    for line in lines:
        p = planets[line.body]
        for seg in line.points:
            for lon, lat in seg[::20]:
                alt = altitude(jd, p.right_ascension, p.declination, lat, lon)
                assert abs(alt) < 0.1, (line.body, angle, lat, lon, alt)
                # rising means altitude grows a few minutes later; setting means it falls
                later = altitude(jd + 5 / 1440, p.right_ascension, p.declination, lat, lon)
                assert (later > alt) == (angle == "asc"), (line.body, angle, lat, lon)
                checked += 1
    assert checked > 50


def test_lines_split_at_antimeridian_and_cover_latitudes():
    natal = calculate_chart(OSLO, S)
    for line in lines_at(natal.moment.jd_ut, S, AcgSettings()):
        for seg in line.points:
            lons = [p[0] for p in seg]
            assert all(-180 <= x <= 180 for x in lons)
            assert all(abs(b - a) < 180 for a, b in zip(lons, lons[1:]))
        if line.angle in ("mc", "ic"):
            lats = [p[1] for seg in line.points for p in seg]
            assert min(lats) <= -85 and max(lats) >= 85


def test_zodiacal_method_differs_from_in_mundo():
    natal = calculate_chart(OSLO, S)
    jd = natal.moment.jd_ut
    mundo = {(l.body, l.angle): l for l in lines_at(jd, S, AcgSettings(bodies=["moon"]))}
    zod = {(l.body, l.angle): l for l in lines_at(jd, S, AcgSettings(bodies=["moon"], method="zodiacal"))}
    assert abs(mundo[("moon", "mc")].points[0][0][0] - zod[("moon", "mc")].points[0][0][0]) > 0.5  # Moon has 4 deg of latitude here


def test_parans_are_simultaneous_angularities():
    natal = calculate_chart(OSLO, S)
    jd = natal.moment.jd_ut
    ps = parans_at(jd, S, AcgSettings(bodies=["sun", "moon", "jupiter", "saturn"]))
    assert ps
    from app.engine.acg import angular_lst
    planets = planets_at(jd, S)
    for p in ps:
        assert -89 <= p.lat <= 89
        a = angular_lst(planets[p.body_a].right_ascension, planets[p.body_a].declination, p.angle_a, p.lat)
        b = angular_lst(planets[p.body_b].right_ascension, planets[p.body_b].declination, p.angle_b, p.lat)
        assert abs(((a - b + 180) % 360) - 180) < 0.01, p
    assert not any(p.body_a == p.body_b for p in ps)
    kinds = {(p.angle_a, p.angle_b) for p in ps}
    assert not any(k in {("mc", "mc"), ("ic", "ic"), ("mc", "ic"), ("ic", "mc")} for k in kinds)


def test_distance_to_lines():
    assert distance_to_line_km([[(10.0, -89.0), (10.0, 89.0)]], 0.0, 11.0) == pytest.approx(111.2, abs=0.5)
    assert distance_to_line_km([[(10.0, -89.0), (10.0, 89.0)]], 60.0, 11.0) == pytest.approx(111.2 * math.cos(math.radians(60)), abs=1.0)
    assert distance_to_line_km([[(10.0, -89.0), (10.0, 89.0)]], 0.0, 10.0) < 0.01


def test_at_place_lists_lines_within_orb_nearest_first():
    natal = calculate_chart(OSLO, S)
    jd = natal.moment.jd_ut
    lines = lines_at(jd, S, AcgSettings())
    sun_mc_lon = next(l for l in lines if l.body == "sun" and l.angle == "mc").points[0][0][0]
    res = at_place(jd, 40.0, sun_mc_lon + 0.5, S, AcgSettings(orb_km=300))
    assert res.lines[0].body == "sun" and res.lines[0].angle == "mc" and res.lines[0].km < 60
    assert all(x.km <= 300 for x in res.lines)
    assert [x.km for x in res.lines] == sorted(x.km for x in res.lines)
    assert res.chart.houses.asc is not None and res.chart.provenance.lat == 40.0
    assert all(abs(p.lat - 40.0) <= 1.0 for p in res.parans)


def test_endpoints():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    r = c.post("/api/acg/lines", json={"jd_ut": 2451545.0, "settings": {}, "acg": {"bodies": ["sun", "moon"]}})
    assert r.status_code == 200, r.text
    assert {l["angle"] for l in r.json()["lines"]} == {"asc", "dsc", "mc", "ic"} and r.json()["parans"]
    r2 = c.post("/api/acg/at", json={"jd_ut": 2451545.0, "lat": 48.86, "lon": 2.35, "settings": {}, "acg": {"orb_km": 500}})
    assert r2.status_code == 200, r2.text
    assert "lines" in r2.json() and "chart" in r2.json()
