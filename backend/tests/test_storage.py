"""Chart library: encrypted at rest, soft delete only, search and tags."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.storage import ChartLibrary, SubjectIn


@pytest.fixture
def lib(tmp_path):
    return ChartLibrary(db_path=tmp_path / "charts.sqlite", key_path=tmp_path / "keys" / "charts.key")


def _subject(**over):
    base = dict(
        name="Test Person", kind="person", tags=["family", "golden"], notes="born at home",
        datetime_local=datetime(1992, 7, 23, 4, 23), time_confidence="exact",
        place_name="Oslo, Norway", lat=59.9167, lon=10.75, timezone="Europe/Oslo", utc_offset_override=None,
        settings={},
    )
    base.update(over)
    return SubjectIn(**base)


def test_key_file_is_created_once(tmp_path):
    key_path = tmp_path / "k" / "charts.key"
    a = ChartLibrary(db_path=tmp_path / "a.sqlite", key_path=key_path)
    assert key_path.exists()
    first = key_path.read_bytes()
    b = ChartLibrary(db_path=tmp_path / "b.sqlite", key_path=key_path)
    assert key_path.read_bytes() == first
    assert (key_path.stat().st_mode & 0o777) == 0o600
    del a, b


def test_round_trip(lib):
    created = lib.create(_subject())
    got = lib.get(created.id)
    assert got.name == "Test Person"
    assert got.datetime_local == datetime(1992, 7, 23, 4, 23)
    assert got.lat == 59.9167 and got.lon == 10.75
    assert got.place_name == "Oslo, Norway"
    assert got.tags == ["family", "golden"]
    assert got.time_confidence == "exact"
    assert got.created_at is not None and got.deleted_at is None


def test_raw_database_has_no_plaintext_birth_data(lib, tmp_path):
    lib.create(_subject(name="Zelda Zebra", place_name="Unique Town", notes="secretnote"))
    lib.close()
    raw = (tmp_path / "charts.sqlite").read_bytes()
    for needle in (b"Zelda", b"Zebra", b"1992-07-23", b"Unique Town", b"secretnote", b"59.9167", b"10.75"):
        assert needle not in raw, needle


def test_update_and_list(lib):
    s = lib.create(_subject())
    lib.create(_subject(name="Another", kind="event", tags=["work"]))
    updated = lib.update(s.id, _subject(name="Renamed", tags=["family"]))
    assert updated.name == "Renamed"
    names = sorted(x.name for x in lib.list())
    assert names == ["Another", "Renamed"]


def test_search_by_name_and_tag(lib):
    lib.create(_subject(name="Alpha One", tags=["a"]))
    lib.create(_subject(name="Beta Two", tags=["b", "shared"]))
    lib.create(_subject(name="Gamma Three", tags=["a", "shared"]))
    assert [x.name for x in lib.list(query="beta")] == ["Beta Two"]
    assert sorted(x.name for x in lib.list(tag="shared")) == ["Beta Two", "Gamma Three"]
    assert [x.name for x in lib.list(query="gam", tag="a")] == ["Gamma Three"]
    assert sorted(lib.tags()) == ["a", "b", "shared"]


def test_delete_is_soft_and_restorable(lib, tmp_path):
    s = lib.create(_subject(name="Keep Me"))
    lib.delete(s.id)
    assert lib.list() == []
    assert [x.name for x in lib.list(include_deleted=True)] == ["Keep Me"]
    assert lib.get(s.id).deleted_at is not None
    lib.restore(s.id)
    assert [x.name for x in lib.list()] == ["Keep Me"]


def test_get_missing_raises(lib):
    with pytest.raises(KeyError):
        lib.get("nope")
