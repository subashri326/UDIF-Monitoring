from docx import Document

from schema.detector import detect_schema


def parse_docx(file_path):

    doc = Document(file_path)

    data = [

        {
            "text": para.text
        }

        for para in doc.paragraphs

        if para.text.strip()
    ]

    return {

        "file": file_path,

        "type": "docx",

        "schema": detect_schema(data),

        "data": data
    }
