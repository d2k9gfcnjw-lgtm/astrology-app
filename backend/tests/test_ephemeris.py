"""The engine must use the Swiss Ephemeris data files, never the Moshier fallback."""
from __future__ import annotations

import pytest

from app.engine import ephemeris
from app.engine.ephemeris import EphemerisDataMissing


def test_missing_data_dir_fails_loudly(tmp_path, monkeypatch):
    with pytest.raises(EphemerisDataMissing) as exc:
        ephemeris.init_ephemeris(tmp_path / "nowhere")
    assert "fetch_data.py" in str(exc.value)


def test_empty_data_dir_fails_loudly(tmp_path):
    (tmp_path / "ephe").mkdir()
    with pytest.raises(EphemerisDataMissing) as exc:
        ephemeris.init_ephemeris(tmp_path / "ephe")
    assert "sepl_18.se1" in str(exc.value)


def test_real_data_dir_initialises_and_reports_files():
    info = ephemeris.init_ephemeris()
    assert info.path.exists()
    assert "sepl_18.se1" in info.files and "semo_18.se1" in info.files and "seas_18.se1" in info.files
    assert info.swisseph_version.startswith("2.")


def test_calc_uses_swieph_flag_not_moshier():
    ephemeris.init_ephemeris()
    xx, retflag = ephemeris.calc_ut(2451545.0, ephemeris.SUN)
    assert retflag & ephemeris.FLG_SWIEPH
    assert not retflag & ephemeris.FLG_MOSEPH


def test_date_outside_files_raises():
    ephemeris.init_ephemeris()
    with pytest.raises(EphemerisDataMissing):
        ephemeris.calc_ut(1_000_000.0, ephemeris.SUN)  # year -1900, no file downloaded
