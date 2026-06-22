# =====================================================
# PARSER FACTORY
# =====================================================
def get_parser(file_type):
   # ================================================
   # CSV
   # ================================================
   if file_type == "csv":
       from parsers.csv_parser import parse_csv
       return parse_csv
   # ================================================
   # TXT
   # ================================================
   elif file_type == "txt":
       from parsers.txt_parser import parse_txt
       return parse_txt
   # ================================================
   # XML
   # ================================================
   elif file_type == "xml":
       from parsers.xml_parser import parse_xml
       return parse_xml
   # ================================================
   # PDF
   # ================================================
   elif file_type == "pdf":
       from parsers.pdf_parser import parse_pdf
       return parse_pdf
   # ================================================
   # PNG
   # ================================================
   elif file_type == "png":
       from parsers.png_parser import parse_png
       return parse_png
   # ================================================
   # DOCX
   # ================================================
   elif file_type == "docx":
       from parsers.docx_parser import parse_docx
       return parse_docx
   # ================================================
   # UNSUPPORTED
   # ================================================
   raise Exception(
       f"Unsupported file type: {file_type}"
   )