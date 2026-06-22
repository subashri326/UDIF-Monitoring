from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
default_args = {
   "owner": "subashri",
   "depends_on_past": False,
   "start_date": datetime(2025, 1, 1),
   "retries": 1
}

def get_active_pipeline_ids():
   hook = PostgresHook(
       postgres_conn_id="metadata_db"
   )
   records = hook.get_records(
       """
       SELECT pipeline_id
       FROM pipeline_master
       WHERE is_active = TRUE
       ORDER BY pipeline_id
       """
   )
   return [row[0] for row in records]

with DAG(
   dag_id="dynamic_metadata_pipeline",
   default_args=default_args,
   schedule=None,
   catchup=False,
   tags=["udif", "metadata", "etl"]
) as dag:
   pipeline_ids = get_active_pipeline_ids()
   for pipeline_id in pipeline_ids:
       BashOperator(
           task_id=f"run_pipeline_{pipeline_id}",
           bash_command=(
               f"cd /opt/airflow/src && "
               f"python main.py {pipeline_id}"
           )
       )