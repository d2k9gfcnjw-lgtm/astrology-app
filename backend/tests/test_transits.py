"""Transit aspects with their own orbs, house ingresses, stations and the year-ahead report."""
from __future__ import annotations

from datetime import datetime

from app.engine.chart import calculate_chart
from app.engine.models import ChartInput, Settings, TransitSettings
from app.engine.solver import jd_from_utc
from app.engine.transits import natal_points, solar_return_instant, transit_hits, year_ahead

CHICAGO = ChartInput(datetime_local=datetime(2024, 11, 3, 7, 50), lat=41.85, lon=-87.65)


def test_defaults_match_owner_decisions():
    t = TransitSettings()
    assert t.bodies == ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    assert t.orbs["jupiter"] == 3 and t.orbs["saturn"] == 3 and t.orbs["uranus"] == 2
    assert t.orbs["neptune"] == 1.5 and t.orbs["pluto"] == 1.5 and t.orbs["mars"] == 3
    assert t.natal_points == ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "asc", "dsc", "mc", "ic"]
    assert t.aspects == ["conjunction", "opposition", "trine", "square", "sextile"]
    assert t.include_ingresses and t.include_stations


def test_natal_points_include_all_four_angles():
    chart = calculate_chart(CHICAGO, Settings())
    pts = natal_points(chart, TransitSettings())
    assert set(pts) >= {"sun", "pluto", "asc", "dsc", "mc", "ic"}
    assert abs((pts["asc"] + 180) % 360 - pts["dsc"]) < 1e-9
    assert "node" not in pts
    pts2 = natal_points(chart, TransitSettings(natal_points=["sun", "node", "cusp_2", "fortune"]))
    assert set(pts2) == {"sun", "node", "cusp_2", "fortune"}


def test_solar_return_instant():
    chart = calculate_chart(CHICAGO, Settings())
    sr = solar_return_instant(chart, 2025)
    from app.engine.time import moment_from_jd
    when = moment_from_jd(sr).utc_datetime.replace(tzinfo=None)
    assert when.year == 2025 and when.month == 11 and when.day in (2, 3)
    from app.engine.planets import planets_at
    from .conftest import angle_diff
    assert angle_diff(planets_at(sr, Settings())["sun"].lon, chart.planets["sun"].lon) < 1 / 3600


def test_hits_have_exact_instant_inside_orb_span_and_passes():
    chart = calculate_chart(CHICAGO, Settings())
    start = jd_from_utc(datetime(2025, 1, 1))
    end = jd_from_utc(datetime(2026, 1, 1))
    hits = transit_hits(chart, TransitSettings(bodies=["jupiter"]), start, end)
    assert hits, "Jupiter makes aspects to something in a year"
    for h in hits:
        assert start <= h.jd_ut < end
        assert h.body == "jupiter" and h.aspect in {"conjunction", "opposition", "trine", "square", "sextile"}
        assert h.orb_enter_jd is None or h.orb_enter_jd <= h.jd_ut
        assert h.orb_exit_jd is None or h.orb_exit_jd >= h.jd_ut
        assert 1 <= h.pass_index <= h.pass_count <= 5
    assert hits == sorted(hits, key=lambda h: h.jd_ut)


def test_year_ahead_report_window_and_contents():
    chart = calculate_chart(CHICAGO, Settings())
    rep = year_ahead(chart, 2025, TransitSettings(bodies=["sun", "jupiter", "saturn"]), timezone="America/Chicago")
    assert rep.year == 2025
    assert 364 < rep.jd_end - rep.jd_start < 367
    assert rep.local_start.startswith("2025-11-0") and rep.local_end.startswith("2026-11-0")
    sun_returns = [h for h in rep.hits if h.body == "sun" and h.natal_point == "sun" and h.aspect == "conjunction"]
    assert len(sun_returns) == 1 and abs(sun_returns[0].jd_ut - rep.jd_start) < 1e-6
    assert all(rep.jd_start <= h.jd_ut < rep.jd_end for h in rep.hits)
    assert rep.counts["sun"] > rep.counts["jupiter"] >= 1
    assert any(i.body == "sun" for i in rep.ingresses) and len([i for i in rep.ingresses if i.body == "sun" and i.kind == "house"]) == 12
    assert any(s.body == "saturn" for s in rep.stations) and all(s.kind in ("retrograde", "direct") for s in rep.stations)
    assert all(h.local_datetime.endswith(("-05:00", "-06:00")) for h in rep.hits)


def test_moon_off_by_default_and_on_when_asked():
    chart = calculate_chart(CHICAGO, Settings())
    off = year_ahead(chart, 2025, TransitSettings(), timezone="America/Chicago")
    assert not any(h.body == "moon" for h in off.hits)
    on = year_ahead(chart, 2025, TransitSettings(bodies=["moon"], natal_points=["sun"], aspects=["conjunction"], include_ingresses=False, include_stations=False), timezone="America/Chicago")
    assert 12 <= len(on.hits) <= 14
