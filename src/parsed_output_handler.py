import os
import json
import boto3


# =====================================================
# SAVE PARSED OUTPUT
# =====================================================
def save_parsed_output(

    parsed_result,

    destination_type,

    destination_path,

    bucket_name=None
):

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------
    if not isinstance(parsed_result, dict):

        raise Exception(
            "Parsed result must be dictionary"
        )

    if "data" not in parsed_result:

        raise Exception(
            "Parsed result missing data"
        )

    # -------------------------------------------------
    # GENERATE OUTPUT FILE NAME
    # -------------------------------------------------
    original_file = parsed_result.get(
        "file",
        "output"
    )

    filename = os.path.basename(
        original_file
    )

    filename_without_ext = os.path.splitext(
        filename
    )[0]

    output_filename = (
        filename_without_ext
        + ".json"
    )

    # =================================================
    # LOCAL OUTPUT
    # =================================================
    if destination_type == "local":

        os.makedirs(
            destination_path,
            exist_ok=True
        )

        full_output_path = os.path.join(

            destination_path,

            output_filename
        )

        with open(

            full_output_path,

            "w",

            encoding="utf-8"

        ) as f:

            json.dump(

                parsed_result,

                f,

                indent=4,

                ensure_ascii=False
            )

        print(
            f"Saved parsed output locally: "
            f"{full_output_path}"
        )

        return full_output_path

    # =================================================
    # S3 OUTPUT
    # =================================================
    elif destination_type == "s3":

        if not bucket_name:

            raise Exception(
                "bucket_name required for S3"
            )

        s3 = boto3.client("s3")

        key = (
            destination_path
            + output_filename
        )

        s3.put_object(

            Bucket=bucket_name,

            Key=key,

            Body=json.dumps(
                parsed_result,
                indent=4
            )
        )

        print(
            f"Uploaded parsed output to S3: "
            f"{key}"
        )

        return key

    # =================================================
    # INVALID DESTINATION
    # =================================================
    else:

        raise Exception(
            f"Unsupported destination type: "
            f"{destination_type}"
        )