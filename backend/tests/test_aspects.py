"""Aspects between bodies with per-aspect orbs; orb is measured on each side of exact."""
from __future__ import annotations

from app.engine.aspects import AspectSettings, find_aspects
from app.engine.models import BodyPosition, format_longitude


def body(lon: float, speed: float = 1.0) -> BodyPosition:
    sign, within, text = format_longitude(lon)
    return BodyPosition(lon=lon % 360, lat=0, dist=1, speed_lon=speed, speed_lat=0, right_ascension=0, declination=0,
                        retrograde=speed < 0, sign=sign, sign_degrees=within, formatted=text)


def test_defaults_match_owner_decision():
    s = AspectSettings()
    assert s.orbs == {"conjunction": 8, "opposition": 8, "trine": 8, "square": 8, "sextile": 6}
    assert s.luminary_bonus == 1
    assert s.minor_aspects is False


def test_square_within_orb_each_side():
    a = find_aspects({"mars": body(10), "saturn": body(107.9)}, AspectSettings())
    assert len(a) == 1 and a[0].type == "square" and abs(a[0].orb - 7.9) < 1e-9
    assert find_aspects({"mars": body(10), "saturn": body(108.1)}, AspectSettings()) == []
    assert find_aspects({"mars": body(10), "saturn": body(261.9)}, AspectSettings()) == []  # 108.1 the short way -> no
    a = find_aspects({"mars": body(10), "saturn": body(100 - 7.5)}, AspectSettings())
    assert a[0].type == "square"


def test_luminary_bonus():
    assert find_aspects({"sun": body(0), "mars": body(188.5)}, AspectSettings())[0].type == "opposition"
    assert find_aspects({"venus": body(0), "mars": body(188.5)}, AspectSettings()) == []


def test_applying_and_separating():
    # Mars at 10 moving +0.5/day, Saturn at 100 moving +0.1/day: distance 90 -> exact square now, growing -> separating
    a = find_aspects({"mars": body(10, 0.5), "saturn": body(100, 0.1)}, AspectSettings())[0]
    assert a.exact is True and a.applying is False
    b = find_aspects({"mars": body(8, 0.5), "saturn": body(100, 0.1)}, AspectSettings())[0]
    assert b.applying is True  # 92 apart, mars faster, closing toward 90


def test_minor_aspects_off_by_default_and_on_when_asked():
    pair = {"moon": body(0), "pluto": body(150.2)}
    assert find_aspects(pair, AspectSettings()) == []
    on = find_aspects(pair, AspectSettings(minor_aspects=True))
    assert on and on[0].type == "quincunx"


def test_points_excluded_by_default_and_included_on_request():
    bodies = {"sun": body(0), "fortune": body(120), "node": body(240), "chiron": body(60)}
    assert find_aspects(bodies, AspectSettings()) == []
    on = find_aspects(bodies, AspectSettings(include_points=True))
    assert {(a.a, a.b, a.type) for a in on} >= {("sun", "node", "trine"), ("sun", "chiron", "sextile")}
