"""Solar and lunar returns: exact instant, relocation, natal houses, the owner's rule flags."""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

from . import ephemeris as eph
from .chart import chart_at
from .houses import house_of
from .models import Chart
from .rules import Rules, load_rules
from .solver import Track, jd_from_utc
from .time import moment_from_jd, zone_name_for

PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
ANGLES = ("asc", "mc", "dsc", "ic")


class ReturnChart(BaseModel):
    model_config = ConfigDict(frozen=True)
    kind: str                      # "solar" or "lunar"
    year: int
    jd_ut: float
    utc_datetime: str
    local_datetime: str
    timezone: str | None
    place: dict                    # {"lat", "lon", "name"}
    precessed: bool
    chart: Chart
    natal_house_of: dict[str, int]       # SR angles and planets in the NATAL houses
    houses_of: dict[str, list[int]]      # SR house(s) of each planet; two when within the cusp orb
    angular: list[dict]                  # [{"body", "angle", "orb"}] within the angular orb
    stelliums: list[dict]                # [{"house", "bodies"}]
    flags: list[dict]                    # [{"id", "severity", "text"}]


class ReturnSet(BaseModel):
    model_config = ConfigDict(frozen=True)
    chosen: ReturnChart
    previous: ReturnChart
    base: ReturnChart


def _local(jd: float, tz: str | None) -> str:
    """Local time rounded to the nearest minute, as astro.com prints return charts."""
    from datetime import timedelta
    dt = moment_from_jd(jd).utc_datetime + timedelta(seconds=30)
    return (dt.astimezone(ZoneInfo(tz)) if tz else dt).isoformat(timespec="minutes")


def _utc(jd: float) -> str:
    return moment_from_jd(jd).utc_datetime.replace(tzinfo=None).isoformat(timespec="seconds")


def precession_offset(natal: Chart, jd: float) -> float:
    """How far the natal Sun's fixed (sidereal) point has moved along the tropical zodiac since birth."""
    return eph.ayanamsa_ut(jd, "lahiri") - eph.ayanamsa_ut(natal.moment.jd_ut, "lahiri")


def solar_return_instant(natal: Chart, year: int, precessed: bool = False) -> float:
    birth = natal.moment.utc_datetime
    centre = jd_from_utc(datetime(year, birth.month, min(birth.day, 28), birth.hour, birth.minute))
    target = natal.planets["sun"].lon + (precession_offset(natal, centre) if precessed else 0.0)
    for pad in (3, 10, 40):
        hits = Track("sun", centre - pad, centre + pad, natal.settings).crossings(target % 360)
        if hits:
            return min(hits, key=lambda h: abs(h.jd_ut - centre)).jd_ut
    raise ValueError(f"no solar return found in {year}")


def lunar_return_instants(natal: Chart, year: int) -> list[float]:
    jd0 = jd_from_utc(datetime(year, 1, 1))
    jd1 = jd_from_utc(datetime(year + 1, 1, 1))
    return [c.jd_ut for c in Track("moon", jd0, jd1, natal.settings).crossings(natal.planets["moon"].lon) if c.jd_ut < jd1]


def dual_houses(lon: float, cusps: dict[int, float], orb: float) -> list[int]:
    """The house a longitude is in, plus the neighbour when within `orb` of the cusp between them."""
    h = house_of(lon, cusps)
    out = [h]
    nxt = 1 if h == 12 else h + 1
    prv = 12 if h == 1 else h - 1
    if (cusps[nxt] - lon) % 360 <= orb:
        out.append(nxt)
    elif (lon - cusps[h]) % 360 <= orb:
        out.append(prv)
    return out


def stelliums(houses_of: dict[str, list[int]], rules: Rules) -> list[dict]:
    per_house: dict[int, list[str]] = {}
    for body, hs in houses_of.items():
        for h in hs:
            per_house.setdefault(h, []).append(body)
    return [{"house": h, "bodies": bodies} for h, bodies in sorted(per_house.items()) if len(bodies) >= rules.stellium_min_bodies]


