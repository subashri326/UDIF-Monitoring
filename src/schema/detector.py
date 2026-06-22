def detect_schema(data):

    if not data:
        return {}

    sample = data[0]

    schema = {}

    for key, value in sample.items():

        schema[key] = type(value).__name__

    return schema