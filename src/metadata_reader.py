import os
 
from dotenv import load_dotenv
 
from extractor import extract_data
 
 
# ==========================================
# LOAD .env
# ==========================================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)
 
ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)
 
load_dotenv(ENV_PATH)
 
 
# ==========================================
# LOAD PIPELINE METADATA
# ==========================================
def load_metadata(pipeline_id):
 
    # ======================================
    # CENTRALIZED METADATA DB CONNECTION
    # ======================================
    config = {
 
        "db_type": "postgres",
 
        "host": os.getenv(
            "METADATA_DB_HOST"
        ),
 
        "port": os.getenv(
            "METADATA_DB_PORT"
        ),
 
        "database": os.getenv(
            "METADATA_DB_NAME"
        ),
 
        "username": os.getenv(
            "METADATA_DB_USER"
        ),
 
        "password": os.getenv(
            "METADATA_DB_PASSWORD"
        )
    }
 
    # ======================================
    # ENTERPRISE DATASET-DRIVEN QUERY
    # ======================================
    query = f"""
 
        SELECT
 
            -- =================================
            -- PIPELINE INFO
            -- =================================
            pm.pipeline_id,
 
            pm.pipeline_name,
 
            pm.is_active,
 
            pc.pipeline_mode,
 
            -- =================================
            -- SOURCE DATASET
            -- =================================
            src.dataset_id
                AS source_dataset_id,
 
            src.dataset_name
                AS source_dataset_name,
 
            src.dataset_type
                AS source_dataset_type,
 
            src.storage_type
                AS source_storage_type,
 
            src.host
                AS source_host,
 
            src.port
                AS source_port,
 
            src.database_name
                AS source_database,
 
            src.username
                AS source_username,
 
            src.source_query
                AS source_query,
 
            src.file_path
                AS source_file_path,
 
            src.bucket_name
                AS source_bucket,
 
            src.object_key
                AS source_object_key,
 
            src.recursive_scan
                AS source_recursive_scan,
 
            src.file_format
                AS source_file_format,
 
            src.source_table_name
                AS source_table_name,
 
            -- =================================
            -- TARGET DATASET
            -- =================================
            tgt.dataset_id
                AS target_dataset_id,
 
            tgt.dataset_name
                AS target_dataset_name,
 
            tgt.dataset_type
                AS target_dataset_type,
 
            tgt.storage_type
                AS target_storage_type,
 
            tgt.host
                AS target_host,
 
            tgt.port
                AS target_port,
 
            tgt.database_name
                AS target_database,
 
            tgt.username
                AS target_username,
 
            tgt.source_query
                AS target_query,
 
            tgt.file_path
                AS target_file_path,
 
            tgt.bucket_name
                AS target_bucket,
 
            tgt.object_key
                AS target_object_key,
 
            tgt.recursive_scan
                AS target_recursive_scan,
 
            tgt.file_format
                AS target_file_format,
 
            tgt.source_table_name
                AS target_table_name
 
        FROM pipeline_master pm
 
        JOIN pipeline_config pc
            ON pm.pipeline_id = pc.pipeline_id
 
        -- =================================
        -- SOURCE DATASET JOIN
        -- =================================
        JOIN dataset_master src
            ON pc.source_dataset_id =
               src.dataset_id
 
        -- =================================
        -- TARGET DATASET JOIN
        -- =================================
        JOIN dataset_master tgt
            ON pc.target_dataset_id =
               tgt.dataset_id
 
        WHERE pm.pipeline_id = {pipeline_id}
 
        AND pm.is_active = TRUE
 
    """
 
    # ======================================
    # FETCH METADATA
    # ======================================
    metadata_df = extract_data(
 
        config,
 
        query
    )
 
    return metadata_df