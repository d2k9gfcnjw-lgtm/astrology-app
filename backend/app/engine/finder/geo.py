"""Land mask (Natural Earth), airports with scheduled service (OurAirports), candidate cities (GeoNames)."""
from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import shapefile
import shapely
from shapely.geometry import shape
from shapely.ops import unary_union

from ...cities import DEFAULT_INDEX
from ..rules import load_rules

ROOT = Path(__file__).resolve().parents[4]
NE_SHP = ROOT / "data" / "naturalearth" / "ne_110m_land.shp"
AIRPORTS_CSV = ROOT / "data" / "airports" / "airports.csv"
EARTH_KM = 6371.0


class LandMask:
    def __init__(self, path: Path = NE_SHP):
        if not path.exists():
            raise FileNotFoundError(f"{path} missing: run scripts/fetch_data.py")
        sf = shapefile.Reader(str(path))
        self.geom = unary_union([shape(s.__geo_interface__) for s in sf.shapes()])
        shapely.prepare(self.geom)

    def is_land(self, lat: float, lon: float) -> bool:
        return bool(shapely.contains_xy(self.geom, lon, lat))

    def mask(self, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
        return shapely.contains_xy(self.geom, np.asarray(lons, dtype=float), np.asarray(lats, dtype=float))


@lru_cache(maxsize=1)
def land_mask() -> LandMask:
    return LandMask()


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_KM * np.arcsin(np.sqrt(a))


class Airports:
    """Airports with scheduled commercial service, of the types the rules file allows."""

    def __init__(self, path: Path = AIRPORTS_CSV, types: list[str] | None = None, scheduled_only: bool = True):
        if not path.exists():
            raise FileNotFoundError(f"{path} missing: run scripts/fetch_data.py")
        d = load_rules().raw.get("city_search_defaults", {})
        types = types or d.get("airport_types", ["large_airport", "medium_airport"])
        rows = []
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r["type"] not in types or (scheduled_only and r["scheduled_service"] != "yes"):
                    continue
                code = r["iata_code"] or r["icao_code"] or r["ident"]
                rows.append((code, r["name"], r["municipality"], float(r["latitude_deg"]), float(r["longitude_deg"]), r["iso_country"]))
        self.rows = rows
        self.lats = np.array([x[3] for x in rows])
        self.lons = np.array([x[4] for x in rows])

    def __len__(self) -> int:
        return len(self.rows)

    def nearest(self, lat: float, lon: float) -> tuple[str, float]:
        d = haversine_km(lat, lon, self.lats, self.lons)
        i = int(np.argmin(d))
        return self.rows[i][0], float(d[i])

    def nearest_many(self, lats: np.ndarray, lons: np.ndarray) -> tuple[list[str], np.ndarray]:
        codes, kms = [], np.empty(len(lats))
        for i, (la, lo) in enumerate(zip(lats, lons)):
            c, k = self.nearest(float(la), float(lo))
            codes.append(c)
            kms[i] = k
        return codes, kms


@lru_cache(maxsize=1)
def airports() -> Airports:
    return Airports()


@dataclass(frozen=True)
class Candidate:
    geonameid: int
    name: str
    country: str
    admin1: str
    population: int
    lat: float
    lon: float
    timezone: str
    airport_code: str
    airport_km: float


@lru_cache(maxsize=1)
def _all_cities_with_airports() -> list[Candidate]:
    conn = sqlite3.connect(DEFAULT_INDEX)
    rows = conn.execute("SELECT geonameid, name, country, admin1, population, lat, lon, timezone FROM cities").fetchall()
    conn.close()
    lats = np.array([r[5] for r in rows]); lons = np.array([r[6] for r in rows])
    codes, kms = airports().nearest_many(lats, lons)
    return [Candidate(r[0], r[1], r[2], r[3], int(r[4]), float(r[5]), float(r[6]), r[7], codes[i], float(kms[i])) for i, r in enumerate(rows)]


def candidate_cities(population_floor: int, airport_max_km: float, exclude_countries: list[str]) -> list[Candidate]:
    ex = set(exclude_countries)
    return [c for c in _all_cities_with_airports() if c.population >= population_floor and c.airport_km <= airport_max_km and c.country not in ex]
