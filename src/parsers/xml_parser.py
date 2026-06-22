import xml.etree.ElementTree as ET

from schema.detector import detect_schema


def parse_xml(file_path):

    tree = ET.parse(file_path)

    root = tree.getroot()

    data = []

    for child in root:

        row = {}

        for elem in child:

            row[elem.tag] = elem.text

        data.append(row)

    return {

        "file": file_path,

        "type": "xml",

        "schema": detect_schema(data),

        "data": data
    }
