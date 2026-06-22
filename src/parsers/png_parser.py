import easyocr

from schema.detector import detect_schema


reader = easyocr.Reader(['en'], gpu=False)


def parse_png(file_path):

    results = reader.readtext(file_path)

    data = []

    for res in results:

        data.append({

            "text": str(res[1]),

            "confidence": float(res[2])
        })

    return {

        "file": file_path,

        "type": "png",

        "schema": detect_schema(data),

        "data": data
    }
