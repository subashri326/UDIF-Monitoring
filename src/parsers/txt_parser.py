from schema.detector import detect_schema


def parse_txt(file_path):

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        lines = f.readlines()

    data = [

        {
            "text": line.strip()
        }

        for line in lines
    ]

    return {

        "file": file_path,

        "type": "txt",

        "schema": detect_schema(data),

        "data": data
    }
