import boto3
import pandas as pd
import io
import os
import logging

from azure.storage.blob import BlobServiceClient

# =====================================================
# NEW PARSER ENGINE INTEGRATION
# =====================================================
from parser_adapter import (
    parse_file_to_dataframe
)

# =====================================================
# SUPPORTED FORMATS
# =====================================================
from supported_formats import (
    SUPPORTED_FORMATS
)

logger = logging.getLogger(__name__)


# =====================================================
# DIRECT PANDAS FORMATS
# =====================================================
DIRECT_FORMATS = [
    "csv",
    "json"
]


# =====================================================
# S3 READ (UNCHANGED)
# =====================================================
def read_from_s3(
    bucket: str,
    key: str,
    fmt: str
):

    fmt = fmt.lower().strip()

    logger.info(
        f"Reading s3://{bucket}/{key} "
        f"as {fmt.upper()} ..."
    )

    s3_client = boto3.client("s3")

    extension = f".{fmt}"

    # =================================================
    # CASE 1 → SINGLE FILE
    # =================================================
    if not key.endswith("/"):

        response = s3_client.get_object(
            Bucket=bucket,
            Key=key
        )

        body = response["Body"].read()

        # ---------------------------------------------
        # DIRECT PANDAS PARSING
        # ---------------------------------------------
        if fmt == "csv":

            df = pd.read_csv(
                io.BytesIO(body)
            )

        elif fmt == "json":

            df = pd.read_json(
                io.BytesIO(body),
                orient="records"
            )

        else:

            raise ValueError(
                f"S3 parser integration for "
                f"{fmt} not yet enabled."
            )

        filename = os.path.basename(key)

        table_name = os.path.splitext(
            filename
        )[0]

        return [

            {
                "table_name": table_name,

                "dataframe": df,

                "original_file_path": key
            }
        ]

    # =================================================
    # CASE 2 → FOLDER / PREFIX INGESTION
    # =================================================
    logger.info(
        f"Scanning S3 prefix: {key}"
    )

    response = s3_client.list_objects_v2(
        Bucket=bucket,
        Prefix=key
    )

    if "Contents" not in response:

        raise ValueError(
            f"No files found under prefix: {key}"
        )

    files = [

        obj["Key"]

        for obj in response["Contents"]

        if obj["Key"].lower().endswith(extension)
    ]

    if not files:

        raise ValueError(
            f"No {fmt.upper()} files found "
            f"under prefix: {key}"
        )

    ingestion_units = []

    for file_key in files:

        response = s3_client.get_object(
            Bucket=bucket,
            Key=file_key
        )

        body = response["Body"].read()

        if fmt == "csv":

            df = pd.read_csv(
                io.BytesIO(body)
            )

        elif fmt == "json":

            df = pd.read_json(
                io.BytesIO(body),
                orient="records"
            )

        else:

            raise ValueError(
                f"S3 parser integration for "
                f"{fmt} not yet enabled."
            )

        filename = os.path.basename(
            file_key
        )

        table_name = os.path.splitext(
            filename
        )[0]

        ingestion_units.append({

            "table_name": table_name,

            "dataframe": df,

            "original_file_path": file_key
        })

    return ingestion_units


