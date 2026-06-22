from datetime import datetime

from airflow import DAG

from airflow.operators.bash import BashOperator

from airflow.providers.postgres.hooks.postgres import PostgresHook


def get_active_pipelines():

    hook = PostgresHook(

        postgres_conn_id="metadata_db"

    )

    records = hook.get_records(

        """

        SELECT

            pipeline_id,

            pipeline_name,

            cron_expression

        FROM pipeline_master

        WHERE is_active = TRUE

        """

    )

    return records


default_args = {

    "owner": "subashri",

    "depends_on_past": False,

    "start_date": datetime(2025, 1, 1),

    "retries": 1

}


for pipeline_id, pipeline_name, cron_expression in get_active_pipelines():

    dag = DAG(

        dag_id=pipeline_name,

        default_args=default_args,

        schedule=cron_expression,

        catchup=False,

        tags=["udif", "metadata", "etl"]

    )

    BashOperator(

        task_id=f"run_pipeline_{pipeline_id}",

        bash_command=(

            f"cd /opt/airflow/src && "

            f"python main.py {pipeline_id}"

        ),

        dag=dag

    )

    globals()[pipeline_name] = dag
 