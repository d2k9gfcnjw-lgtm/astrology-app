"""GeoNames city search: prefix match, biggest population first, alternate names."""
from __future__ import annotations

import pytest

from app.cities import CityIndex, parse_geonames_line

SAMPLE = "\n".join([
    # geonameid name asciiname alternatenames lat lon fclass fcode country cc2 admin1 admin2 admin3 admin4 pop elev dem tz mod
    "3143244\tOslo\tOslo\tOslo,Осло,オスロ\t59.91273\t10.74609\tP\tPPLC\tNO\t\t12\t0301\t\t\t580000\t\t26\tEurope/Oslo\t2019-01-01",
    "4164138\tMiami\tMiami\tMiami,Майами\t25.77427\t-80.19366\tP\tPPLA2\tUS\t\tFL\t086\t\t\t441003\t\t25\tAmerica/New_York\t2019-01-01",
    "4175179\tMiami Beach\tMiami Beach\t\t25.79065\t-80.13005\tP\tPPL\tUS\t\tFL\t086\t\t\t91732\t\t2\tAmerica/New_York\t2019-01-01",
    "3451190\tRio de Janeiro\tRio de Janeiro\tRio,Río de Janeiro\t-22.90278\t-43.2075\tP\tPPLA\tBR\t\t21\t3304557\t\t\t6023699\t\t8\tAmerica/Sao_Paulo\t2019-01-01",
    "2988507\tParis\tParis\tParis,Париж,巴黎\t48.85341\t2.3488\tP\tPPLC\tFR\t\t11\t75\t\t\t2138551\t\t42\tEurope/Paris\t2019-01-01",
    "4717560\tParis\tParis\t\t33.66094\t-95.55551\tP\tPPLA2\tUS\t\tTX\t277\t\t\t24716\t\t174\tAmerica/Chicago\t2019-01-01",
])


@pytest.fixture
def index(tmp_path):
    src = tmp_path / "cities15000.txt"
    src.write_text(SAMPLE + "\n", encoding="utf-8")
    idx = CityIndex(tmp_path / "cities.sqlite")
    idx.build_from_file(src)
    return idx


def test_parse_line():
    c = parse_geonames_line(SAMPLE.splitlines()[0])
    assert c.name == "Oslo" and c.country == "NO" and c.population == 580000
    assert c.timezone == "Europe/Oslo" and abs(c.lat - 59.91273) < 1e-6


def test_prefix_search_biggest_first(index):
    hits = index.search("mia")
    assert [h.name for h in hits] == ["Miami", "Miami Beach"]
    assert hits[0].admin1 == "FL" and hits[0].country == "US"


def test_same_name_ordered_by_population(index):
    hits = index.search("paris")
    assert [(h.name, h.country) for h in hits] == [("Paris", "FR"), ("Paris", "US")]


def test_alternate_names_and_accents(index):
    assert index.search("rio")[0].name == "Rio de Janeiro"
    assert index.search("Río de")[0].name == "Rio de Janeiro"
    assert index.search("Осло")[0].name == "Oslo"


def test_limit_and_empty(index):
    assert index.search("") == []
    assert len(index.search("m", limit=1)) == 1
    assert index.count() == 6
