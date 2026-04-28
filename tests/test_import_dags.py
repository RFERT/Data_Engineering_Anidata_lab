import importlib.util
import sys
from pathlib import Path

import pytest

# This test verifies that all Airflow DAG definitions can be imported cleanly.
# It protects the CI pipeline from broken DAG syntax or missing dependencies.

def test_dag_imports():
    if importlib.util.find_spec("airflow") is None:
        pytest.skip("Airflow is not installed in this environment")

    from airflow.models import DagBag

    root = Path(__file__).resolve().parents[1]
    dag_folder = root / "airflow" / "dags"
    # Import all DAG files under the project airflow/dags directory.
    dagbag = DagBag(dag_folder=str(dag_folder), include_examples=False)
    assert len(dagbag.import_errors) == 0, f"Import errors: {dagbag.import_errors}"
