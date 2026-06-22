"""
Airflow REST API client for the UDIF UI.

All calls go through this module — pages never call requests directly.
Credentials are read from src/.env via the same pattern as connection.py.

Airflow REST API docs: https://airflow.apache.org/docs/apache-airflow/stable/stable-rest-api-ref.html
"""
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# ── Load shared .env ───────────────────────────────────────────────────────────
_THIS_FILE    = os.path.abspath(__file__)
_DASHBOARD    = os.path.dirname(_THIS_FILE)          # streamlit_dashboard/
_PROJECT_ROOT = os.path.dirname(_DASHBOARD)           # JDBC/
_ENV_PATH     = os.path.join(_PROJECT_ROOT, "src", ".env")
load_dotenv(_ENV_PATH)

AIRFLOW_BASE_URL = os.getenv("AIRFLOW_BASE_URL", "http://localhost:8080")
AIRFLOW_USER     = os.getenv("AIRFLOW_USER",     "airflow")
AIRFLOW_PASSWORD = os.getenv("AIRFLOW_PASSWORD",  "airflow")

_API = f"{AIRFLOW_BASE_URL.rstrip('/')}/api/v1"
_AUTH = lambda: (AIRFLOW_USER, AIRFLOW_PASSWORD)


def _get(path: str) -> dict:
    """GET request, returns parsed JSON or raises RuntimeError."""
    try:
        r = requests.get(f"{_API}{path}", auth=_AUTH(), timeout=8)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach Airflow at {AIRFLOW_BASE_URL}. "
            f"Is the webserver running?"
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Airflow API error {r.status_code}: {r.text}") from e


def _post(path: str, body: dict = None) -> dict:
    try:
        r = requests.post(
            f"{_API}{path}", auth=_AUTH(),
            json=body or {}, timeout=8,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach Airflow at {AIRFLOW_BASE_URL}. "
            f"Is the webserver running?"
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Airflow API error {r.status_code}: {r.text}") from e


def _patch(path: str, body: dict) -> dict:
    try:
        r = requests.patch(
            f"{_API}{path}", auth=_AUTH(),
            json=body, timeout=8,
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Cannot reach Airflow at {AIRFLOW_BASE_URL}. "
            f"Is the webserver running?"
        )
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"Airflow API error {r.status_code}: {r.text}") from e


# ── Public API ─────────────────────────────────────────────────────────────────

def health() -> dict:
    """
    Returns Airflow health status.
    Response: { "metadatabase": {"status": "healthy"}, "scheduler": {"status": "healthy"} }
    """
    return _get("/health")


def list_dags() -> list[dict]:
    """
    Returns list of all DAGs Airflow knows about.
    Each dict has: dag_id, is_paused, is_active, last_parsed_time, next_dagrun, tags, etc.
    """
    data = _get("/dags?limit=100")
    return data.get("dags", [])


def get_dag(dag_id: str) -> dict:
    """Get a single DAG's metadata."""
    return _get(f"/dags/{dag_id}")


def trigger_dag(dag_id: str, note: str = "") -> dict:
    """
    Trigger a DAG run immediately.
    Returns the new dag_run object with run_id, state, execution_date.
    """
    body = {
        "dag_run_id": f"manual__{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}",
        "note": note or "Triggered from UDIF Portal",
    }
    return _post(f"/dags/{dag_id}/dagRuns", body)


def pause_dag(dag_id: str) -> dict:
    """Pause a DAG (disables scheduled runs)."""
    return _patch(f"/dags/{dag_id}", {"is_paused": True})


def unpause_dag(dag_id: str) -> dict:
    """Unpause a DAG (re-enables scheduled runs)."""
    return _patch(f"/dags/{dag_id}", {"is_paused": False})


def get_dag_runs(dag_id: str, limit: int = 10) -> list[dict]:
    """
    Returns the most recent DAG runs for a given DAG.
    Each dict has: dag_run_id, state, execution_date, start_date, end_date, note.
    """
    data = _get(f"/dags/{dag_id}/dagRuns?limit={limit}&order_by=-execution_date")
    return data.get("dag_runs", [])


def get_task_instances(dag_id: str, dag_run_id: str) -> list[dict]:
    """
    Returns task instances for a specific DAG run.
    Each dict has: task_id, state, start_date, end_date, duration, try_number.
    """
    data = _get(f"/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances")
    return data.get("task_instances", [])