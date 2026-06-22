
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus
import logging
import json

logger = logging.getLogger(__name__)


def build_target_url(db_type: str, host: str, port: str, name: str, user: str, password: str) -> str:
    """Build SQLAlchemy URL for target DB."""
    pwd = quote_plus(str(password))

    if db_type == "postgres":
        return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"
    elif db_type == "mysql":
        return f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{name}"
    elif db_type == "mssql":
        return f"mssql+pyodbc://{user}:{pwd}@{host}:{port}/{name}?driver=ODBC+Driver+17+for+SQL+Server"
    elif db_type == "sqlite":
        return f"sqlite:///{name}"
    else:
        raise ValueError(f"Unsupported target db type: '{db_type}'")


def load_to_db(df: pd.DataFrame, target_config: dict) -> None:
    """
    Load DataFrame into target database table.

    Args:
        df:            Transformed DataFrame
        target_config: target_db config
    """

    # ============================
    # ✅ STEP 1: Ensure DataFrame
    # ============================
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)

    # ============================
    # ✅ STEP 2: Convert dict/list → JSON string
    # ============================
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x
        )

    # ============================
    # 🔽 EXISTING CONFIG LOGIC
    # ============================
    db_type  = target_config.get("type", "postgres").lower()
    host     = target_config.get("host", "localhost")
    port     = str(target_config.get("port", "5432"))
    name     = target_config.get("name", "")
    user     = target_config.get("user", "")
    password = target_config.get("password", "")
    table    = target_config.get("table", "output_table")
    if_exists = target_config.get("if_exists", "replace")

    if not name or not user:
        raise ValueError("Target DB config missing 'name' or 'user'.")

    url    = build_target_url(db_type, host, port, name, user, password)
    engine = create_engine(url)

    logger.info(
        f"Loading {len(df)} rows into [{db_type.upper()}] "
        f"{host}:{port}/{name} → table: '{table}' (if_exists: {if_exists})"
    )

    # ============================
    # ✅ LOAD TO DB
    # ============================
    df.to_sql(
        name=table,
        con=engine,
        if_exists=if_exists,
        index=False,
        chunksize=1000,
    )

    engine.dispose()
    logger.info(f"Loaded successfully → table '{table}' ✓")
