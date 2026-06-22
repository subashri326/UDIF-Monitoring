from parsers.pdf_parser import parse_pdf

from parsed_output_handler import (
    save_parsed_output
)

parsed = parse_pdf(
    "sample.pdf"
)

save_parsed_output(

    parsed,

    "local",

    "parsed_output/"
)