import os
import pandas as pd

from extractor import extract_data
from uploader import save_output
from reader import read_input
from loader import load_to_db

# =====================================================
# NEW PARSED OUTPUT SUPPORT
# =====================================================
from parsed_output_handler import (
    save_parsed_output
)

from parsers.parser_factory import (
    get_parser
)


# =========================================
# Helper
# =========================================
def safe_value(val):

    if pd.isna(val):
        return None

    return val


# =========================================
# Password Helper
# =========================================
def get_password(db_type):

    password_map = {

        "postgres": "DB_PASSWORD",

        "mysql": "MYSQL_PASSWORD",

        "mssql": "MSSQL_PASSWORD",

        "oracle": "ORACLE_PASSWORD",

        "sqlite": None
    }

    password_env = password_map.get(db_type)

    if password_env:
        return os.getenv(password_env)

    return ""


# =========================================
# Dynamic Filename Generator
# =========================================
def generate_output_filename(row):

    table_name = row["source_table_name"]

    file_format = row["target_file_format"]

    return f"{table_name}.{file_format}"


# =========================================
# Main Pipeline Executor
# =========================================
def run_pipeline(row: pd.Series):

    mode = row["pipeline_mode"]

    # =====================================================
    # DB → STORAGE
    # =====================================================
    if mode == "db_to_storage":

        source_db_type = row[
            "source_dataset_type"
        ].lower()

        password = get_password(
            source_db_type
        )

        source_config = {

            "db_type": source_db_type,

            "host": row["source_host"],

            "port": row["source_port"],

            "database": row["source_database"],

            "username": row["source_username"],

            "password": password
        }

        df = extract_data(

            source_config,

            row["source_query"]
        )

        target_type = row[
            "target_dataset_type"
        ].lower()

        generated_filename = (
            generate_output_filename(row)
        )

        # =================================================
        # S3 / AZURE STORAGE
        # =================================================
        if target_type in ["s3", "azure"]:

            target_key = (
                row["target_object_key"]
                + generated_filename
            )

            output_config = {

                "destination": target_type,

                "format":
                    row["target_file_format"],

                "target_bucket":
                    row["target_bucket"],

                "target_key":
                    target_key,

                "local_folder": None
            }

        # =================================================
        # LOCAL STORAGE
        # =================================================
        elif target_type == "local":

            local_folder = row[
                "target_file_path"
            ]

            full_local_path = os.path.join(

                local_folder,

                generated_filename
            )

            output_config = {

                "destination": target_type,

                "format":
                    row["target_file_format"],

                "target_bucket": None,

                "target_key": None,

                "local_folder":
                    full_local_path
            }

        else:

            raise ValueError(
                f"Unsupported target type: "
                f"{target_type}"
            )

        save_output(

            df,

            output_config,

            row["target_file_format"]
        )

        return len(df)

    # =====================================================
    # STORAGE → DB
    # =====================================================
    elif mode == "storage_to_db":

        source_type = row[
            "source_dataset_type"
        ].lower()

        input_config = {

            "source": source_type,

            "format":
                row["source_file_format"],

            "s3_bucket":
                row["source_bucket"],

            "s3_key":
                row["source_object_key"],

            "file_path":
                row["source_file_path"]
        }

        ingestion_units = read_input(
            input_config
        )

        target_type = row[
            "target_dataset_type"
        ].lower()

        password = get_password(
            target_type
        )

        total_rows = 0

        for unit in ingestion_units:

            table_name = unit[
                "table_name"
            ]

            df = unit[
                "dataframe"
            ]

            print(
                f"Loading table: "
                f"{table_name} "
                f"({len(df)} rows)"
            )

            target_config = {

                "type": target_type,

                "host":
                    safe_value(
                        row["target_host"]
                    ) or "localhost",

                "port": int(

                    safe_value(
                        row["target_port"]
                    ) or 5432
                ),

                "name":

                    safe_value(
                        row["target_database"]
                    ) or "destination_db",

                "user":

                    safe_value(
                        row["target_username"]
                    ) or "postgres",

                "password": password,

                "table": table_name,

                "if_exists": "replace"
            }

            load_to_db(
                df,
                target_config
            )

            total_rows += len(df)

        print(
            f"Processed total rows: "
            f"{total_rows}"
        )

        return total_rows

    # =====================================================
    # STORAGE → PARSED STORAGE
    # =====================================================
    elif mode == "storage_to_parsed_storage":

        source_type = row[
            "source_dataset_type"
        ].lower()

        input_config = {

            "source": source_type,

            "format":
                row["source_file_format"],

            "file_path":
                row["source_file_path"]
        }

        ingestion_units = read_input(
            input_config
        )

        total_processed = 0

        # -------------------------------------------------
        # PROCESS EACH FILE
        # -------------------------------------------------
        for unit in ingestion_units:

            try:

                table_name = unit[
                    "table_name"
                ]

                original_file_path = unit[
                    "original_file_path"
                ]

                print(
                    f"Parsing file: "
                    f"{original_file_path}"
                )

                # -----------------------------------------
                # DETECT ACTUAL FILE TYPE
                # -----------------------------------------
                actual_extension = (

                    os.path.splitext(
                        original_file_path
                    )[1]

                    .replace(".", "")

                    .lower()
                )

                # -----------------------------------------
                # GET PARSER DYNAMICALLY
                # -----------------------------------------
                parser = get_parser(
                    actual_extension
                )

                parsed_result = parser(
                    original_file_path
                )

                # -----------------------------------------
                # SAVE PARSED OUTPUT
                # -----------------------------------------
                target_type = row[
                    "target_dataset_type"
                ].lower()

                if target_type == "local":

                    save_parsed_output(

                        parsed_result,

                        "local",

                        row["target_file_path"]
                    )

                elif target_type == "s3":

                    save_parsed_output(

                        parsed_result,

                        "s3",

                        row["target_object_key"],

                        bucket_name=
                        row["target_bucket"]
                    )

                else:

                    raise ValueError(
                        f"Unsupported parsed "
                        f"target: {target_type}"
                    )

                total_processed += 1

            # =================================================
            # FILE-LEVEL FAILURE HANDLING
            # =================================================
            except Exception as e:

                print(
                    f"❌ Failed file: "
                    f"{original_file_path}"
                )

                print(
                    f"Reason: {str(e)}"
                )

                # ---------------------------------------------
                # MOVE TO FAILED FOLDER
                # ---------------------------------------------
                failed_folder = (
                    "C:/Users/subas/"
                    "OneDrive/Desktop/failed/"
                )

                os.makedirs(
                    failed_folder,
                    exist_ok=True
                )

                failed_file_path = os.path.join(

                    failed_folder,

                    os.path.basename(
                        original_file_path
                    )
                )

                try:

                    os.replace(

                        original_file_path,

                        failed_file_path
                    )

                    print(
                        f"Moved to failed/: "
                        f"{failed_file_path}"
                    )

                except Exception as move_error:

                    print(
                        f"Could not move failed file: "
                        f"{move_error}"
                    )

                continue

        print(
            f"Parsed files processed: "
            f"{total_processed}"
        )

        return total_processed

    # =====================================================
    # DB → DB
    # =====================================================
    elif mode == "db_to_db":

        source_db_type = row[
            "source_dataset_type"
        ].lower()

        password = get_password(
            source_db_type
        )

        source_config = {

            "db_type": source_db_type,

            "host": row["source_host"],

            "port": row["source_port"],

            "database": row["source_database"],

            "username": row["source_username"],

            "password": password
        }

        df = extract_data(

            source_config,

            row["source_query"]
        )

        target_type = row[
            "target_dataset_type"
        ].lower()

        target_password = get_password(
            target_type
        )

        target_config = {

            "type": target_type,

            "host":
                safe_value(
                    row["target_host"]
                ) or "localhost",

            "port": int(

                safe_value(
                    row["target_port"]
                ) or 5432
            ),

            "name":

                safe_value(
                    row["target_database"]
                ) or "destination_db",

            "user":

                safe_value(
                    row["target_username"]
                ) or "postgres",

            "password": target_password,

            "table":
                row["source_table_name"],

            "if_exists": "replace"
        }

        load_to_db(
            df,
            target_config
        )

        return len(df)

    # =====================================================
    # STORAGE → STORAGE
    # =====================================================
    elif mode == "storage_to_storage":

        source_type = row[
            "source_dataset_type"
        ].lower()

        input_config = {

            "source": source_type,

            "format":
                row["source_file_format"],

            "s3_bucket":
                row["source_bucket"],

            "s3_key":
                row["source_object_key"],

            "file_path":
                row["source_file_path"]
        }

        ingestion_units = read_input(
            input_config
        )

        total_rows = 0

        for unit in ingestion_units:

            table_name = unit[
                "table_name"
            ]

            df = unit[
                "dataframe"
            ]

            print(
                f"Processing file: "
                f"{table_name} "
                f"({len(df)} rows)"
            )

            target_type = row[
                "target_dataset_type"
            ].lower()

            filename = (
                f"{table_name}."
                f"{row['target_file_format']}"
            )

            # =================================
            # TARGET = S3
            # =================================
            if target_type == "s3":

                output_config = {

                    "destination": "s3",

                    "format":
                        row["target_file_format"],

                    "target_bucket":
                        row["target_bucket"],

                    "target_key":
                        row["target_object_key"]
                        + filename,

                    "local_folder": None
                }

            # =================================
            # TARGET = LOCAL
            # =================================
            elif target_type == "local":

                full_local_path = os.path.join(

                    row["target_file_path"],

                    filename
                )

                output_config = {

                    "destination": "local",

                    "format":
                        row["target_file_format"],

                    "target_bucket": None,

                    "target_key": None,

                    "local_folder":
                        full_local_path
                }

            else:

                raise ValueError(
                    f"Unsupported target type: "
                    f"{target_type}"
                )

            save_output(

                df,

                output_config,

                row["target_file_format"]
            )

            total_rows += len(df)

        print(
            f"Processed total rows: "
            f"{total_rows}"
        )

        return total_rows

    # =====================================================
    # INVALID MODE
    # =====================================================
    else:

        raise ValueError(
            f"Unsupported pipeline mode: {mode}"
        )
