import os

from dotenv import load_dotenv

import psycopg2

BASE_DIR = os.path.dirname(

    os.path.abspath(__file__)

)

load_dotenv(

    os.path.join(BASE_DIR, ".env")

)


def log_audit(

    pipeline_id,

    pipeline_name,

    start_time,

    end_time,

    status,

    records_processed=0,
    duration_seconds=0,

    error_message=None

):

    conn = psycopg2.connect(

        host=os.getenv("METADATA_DB_HOST"),

        port=os.getenv("METADATA_DB_PORT"),

        database=os.getenv("METADATA_DB_NAME"),

        user=os.getenv("METADATA_DB_USER"),

        password=os.getenv("METADATA_DB_PASSWORD")

    )

    cur = conn.cursor()

    cur.execute(

        """

        INSERT INTO pipeline_audit

        (

            pipeline_id,

            pipeline_name,

            start_time,

            end_time,

            status,

            records_processed,
            duration_seconds,
            error_message

        )

        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)

        """,

        (

            pipeline_id,

            pipeline_name,

            start_time,

            end_time,

            status,

            records_processed,
            duration_seconds,
            error_message

        )

    )

    conn.commit()

    cur.close()

    conn.close()
 