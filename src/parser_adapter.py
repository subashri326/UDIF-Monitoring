import pandas as pd
import os

from parsers.parser_factory import get_parser


# =====================================================
# PARSE FILE USING UNIVERSAL PARSER ENGINE
# =====================================================
def parse_file_to_dataframe(file_path):

    # -------------------------------------------------
    # DETECT FILE TYPE
    # -------------------------------------------------
    file_type = (
        file_path.split(".")[-1]
        .lower()
    )

    # -------------------------------------------------
    # GET PARSER
    # -------------------------------------------------
    parser = get_parser(file_type)

    # -------------------------------------------------
    # PARSE FILE
    # -------------------------------------------------
    result = parser(file_path)

    # -------------------------------------------------
    # VALIDATION
    # -------------------------------------------------
    if "data" not in result:

        raise Exception(
            f"No data returned from parser "
            f"for file: {file_path}"
        )

    # -------------------------------------------------
    # CONVERT TO DATAFRAME
    # -------------------------------------------------
    df = pd.DataFrame(
        result["data"]
    )

    # -------------------------------------------------
    # GENERATE TABLE NAME
    # -------------------------------------------------
    filename = os.path.basename(
        file_path
    )

    table_name = os.path.splitext(
        filename
    )[0]

    return {

        "table_name": table_name,

        "dataframe": df,

        "schema": result.get("schema"),

        "file_type": file_type
    }