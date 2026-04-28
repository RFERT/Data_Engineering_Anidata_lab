import importlib.util
from pathlib import Path

import pandas as pd
import pytest

# Root path for the Data-Engineering-101 project.
ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    path = ROOT / "airflow" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load the extract script implementation dynamically for white-box testing.
extract = _load_script("extract")


def test_extract_csv_and_validate_schema(tmp_path, monkeypatch):
    # Create a temporary data directory and a small sample CSV file.
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    monkeypatch.setattr(extract, "REP_SOURCE", str(data_dir))

    df = pd.DataFrame({
        "MAL_ID": [1],
        "Name": ["Naruto"],
        "Score": [8.2],
        "Genres": ["Action, Adventure"],
        "Type": ["TV"],
        "Episodes": [220],
        "Studios": ["Pierrot"],
        "Source": ["Manga"],
        "Members": [1000000],
        "Favorites": [50000],
        "Watching": [200000],
        "Completed": [600000],
        "On-Hold": [50000],
        "Dropped": [15000],
        "Plan to Watch": [150000],
    })
    csv_path = data_dir / "anime.csv"
    df.to_csv(csv_path, index=False)

    def fake_to_parquet(self, path, index=False):
        Path(path).write_text("parquet placeholder")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    result = extract.extract_csv("anime")
    assert result["dataset"] == "anime"
    assert result["rows"] == 1
    assert (data_dir / "raw_anime.parquet").exists()

    validation = extract.validate_schema("anime", result)
    assert validation["status"] == "valid"
    assert validation["rows"] == 1
    assert validation["columns_checked"] == len(extract.EXPECTED_SCHEMAS["anime"]["required_columns"])


def test_validate_schema_missing_columns():
    fake_result = {
        "dataset": "anime",
        "rows": 1,
        "columns": ["MAL_ID", "Name", "Score"],
    }
    with pytest.raises(ValueError, match=r"Colonnes manquantes"):
        extract.validate_schema("anime", fake_result)
