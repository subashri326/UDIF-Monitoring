import boto3
import pandas as pd
import io
import os
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings

logger = logging.getLogger(__name__)


def upload_to_s3(df: pd.DataFrame, bucket: str, key: str, fmt: str = "csv") -> None:
    fmt = fmt.lower().strip()
    buffer = io.StringIO()

    if fmt == "csv":
        df.to_csv(buffer, index=False)
        content_type = "text/csv"
    elif fmt == "json":
        df.to_json(buffer, orient="records", indent=2)
        content_type = "application/json"
    else:
        raise ValueError(f"Unsupported format '{fmt}'. Choose 'csv' or 'json'.")

    data = buffer.getvalue().encode("utf-8")

    base_key = key.rsplit(".", 1)[0]
    final_key = f"{base_key}.{fmt}"

    logger.info(f"Uploading to s3://{bucket}/{final_key} ...")

    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=final_key,
        Body=data,   # ✅ FIXED
        ContentType=content_type,
    )

    logger.info(f"Uploaded to s3://{bucket}/{final_key}")


def save_to_local(df: pd.DataFrame, folder: str, filename: str, fmt: str = "csv") -> None:
    fmt = fmt.lower().strip()
    os.makedirs(folder, exist_ok=True)

    base = filename.rsplit(".", 1)[0]
    final_filename = f"{base}.{fmt}"
    filepath = os.path.join(folder, final_filename)

    if fmt == "csv":
        df.to_csv(filepath, index=False)
    elif fmt == "json":
        df.to_json(filepath, orient="records", indent=2)
    else:
        raise ValueError(f"Unsupported format '{fmt}'. Choose 'csv' or 'json'.")

    logger.info(f"Saved locally → {filepath}")


def upload_to_azure(df: pd.DataFrame, container: str, blob: str, fmt: str = "csv") -> None:
    fmt    = fmt.lower().strip()
    buffer = io.StringIO()
    if fmt == "csv":
        df.to_csv(buffer, index=False)
        content_type = "text/csv"
    elif fmt == "json":
        df.to_json(buffer, orient="records", indent=2)
        content_type = "application/json"
    else:
        raise ValueError(f"Unsupported format '{fmt}'. Choose 'csv' or 'json'.")

    data = buffer.getvalue().encode("utf-8")

    base_blob  = blob.rsplit(".", 1)[0]
    final_blob = f"{base_blob}.{fmt}"

    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    if not connection_string:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING not set in .env.")

    logger.info(f"Uploading to azure://{container}/{final_blob} ...")
    client      = BlobServiceClient.from_connection_string(connection_string)
    blob_client = client.get_blob_client(container=container, blob=final_blob)
    blob_client.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )
    logger.info(f"Uploaded to azure://{container}/{final_blob} ✓")


def save_output(df: pd.DataFrame, output_config: dict, fmt: str) -> None:
    """
    Routes output to S3, Azure, or local folder based on config.
    destination: s3 | azure | local
    """
    destination = output_config.get("destination", "s3").lower()

    if destination == "s3":
        bucket = output_config["target_bucket"]
        key    = output_config.get("target_key", f"output.{fmt}")
        upload_to_s3(df, bucket, key, fmt)

    elif destination == "azure":
        container = output_config.get("target_bucket", "")
        blob      = output_config.get("target_key", f"output.{fmt}")
        if not container or not blob:
            raise ValueError("output.target_bucket and output.target_key are required when destination is 'azure'.")
        upload_to_azure(df, container, blob, fmt)

    elif destination == "local":
        folder   = output_config.get("local_folder", "output")
        filename = output_config.get("filename", f"output.{fmt}")
        save_to_local(df, folder, filename, fmt)

    else:
        raise ValueError(f"Unsupported destination '{destination}'. Use 's3', 'azure', or 'local'.")