# =====================================================
# LOCAL READ (MIXED FORMAT SUPPORT)
# =====================================================
def read_from_local(
    file_path: str,
    fmt: str
):

    fmt = fmt.lower().strip()

    if not os.path.exists(file_path):

        raise FileNotFoundError(
            f"Input path not found: {file_path}"
        )

    # =================================================
    # CASE 1 → SINGLE FILE
    # =================================================
    if os.path.isfile(file_path):

        logger.info(
            f"Reading single file: {file_path}"
        )

        actual_extension = (

            os.path.splitext(file_path)[1]
            .replace(".", "")
            .lower()
        )

        # ---------------------------------------------
        # VALIDATION
        # ---------------------------------------------
        if actual_extension not in SUPPORTED_FORMATS:

            raise ValueError(
                f"Unsupported format: "
                f"{actual_extension}"
            )

        # ---------------------------------------------
        # CSV
        # ---------------------------------------------
        if actual_extension == "csv":

            df = pd.read_csv(file_path)

        # ---------------------------------------------
        # JSON
        # ---------------------------------------------
        elif actual_extension == "json":

            df = pd.read_json(

                file_path,

                orient="records"
            )

        # ---------------------------------------------
        # PARSER ENGINE
        # ---------------------------------------------
        else:

            parsed = parse_file_to_dataframe(
                file_path
            )

            return [

                {
                    "table_name":
                        parsed["table_name"],

                    "dataframe":
                        parsed["dataframe"],

                    "original_file_path":
                        file_path
                }
            ]

        filename = os.path.basename(
            file_path
        )

        table_name = os.path.splitext(
            filename
        )[0]

        return [

            {
                "table_name": table_name,

                "dataframe": df,

                "original_file_path":
                    file_path
            }
        ]

    # =================================================
    # CASE 2 → MIXED-FORMAT FOLDER INGESTION
    # =================================================
    elif os.path.isdir(file_path):

        logger.info(
            f"Scanning mixed-format folder: "
            f"{file_path}"
        )

        files = []

        # ---------------------------------------------
        # DISCOVER ALL SUPPORTED FILES
        # ---------------------------------------------
        for f in os.listdir(file_path):

            extension = (

                os.path.splitext(f)[1]
                .replace(".", "")
                .lower()
            )

            if extension in SUPPORTED_FORMATS:

                files.append(

                    os.path.join(file_path, f)
                )

        if not files:

            raise ValueError(
                f"No supported files found "
                f"in folder: {file_path}"
            )

        logger.info(
            f"Found {len(files)} supported files"
        )

        ingestion_units = []

        # ---------------------------------------------
        # PROCESS EACH FILE DYNAMICALLY
        # ---------------------------------------------
        for file in files:

            logger.info(
                f"Processing file: {file}"
            )

            extension = (

                os.path.splitext(file)[1]
                .replace(".", "")
                .lower()
            )

            # -----------------------------------------
            # CSV
            # -----------------------------------------
            if extension == "csv":

                df = pd.read_csv(file)

                filename = os.path.basename(
                    file
                )

                table_name = os.path.splitext(
                    filename
                )[0]

                ingestion_units.append({

                    "table_name": table_name,

                    "dataframe": df,

                    "original_file_path": file
                })

            # -----------------------------------------
            # JSON
            # -----------------------------------------
            elif extension == "json":

                df = pd.read_json(

                    file,

                    orient="records"
                )

                filename = os.path.basename(
                    file
                )

                table_name = os.path.splitext(
                    filename
                )[0]

                ingestion_units.append({

                    "table_name": table_name,

                    "dataframe": df,

                    "original_file_path": file
                })

            # -----------------------------------------
            # UNIVERSAL PARSER ENGINE
            # -----------------------------------------
            else:

                parsed = parse_file_to_dataframe(
                    file
                )

                ingestion_units.append({

                    "table_name":
                        parsed["table_name"],

                    "dataframe":
                        parsed["dataframe"],

                    "original_file_path":
                        file
                })

        logger.info(
            f"Prepared "
            f"{len(ingestion_units)} "
            f"ingestion units ✓"
        )

        return ingestion_units

    # =================================================
    # INVALID PATH
    # =================================================
    else:

        raise ValueError(
            f"Invalid path: {file_path}"
        )


# =====================================================
# AZURE READ (UNCHANGED)
# =====================================================
def read_from_azure(
    container: str,
    blob: str,
    fmt: str,
    connection_string: str
):

    raise NotImplementedError(
        "Azure parser integration pending."
    )


# =====================================================
# MAIN INPUT READER
# =====================================================
def read_input(input_config: dict):

    source = input_config.get(
        "source",
        "local"
    ).lower()

    fmt = input_config.get(
        "format",
        "mixed"
    ).lower()

    # =================================================
    # LOCAL
    # =================================================
    if source == "local":

        file_path = input_config.get(
            "file_path",
            ""
        )

        if not file_path:

            raise ValueError(
                "input.file_path is required "
                "when input.source is 'local'."
            )

        return read_from_local(
            file_path,
            fmt
        )

    # =================================================
    # S3
    # =================================================
    elif source == "s3":

        bucket = input_config.get(
            "s3_bucket",
            ""
        )

        key = input_config.get(
            "s3_key",
            ""
        )

        if not bucket or not key:

            raise ValueError(
                "input.s3_bucket and "
                "input.s3_key are required "
                "when input.source is 's3'."
            )

        return read_from_s3(
            bucket,
            key,
            fmt
        )

    # =================================================
    # AZURE
    # =================================================
    elif source == "azure":

        raise NotImplementedError(
            "Azure parser integration pending."
        )

    # =================================================
    # INVALID SOURCE
    # =================================================
    else:

        raise ValueError(
            f"Unsupported input source '{source}'. "
            f"Use 'local', 's3', or 'azure'."
        )