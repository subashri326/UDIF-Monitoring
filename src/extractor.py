import pandas as pd
 
from sqlalchemy import create_engine
 
 
# =====================================================

# DATABASE CONNECTION

# =====================================================

def connect_db(config):
 
    db_type = config.get(

        "db_type"

    )
 
    host = config.get(

        "host"

    )
 
    port = config.get(

        "port"

    )
 
    database = config.get(

        "database"

    )
 
    username = config.get(

        "username"

    )
 
    password = config.get(

        "password"

    )
 
    # -------------------------------------------------

    # DEBUG

    # -------------------------------------------------

    print("\n===================================")

    print("DATABASE CONNECTION CONFIG")

    print("===================================")
 
    print(f"DB TYPE   : {db_type}")

    print(f"HOST      : {host}")

    print(f"PORT      : {port}")

    print(f"DATABASE  : {database}")

    print(f"USERNAME  : {username}")
 
    print("===================================\n")
 
    # =================================================

    # POSTGRES

    # =================================================

    if db_type == "postgres":
 
        connection_string = (
 
            f"postgresql+psycopg2://"
 
            f"{username}:{password}"
 
            f"@{host}:{port}/{database}"

        )
 
    # =================================================

    # MYSQL

    # =================================================

    elif db_type == "mysql":
 
        connection_string = (
 
            f"mysql+pymysql://"
 
            f"{username}:{password}"
 
            f"@{host}:{port}/{database}"

        )
 
    # =================================================

    # MSSQL

    # =================================================

    elif db_type == "mssql":
 
        connection_string = (
 
            f"mssql+pyodbc://"
 
            f"{username}:{password}"
 
            f"@{host}:{port}/{database}"
 
            f"?driver=ODBC+Driver+17+for+SQL+Server"

        )
 
    # =================================================

    # SQLITE

    # =================================================

    elif db_type == "sqlite":
 
        connection_string = (

            f"sqlite:///{database}"

        )
 
    else:
 
        raise ValueError(

            f"Unsupported DB type: {db_type}"

        )
 
    # =================================================

    # CREATE ENGINE

    # =================================================

    try:
 
        engine = create_engine(

            connection_string

        )
 
        # -------------------------------------------------

        # TEST CONNECTION

        # -------------------------------------------------

        with engine.connect() as conn:
 
            print(

                f"Connected to "

                f"{db_type.upper()} successfully."

            )
 
        return engine
 
    except Exception as e:
 
        raise ConnectionError(

            f"Could not connect to "

            f"{db_type.upper()}: {e}"

        )
 
 
# =====================================================

# EXTRACT DATA

# =====================================================

def extract_data(config, query):
 
    engine = connect_db(config)
 
    df = pd.read_sql(

        query,

        engine

    )
 
    return df
 