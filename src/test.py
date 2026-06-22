from parser_adapter import parse_file_to_dataframe


result = parse_file_to_dataframe(
    "sample.pdf"
)

print(result["table_name"])

print(result["dataframe"].head())