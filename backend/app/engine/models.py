"""Pydantic models shared by the engine and the API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
              "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

Zodiac = Literal["tropical", "sidereal"]
HouseSystem = Literal["placidus", "whole_sign"]
NodeType = Literal["true", "mean"]
LilithType = Literal["mean", "true"]
FortuneFormula = Literal["sect", "day"]
Ayanamsa = Literal["lahiri", "fagan_bradley", "raman", "krishnamurti"]


class AspectSettings(BaseModel):
    """Natal wheel defaults chosen by the owner (27 Oct 2026). Transit orbs are a separate setting in Phase 3."""
    model_config = ConfigDict(frozen=True)

    orbs: dict[str, float] = Field(default_factory=lambda: {"conjunction": 8, "opposition": 8, "trine": 8, "square": 8, "sextile": 6})
    luminary_bonus: float = 1.0        # extra orb when the Sun or Moon is involved
    minor_aspects: bool = False
    minor_orb: float = 2.0

    def model_post_init(self, __context) -> None:  # fill in any orb the user left out
        merged = {"conjunction": 8, "opposition": 8, "trine": 8, "square": 8, "sextile": 6}
        merged.update(self.orbs)
        object.__setattr__(self, "orbs", merged)


class Aspect(BaseModel):
    model_config = ConfigDict(frozen=True)

    a: str
    b: str
    type: str
    angle: float          # exact angle of this aspect type
    separation: float     # actual angular distance 0-180
    orb: float            # |separation - angle|
    max_orb: float
    applying: bool
    exact: bool


class Settings(BaseModel):
    """Per-chart calculation settings. Defaults follow CLAUDE.md and the owner's decisions."""
    model_config = ConfigDict(frozen=True)

    zodiac: Zodiac = "tropical"
    ayanamsa: Ayanamsa = "lahiri"          # only used when zodiac == "sidereal"
    house_system: HouseSystem = "placidus"
    placidus_fallback_latitude: float = 66.0  # |lat| at or above this: Whole Sign with a warning
    node_type: NodeType = "true"
    lilith_type: LilithType = "mean"
    fortune_formula: FortuneFormula = "sect"  # sect: reversed at night; day: ASC+Moon-Sun always
    include_node: bool = True
    include_chiron: bool = True
    include_lilith: bool = True
    include_fortune: bool = True
    aspects: AspectSettings = Field(default_factory=AspectSettings)


class ChartInput(BaseModel):
    """What the user enters. Time zone is looked up from lat/lon unless given."""
    datetime_local: datetime
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    timezone: str | None = None
    utc_offset_override: str | None = None  # "+HH:MM" / "-HH:MM"; wins over the zone


class Moment(BaseModel):
    """One instant, with every time fact CLAUDE.md says a chart must store."""
    model_config = ConfigDict(frozen=True)

    local_datetime: datetime
    timezone: str | None
    utc_offset: str
    utc_offset_seconds: int
    utc_datetime: datetime
    jd_ut: float
    jd_tt: float
    delta_t_sec: float
    flags: tuple[str, ...]


class BodyPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    lon: float                 # ecliptic longitude 0-360 in the chart's zodiac
    lat: float                 # ecliptic latitude
    dist: float                # AU
    speed_lon: float           # deg/day, negative = retrograde
    speed_lat: float
    right_ascension: float
    declination: float
    retrograde: bool
    sign: str                  # three-letter sign
    sign_degrees: float        # 0-30 within the sign
    formatted: str             # e.g. 5°39'32" Tau
    variant: str | None = None # "true"/"mean" for node and lilith


class Houses(BaseModel):
    model_config = ConfigDict(frozen=True)

    cusps: dict[int, float]            # 1..12 longitudes
    cusp_declinations: dict[int, float]
    asc: float
    mc: float
    dsc: float
    ic: float
    vertex: float
    armc: float                         # right ascension of the MC (local sidereal time in degrees)
    obliquity: float
    system_used: HouseSystem
    system_requested: HouseSystem
    warnings: tuple[str, ...]
    ayanamsa_degrees: float | None = None


class Provenance(BaseModel):
    model_config = ConfigDict(frozen=True)

    local_time: datetime
    utc_offset: str
    timezone: str | None
    lat: float
    lon: float
    house_system: HouseSystem
    zodiac: Zodiac
    ayanamsa: Ayanamsa | None
    node_type: NodeType
    lilith_type: LilithType
    fortune_formula: FortuneFormula
    time_flags: tuple[str, ...]
    relocated_from: tuple[float, float] | None = None


class Chart(BaseModel):
    model_config = ConfigDict(frozen=True)

    aspects: list[Aspect] = Field(default_factory=list)
    moment: Moment
    planets: dict[str, BodyPosition]   # ephemeris bodies only (location independent)
    houses: Houses
    fortune: BodyPosition | None       # depends on the ASC, so it is not in `planets`
    planet_houses: dict[str, int]      # house number of every body and the Part of Fortune
    is_day: bool
    provenance: Provenance
    settings: Settings


def format_longitude(lon: float) -> tuple[str, float, str]:
    """360-degree longitude -> (sign, degrees within sign, '5°39\\'32" Tau')."""
    lon = lon % 360
    sign_index = int(lon // 30)
    within = lon - sign_index * 30
    total_sec = round(within * 3600)
    if total_sec >= 30 * 3600:  # rounding pushed it to the next sign
        total_sec = 30 * 3600 - 1
    d, rem = divmod(total_sec, 3600)
    m, s = divmod(rem, 60)
    return SIGNS[sign_index], within, f"{d}°{m:02d}'{s:02d}\" {SIGNS[sign_index]}"
