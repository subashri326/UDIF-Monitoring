import os

def build_pipeline_config(row):
    # dynamically fetch password based on DB type
    db_type = row["source_type"].lower()

    password_key_map = {
        "postgres": "DB_PASSWORD",
        "mysql": "MYSQL_PASSWORD",
        "mssql": "MSSQL_PASSWORD",
        "oracle": "ORACLE_PASSWORD"
    }

    password_key = password_key_map.get(db_type)
    password = os.getenv(password_key)

    if not password:
        raise ValueError(f"{password_key} not found in .env")

    source_config = {
        "db_type": db_type,
        "host": row["source_host"],
        "port": row["source_port"],
        "database": row["source_db"],
        "username": row["source_user"],
        "password": password   # ✅ FIXED
    }

    target_config = {
        "bucket": row["target_bucket"],
        "key": row["target_key"],
        "format": row["file_format"]
    }

    query = row["source_query"]

    return source_config, target_config, query