def rule_flags(houses_of: dict[str, list[int]], natal_house_of: dict[str, int], sts: list[dict], rules: Rules) -> list[dict]:
    flags: list[dict] = []
    mars, saturn = set(houses_of.get("mars", [])), set(houses_of.get("saturn", []))
    shared = sorted(h for h in mars & saturn if h not in rules.mars_saturn_allowed_houses)
    if shared:
        flags.append({"id": "mars_saturn_same_house", "severity": "hard",
                      "text": f"Mars and Saturn share house {shared[0]}. " + rules.mars_saturn_text})
    in_1_12 = [b for b, hs in houses_of.items() if 1 in hs or 12 in hs]
    if len(set(in_1_12)) >= rules.stellium_min_bodies:
        flags.append({"id": "stellium_1_12_reads_as_asc_in_12", "severity": "hard",
                      "text": f"Stellium across the 1st and 12th ({', '.join(dict.fromkeys(in_1_12))}). " + rules.stellium_1_12_text})
    in_8 = [b for b, hs in houses_of.items() if 8 in hs]
    if len(in_8) >= rules.stellium_min_bodies:
        flags.append({"id": "stellium_8_reads_as_asc_in_12", "severity": "hard",
                      "text": f"Stellium in the 8th ({', '.join(in_8)}). " + rules.stellium_8_text})
    asc_house = natal_house_of.get("asc")
    if asc_house in rules.sr_asc_hard_filter_houses:
        flags.append({"id": "sr_asc_in_natal_1_6_12", "severity": "hard",
                      "text": f"Return Ascendant falls in natal house {asc_house}. " + rules.sr_asc_text})
    return flags


def _facts(natal: Chart, chart: Chart, rules: Rules) -> dict:
    natal_house_of = {"asc": house_of(chart.houses.asc, natal.houses.cusps), "mc": house_of(chart.houses.mc, natal.houses.cusps)}
    for p in PLANETS:
        natal_house_of[p] = house_of(chart.planets[p].lon, natal.houses.cusps)
    houses_of = {p: dual_houses(chart.planets[p].lon, chart.houses.cusps, rules.cusp_orb_degrees) for p in PLANETS}
    angles = {"asc": chart.houses.asc, "mc": chart.houses.mc, "dsc": chart.houses.dsc, "ic": chart.houses.ic}
    angular = []
    for p in PLANETS:
        for name, lon in angles.items():
            orb = abs(((chart.planets[p].lon - lon + 180) % 360) - 180)
            if orb <= rules.angular_orb_degrees:
                angular.append({"body": p, "angle": name, "orb": round(orb, 2)})
    angular.sort(key=lambda a: a["orb"])
    sts = stelliums(houses_of, rules)
    return {"natal_house_of": natal_house_of, "houses_of": houses_of, "angular": angular, "stelliums": sts,
            "flags": rule_flags(houses_of, natal_house_of, sts, rules)}


def _build(kind: str, natal: Chart, year: int, jd: float, lat: float, lon: float, place_name: str, precessed: bool) -> ReturnChart:
    rules = load_rules()
    chart = chart_at(jd, lat, lon, natal.settings)
    tz = zone_name_for(lat, lon)
    return ReturnChart(kind=kind, year=year, jd_ut=jd, utc_datetime=_utc(jd), local_datetime=_local(jd, tz), timezone=tz,
                       place={"lat": lat, "lon": lon, "name": place_name}, precessed=precessed, chart=chart, **_facts(natal, chart, rules))


def solar_return(natal: Chart, year: int, lat: float, lon: float, precessed: bool = False, at_jd: float | None = None,
                 place_name: str = "") -> ReturnChart:
    jd = at_jd if at_jd is not None else solar_return_instant(natal, year, precessed)
    return _build("solar", natal, year, jd, lat, lon, place_name, precessed)


def lunar_return(natal: Chart, jd: float, lat: float, lon: float, place_name: str = "") -> ReturnChart:
    return _build("lunar", natal, moment_from_jd(jd).utc_datetime.year, jd, lat, lon, place_name, False)


def return_set(natal: Chart, year: int, chosen: tuple[float, float], home: tuple[float, float], precessed: bool = False,
               chosen_name: str = "", home_name: str = "") -> ReturnSet:
    return ReturnSet(
        chosen=solar_return(natal, year, chosen[0], chosen[1], precessed, place_name=chosen_name),
        previous=solar_return(natal, year - 1, home[0], home[1], precessed, place_name=home_name),
        base=solar_return(natal, year, home[0], home[1], precessed, place_name=home_name),
    )
