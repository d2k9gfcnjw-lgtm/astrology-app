"""GeoNames cities15000 search index (SQLite, built once from the downloaded text file)."""
from __future__ import annotations

import os
import sqlite3
import unicodedata
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "data" / "geonames" / "cities15000.txt"
DEFAULT_INDEX = Path(os.environ.get("ASTRO_CITIES_DB", ROOT / "data" / "cities.sqlite"))


@dataclass(frozen=True)
class City:
    geonameid: int
    name: str
    ascii_name: str
    alternate_names: str
    lat: float
    lon: float
    country: str
    admin1: str
    population: int
    timezone: str


def fold(text: str) -> str:
    """Lowercase and strip accents so 'Río' matches 'rio'."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).casefold()


def parse_geonames_line(line: str) -> City:
    f = line.rstrip("\n").split("\t")
    return City(
        geonameid=int(f[0]), name=f[1], ascii_name=f[2], alternate_names=f[3], lat=float(f[4]), lon=float(f[5]),
        country=f[8], admin1=f[10], population=int(f[14] or 0), timezone=f[17],
    )


class CityIndex:
    def __init__(self, db_path: Path | str = DEFAULT_INDEX):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def is_built(self) -> bool:
        row = self._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cities'").fetchone()
        return row is not None and self.count() > 0

    def count(self) -> int:
        try:
            return self._conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
        except sqlite3.OperationalError:
            return 0

    def build_from_file(self, source: Path | str = DEFAULT_SOURCE) -> int:
        """(Re)build the index from a GeoNames tab file. One row per city, plus one per searchable name."""
        c = self._conn
        c.executescript(
            """DROP TABLE IF EXISTS cities; DROP TABLE IF EXISTS names;
               CREATE TABLE cities (geonameid INTEGER PRIMARY KEY, name TEXT, ascii_name TEXT, alternate_names TEXT,
                                    lat REAL, lon REAL, country TEXT, admin1 TEXT, population INTEGER, timezone TEXT);
               CREATE TABLE names (key TEXT, geonameid INTEGER);"""
        )
        n = 0
        with open(source, encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                city = parse_geonames_line(line)
                c.execute("INSERT INTO cities VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (city.geonameid, city.name, city.ascii_name, city.alternate_names, city.lat, city.lon,
                           city.country, city.admin1, city.population, city.timezone))
                keys = {fold(city.name), fold(city.ascii_name)}
                keys.update(fold(a) for a in city.alternate_names.split(",") if a)
                c.executemany("INSERT INTO names VALUES (?,?)", [(k, city.geonameid) for k in keys if k])
                n += 1
        c.execute("CREATE INDEX names_key ON names(key)")
        c.execute("CREATE INDEX cities_pop ON cities(population DESC)")
        c.commit()
        return n

    def search(self, query: str, limit: int = 10) -> list[City]:
        q = fold(query.strip())
        if not q:
            return []
        rows = self._conn.execute(
            """SELECT DISTINCT c.* FROM cities c JOIN names n ON n.geonameid = c.geonameid
               WHERE n.key >= ? AND n.key < ? ORDER BY c.population DESC, c.name LIMIT ?""",
            (q, q + "￿", limit),
        ).fetchall()
        return [City(r["geonameid"], r["name"], r["ascii_name"], r["alternate_names"], r["lat"], r["lon"],
                     r["country"], r["admin1"], r["population"], r["timezone"]) for r in rows]
