import PyPDF2

from schema.detector import detect_schema


def parse_pdf(file_path):

    data = []

    with open(file_path, "rb") as f:

        reader = PyPDF2.PdfReader(f)

        for i, page in enumerate(reader.pages):

            text = page.extract_text()

            data.append({

                "page": i + 1,

                "text": text if text else ""
            })

    return {

        "file": file_path,

        "type": "pdf",

        "schema": detect_schema(data),

        "data": data
    }
