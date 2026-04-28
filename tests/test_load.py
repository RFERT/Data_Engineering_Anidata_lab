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


# Skip load tests when Elasticsearch is not available in the environment.
@pytest.fixture(autouse=True)
def _skip_if_no_elasticsearch():
    try:
        import elasticsearch  # noqa: F401
    except ImportError:
        pytest.skip("elasticsearch package is not installed")


@pytest.fixture
def load_module():
    return _load_script("load")


class DummyIndices:
    # Emulate Elasticsearch index operations for unit tests.
    def __init__(self):
        self._exists = False

    def exists(self, index):
        return self._exists

    def delete(self, index):
        self._exists = False

    def create(self, index, mappings=None, settings=None):
        self._exists = True

    def refresh(self, index=None):
        return None


class DummyElasticsearch:
    # Provide a minimal Elasticsearch client stub for index creation and query verification.
    def __init__(self, *args, **kwargs):
        self.indices = DummyIndices()

    def ping(self):
        return True

    def count(self, index=None):
        return {"count": 1}

    def search(self, index=None, query=None, size=3):
        return {"hits": {"hits": [{"_source": {"Name": "Naruto"}}]}}


def test_create_index_mapping(load_module, monkeypatch):
    monkeypatch.setattr(load_module, "Elasticsearch", DummyElasticsearch)
    result = load_module.create_index_mapping()
    assert result["index"] == load_module.INDEX_NAME
    assert result["status"] == "created"


def test_bulk_index_and_verify(load_module, monkeypatch, tmp_path):
    monkeypatch.setattr(load_module, "Elasticsearch", DummyElasticsearch)
    monkeypatch.setattr(load_module.helpers, "bulk", lambda es, actions, raise_on_error, chunk_size: (len(actions), []))

    tmp = tmp_path / "data"
    tmp.mkdir()
    monkeypatch.setattr(load_module, "REP_SOURCE", str(tmp))

    df = pd.DataFrame({"MAL_ID": [1], "Name": ["Naruto"], "Score": [8.5]})
    df.to_csv(tmp / "anime_gold_latest.csv", index=False)

    result = load_module.bulk_index()
    assert result["indexed"] == 1
    assert result["errors"] == 0
    assert result["total"] == 1

    verify = load_module.verify_index()
    assert verify["doc_count"] == 1
    assert "Naruto" in verify["sample_titles"]
