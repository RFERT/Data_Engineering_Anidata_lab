import importlib.util
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_script(name):
    path = ROOT / "airflow" / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anomaly = _load_script("anomaly")


def _fake_to_parquet(self, path, index=False):
    # Simulate parquet writes in tests for anomaly detection outputs.
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("parquet placeholder")


def test_detect_spam_users_and_mono_raters(tmp_path, monkeypatch):
    # Validate spam and mono-rater detection logic using a synthetic ratings set.
    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(anomaly, "REP_SOURCE", str(tmp))
    monkeypatch.setattr(pd.DataFrame, "to_parquet", _fake_to_parquet)

    ratings = pd.DataFrame({
        "user_id": [1] * 11 + [2] * 5,
        "anime_id": list(range(11)) + list(range(5)),
        "rating": [5] * 16,
    })
    ratings.to_csv(tmp / "rating_complete.csv", index=False)

    spam = anomaly.detect_spam_users(min_ratings=5)
    assert spam["spam_users"] == 1
    assert spam["max_ratings"] == 11
    assert (tmp / "anomalies_spam.parquet").exists()

    mono = anomaly.detect_mono_raters()
    assert mono["mono_raters"] == 1
    assert (tmp / "anomalies_mono.parquet").exists()


def test_detect_suspicious_ratings(tmp_path, monkeypatch):
    # Confirm that the review-bombing logic flags at least one suspicious title.
    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(anomaly, "REP_SOURCE", str(tmp))

    df = pd.DataFrame({
        "MAL_ID": [1, 2],
        "Name": ["Naruto", "One Piece"],
        "Score": [8.2, 6.5],
        "Score-1": [90, 0],
        "Score-2": [11, 100],
        "Score-3": [0, 0],
        "Score-4": [0, 0],
        "Score-5": [0, 0],
        "Score-6": [0, 0],
        "Score-7": [0, 0],
        "Score-8": [0, 0],
        "Score-9": [0, 0],
        "Score-10": [0, 0],
    })
    df.to_csv(tmp / "anime_gold_latest.csv", index=False)

    result = anomaly.detect_suspicious_ratings()
    assert result["total_checked"] == 2
    assert result["review_bombed"] == 1
    assert (tmp / "anomalies_review_bombing.csv").exists()


def test_anomaly_report(tmp_path, monkeypatch):
    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(anomaly, "REP_SOURCE", str(tmp))

    (tmp / "anomalies_spam.parquet").write_text("dummy")
    (tmp / "anomalies_mono.parquet").write_text("dummy")
    (tmp / "anomalies_review_bombing.csv").write_text("dummy")

    monkeypatch.setattr(anomaly.pd, "read_parquet", lambda path: pd.DataFrame([{"dummy": 1}]))

    report = anomaly.anomaly_report()
    assert "report_path" in report
    assert (tmp / "anomaly_report.txt").exists()
