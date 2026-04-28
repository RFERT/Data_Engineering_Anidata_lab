import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    path = ROOT / "airflow" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


transform = _load_script("transform")


def _fake_to_parquet(self, path, index=False):
    # Simulate parquet writes without requiring an actual parquet engine.
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("parquet placeholder")


def test_clean_anime(tmp_path, monkeypatch):
    # Verify the anime cleaning pipeline removes duplicates and writes the output file.
    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(transform, "REP_SOURCE", str(tmp))
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet)

    raw = pd.DataFrame({
        "MAL_ID": [1, 1],
        "Name": [" Naruto ", "Naruto"],
        "Score": ["8.2", "8.2"],
        "Episodes": ["220", "220"],
        "Ranked": ["1", "1"],
        "Score-1": ["10", "10"],
        "Score-2": ["5", "5"],
        "Score-3": ["0", "0"],
        "Score-4": ["0", "0"],
        "Score-5": ["0", "0"],
        "Score-6": ["0", "0"],
        "Score-7": ["0", "0"],
        "Score-8": ["0", "0"],
        "Score-9": ["0", "0"],
        "Score-10": ["0", "0"],
    })
    monkeypatch.setattr(transform, "load_raw", lambda dataset_key: raw)

    result = transform.clean_anime()
    assert result["rows"] == 1
    assert result["nulls"] >= 0
    assert (tmp / "clean_anime.parquet").exists()


def test_clean_synopsis(tmp_path, monkeypatch):
    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(transform, "REP_SOURCE", str(tmp))
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet)

    raw = pd.DataFrame({
        "MAL_ID": [1, 2],
        "Name": ["Naruto", "Bleach"],
        "sypnopsis": [" Synopsis ", "No synopsis information has been added to this title."],
    })
    monkeypatch.setattr(transform, "load_raw", lambda dataset_key: raw)

    result = transform.clean_synopsis()
    assert result["rows"] == 2
    assert (tmp / "clean_synopsis.parquet").exists()


def test_clean_ratings(tmp_path, monkeypatch):
    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(transform, "REP_SOURCE", str(tmp))
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet)

    raw = pd.DataFrame({
        "user_id": [1, 1, 2],
        "anime_id": [10, 10, 20],
        "rating": [5, 5, 11],
    })
    monkeypatch.setattr(transform, "load_raw", lambda dataset_key: raw)

    result = transform.clean_ratings()
    assert result["rows"] == 1
    assert (tmp / "clean_ratings.parquet").exists()


def test_merge_datasets(monkeypatch):
    # Validate that cleaned anime and synopsis data are joined correctly.
    tmp = Path("/opt/airflow/data")
    tmp.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(transform, "REP_SOURCE", str(tmp))

    anime = pd.DataFrame({"MAL_ID": [1], "Name": ["Naruto"]})
    synopsis = pd.DataFrame({"MAL_ID": [1], "Synopsis": ["synopsis"]})
    monkeypatch.setattr(transform.pd, "read_parquet", lambda path: anime if "clean_anime" in str(path) else synopsis)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet)

    result = transform.merge_datasets()
    assert result["rows"] == 1
    assert result["with_synopsis"] == 1


def test_feature_engineering(monkeypatch):
    tmp = Path("/opt/airflow/data")
    tmp.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(transform, "REP_SOURCE", str(tmp))

    data = pd.DataFrame({
        "MAL_ID": [1, 2],
        "Score": [8.0, 9.0],
        "Members": [1000, 50],
        "Completed": [900, 30],
        "Dropped": [100, 20],
        "Studios": ["Studio A", "Studio B"],
        "Duration": ["1 hr 30 min", "24 min"],
        "Genres": ["Action, Adventure", "Comedy"],
        "Favorites": [500, 10],
        "Aired": ["Jan 1, 2020", None],
    })
    monkeypatch.setattr(transform.pd, "read_parquet", lambda path: data)
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet)

    result = transform.feature_engineering()
    assert result["rows"] == 2
    assert "weighted_score" in result["new_features"]
