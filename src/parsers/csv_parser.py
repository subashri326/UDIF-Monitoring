import pandas as pd

from schema.detector import detect_schema


def parse_csv(file_path):

    df = pd.read_csv(file_path)

    data = df.to_dict(orient="records")

    return {

        "file": file_path,

        "type": "csv",

        "schema": detect_schema(data),

        "data": data
    }