"""Swiss Ephemeris access. Data files are mandatory; the Moshier fallback is never accepted."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_EPHE_DIR = Path(os.environ.get("ASTRO_EPHE_DIR", ROOT / "data" / "ephe"))

# Files that must exist for the engine to start (1800-2400 CE, planets, Moon, Chiron).
REQUIRED_FILES = ("sepl_18.se1", "semo_18.se1", "seas_18.se1")

SUN, MOON, MERCURY, VENUS, MARS = swe.SUN, swe.MOON, swe.MERCURY, swe.VENUS, swe.MARS
JUPITER, SATURN, URANUS, NEPTUNE, PLUTO = swe.JUPITER, swe.SATURN, swe.URANUS, swe.NEPTUNE, swe.PLUTO
MEAN_NODE, TRUE_NODE, MEAN_APOG, OSCU_APOG, CHIRON = swe.MEAN_NODE, swe.TRUE_NODE, swe.MEAN_APOG, swe.OSCU_APOG, swe.CHIRON
ECL_NUT = swe.ECL_NUT

FLG_SWIEPH, FLG_MOSEPH, FLG_SPEED = swe.FLG_SWIEPH, swe.FLG_MOSEPH, swe.FLG_SPEED
FLG_EQUATORIAL, FLG_SIDEREAL = swe.FLG_EQUATORIAL, swe.FLG_SIDEREAL

AYANAMSA_IDS = {
    "lahiri": swe.SIDM_LAHIRI,
    "fagan_bradley": swe.SIDM_FAGAN_BRADLEY,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
}


class EphemerisDataMissing(RuntimeError):
    """Raised when the .se1 files are absent or a date falls outside them."""


@dataclass(frozen=True)
class EphemerisInfo:
    path: Path
    files: tuple[str, ...]
    swisseph_version: str


_info: EphemerisInfo | None = None


def init_ephemeris(path: Path | str | None = None) -> EphemerisInfo:
    """Point Swiss Ephemeris at the data folder and verify the files are there. Fails loudly."""
    global _info
    ephe_dir = Path(path) if path is not None else DEFAULT_EPHE_DIR
    if not ephe_dir.is_dir():
        raise EphemerisDataMissing(
            f"Swiss Ephemeris folder not found: {ephe_dir}. Run `python3 scripts/fetch_data.py` to download it."
        )
    files = tuple(sorted(p.name for p in ephe_dir.glob("*.se1")))
    missing = [f for f in REQUIRED_FILES if f not in files]
    if missing:
        raise EphemerisDataMissing(
            f"Swiss Ephemeris files missing in {ephe_dir}: {', '.join(missing)}. "
            "Run `python3 scripts/fetch_data.py` to download them."
        )
    swe.set_ephe_path(str(ephe_dir))
    _info = EphemerisInfo(path=ephe_dir, files=files, swisseph_version=swe.version)
    return _info


def info() -> EphemerisInfo:
    return _info if _info is not None else init_ephemeris()


def calc_ut(jd_ut: float, body: int, flags: int = 0) -> tuple[tuple[float, ...], int]:
    """swe.calc_ut with the Swiss Ephemeris files enforced. Returns (xx, retflag)."""
    info()
    want = flags | FLG_SWIEPH | FLG_SPEED
    try:
        xx, retflag = swe.calc_ut(jd_ut, body, want)
    except swe.Error as exc:
        raise EphemerisDataMissing(f"Swiss Ephemeris could not compute body {body} at JD {jd_ut}: {exc}") from exc
    if retflag < 0 or (retflag & FLG_MOSEPH) or not (retflag & FLG_SWIEPH):
        raise EphemerisDataMissing(
            f"Swiss Ephemeris data files do not cover JD {jd_ut} for body {body} "
            f"(returned flags {retflag}); Moshier fallback is not allowed. Download more .se1 files."
        )
    return xx, retflag


def set_sidereal_mode(ayanamsa: str) -> None:
    swe.set_sid_mode(AYANAMSA_IDS[ayanamsa], 0, 0)


def ayanamsa_ut(jd_ut: float, ayanamsa: str) -> float:
    """Ayanamsa referred to the true equinox of date, the same one calc_ut and houses_ex subtract.
    (swe.get_ayanamsa_ut uses the mean equinox and differs by the nutation, about 18".)"""
    info()
    set_sidereal_mode(ayanamsa)
    _, value = swe.get_ayanamsa_ex_ut(jd_ut, FLG_SWIEPH)
    return value


def obliquity_ut(jd_ut: float) -> float:
    """True obliquity of the ecliptic in degrees."""
    xx, _ = calc_ut(jd_ut, ECL_NUT)
    return xx[0]


def ecliptic_to_equatorial(lon: float, lat: float, obliquity: float) -> tuple[float, float]:
    """(lon, lat) on the ecliptic -> (right ascension, declination)."""
    ra, dec, _ = swe.cotrans((lon, lat, 1.0), -obliquity)
    return ra % 360, dec


def julday(year: int, month: int, day: int, hour: float) -> float:
    return swe.julday(year, month, day, hour, swe.GREG_CAL)


def delta_t_days(jd_ut: float) -> float:
    return swe.deltat(jd_ut)
