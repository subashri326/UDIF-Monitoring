import pandas as pd
import re
import logging

logger = logging.getLogger("transformer")


# ══════════════════════════════════════════════════════════════════
# LAYER 1 — Generic (always runs, works with any dataset)
# ══════════════════════════════════════════════════════════════════

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    original_cols = df.columns.tolist()
    df.columns = [re.sub(r'\W+', '_', col.strip().lower()) for col in df.columns]
    logger.info(f"Columns standardized: {original_cols} → {df.columns.tolist()}")
    return df

def normalize_complex_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert list/dict columns into string so Pandas can process them.
    """
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].astype(str)
            logger.info(f"Converted complex column '{col}' to string")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    cols = [c for c in df.columns if c != "id"]
    df = df.drop_duplicates(subset=cols)
    logger.info(f"Duplicates removed: {before - len(df)}")
    return df


def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    logger.info("String columns trimmed")
    return df


def convert_data_types(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype == object:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() > 0.9 * len(df):
                df[col] = converted
                logger.info(f"Converted '{col}' to numeric")
                continue
        if df[col].dtype == object:
            try:
                converted = pd.to_datetime(df[col], errors="coerce")
                if converted.notna().sum() > 0.9 * len(df):
                    df[col] = converted
                    logger.info(f"Converted '{col}' to datetime")
            except Exception:
                pass
    return df


def handle_missing_values(df: pd.DataFrame, null_rules: dict = {}) -> pd.DataFrame:
    """
    Smart null handling.
    Uses null_rules from config if provided, otherwise falls back to:
    - Numeric  → mean
    - String   → Unknown
    - Datetime → leave as NaT
    """
    missing_before = df.isnull().sum().sum()
    if missing_before == 0:
        logger.info("No missing values found, skipping fill step")
        return df

    logger.info(f"Missing values found: {missing_before}")

    for col in df.columns:
        if df[col].isnull().sum() == 0:
            continue

        rule = null_rules.get(col, None)

        if rule == "drop":
            df = df.dropna(subset=[col])
            logger.info(f"'{col}' → dropped rows with nulls")
        elif rule == "leave":
            logger.info(f"'{col}' → leaving nulls as is")
        elif rule == "unknown":
            df[col] = df[col].fillna("Unknown")
            logger.info(f"'{col}' → filled with 'Unknown'")
        elif rule == "median" and pd.api.types.is_numeric_dtype(df[col]):
            median_val = round(df[col].median(), 2)
            df[col] = df[col].fillna(median_val)
            logger.info(f"'{col}' → filled with median: {median_val}")
        elif rule == "mean" and pd.api.types.is_numeric_dtype(df[col]):
            mean_val = round(df[col].mean(), 2)
            df[col] = df[col].fillna(mean_val)
            logger.info(f"'{col}' → filled with mean: {mean_val}")
        else:
            # Smart default fallback
            if pd.api.types.is_numeric_dtype(df[col]):
                mean_val = round(df[col].mean(), 2)
                df[col] = df[col].fillna(mean_val)
                logger.info(f"'{col}' → filled with mean: {mean_val} (default)")
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                logger.info(f"'{col}' → datetime, leaving NaT as is")
            else:
                df[col] = df[col].fillna("Unknown")
                logger.info(f"'{col}' → filled with 'Unknown' (default)")

    return df


# ══════════════════════════════════════════════════════════════════
# LAYER 2 — Custom (only runs if transformation section exists in config.yaml)
# ══════════════════════════════════════════════════════════════════

def validate_data(df: pd.DataFrame, range_rules: dict = {}, positive_cols: list = []) -> pd.DataFrame:
    """Config-driven validation — range and positive checks."""
    for col, bounds in range_rules.items():
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            before = len(df)
            df = df[df[col].between(bounds["min"], bounds["max"])]
            removed = before - len(df)
            if removed:
                logger.info(f"Removed {removed} rows: '{col}' outside {bounds['min']}-{bounds['max']}")

    for col in positive_cols:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            before = len(df)
            df = df[df[col] > 0]
            removed = before - len(df)
            if removed:
                logger.info(f"Removed {removed} rows: '{col}' is non-positive")

    return df


def detect_name_columns(df: pd.DataFrame, name_config: dict = {}) -> tuple:
    first_candidates = name_config.get("first_name", ["first_name", "fname", "firstname"])
    last_candidates  = name_config.get("last_name",  ["last_name", "lname", "lastname", "surname"])
    first_col = next((col for col in df.columns if any(k in col for k in first_candidates)), None)
    last_col  = next((col for col in df.columns if any(k in col for k in last_candidates)), None)
    return first_col, last_col


def apply_name_rules(df: pd.DataFrame, name_config: dict = {}) -> pd.DataFrame:
    first_col, last_col = detect_name_columns(df, name_config)

    if not first_col or not last_col or first_col == last_col:
        logger.info("Name columns not found or same — skipping name rules")
        return df

    mask = df[first_col] == "Unknown"
    df.loc[mask, first_col] = df.loc[mask, last_col]
    df[first_col] = df[first_col].replace("Unknown", "Default")

    mask = df[last_col] == "Unknown"
    df.loc[mask, last_col] = df.loc[mask, first_col]
    df[last_col] = df[last_col].replace("Unknown", "Default")

    def build_full_name(row):
        first = row[first_col] if row[first_col] not in ("Default", "Unknown") else ""
        last  = row[last_col]  if row[last_col]  not in ("Default", "Unknown") else ""
        if first == last and first != "":
            return first
        if not first and not last:
            return "Default"
        return (first + " " + last).strip()

    df["full_name"] = df.apply(build_full_name, axis=1)
    logger.info(f"Created 'full_name' from '{first_col}' + '{last_col}'")
    return df


# ══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def transform_data(df: pd.DataFrame, rules: dict = {}) -> pd.DataFrame:
    """
    Two-layer transformation pipeline:

    Layer 1 — Generic (always runs):
        standardize_columns → remove_duplicates → clean_strings
        → convert_data_types → handle_missing_values

    Layer 2 — Custom (only if transformation section exists in config.yaml):
        validate_data → apply_name_rules
    """
    logger.info("Starting transformation pipeline")
    initial_rows = len(df)
    initial_cols = len(df.columns)

    # ── Layer 1: Generic
    logger.info("[ Layer 1 ] Generic transformation...")
    df = standardize_columns(df)
    df = normalize_complex_columns(df)
    df = remove_duplicates(df)
    df = clean_strings(df)
    df = convert_data_types(df)
    df = handle_missing_values(df, rules.get("null_handling", {}))

    # ── Layer 2: Custom 
    if rules:
        logger.info("[ Layer 2 ] Custom rules found in config.yaml, applying...")
        steps         = rules.get("steps", {})
        range_rules   = rules.get("range_validation", {})
        positive_cols = rules.get("positive_validation", [])
        name_config   = rules.get("name_columns", {})

        if steps.get("validate_data", True):
            df = validate_data(df, range_rules, positive_cols)

        if steps.get("apply_name_rules", True):
            df = apply_name_rules(df, name_config)
    else:
        logger.info("[ Layer 2 ] No custom rules in config.yaml, skipping...")

    logger.info(
        f"Transformation complete → "
        f"{initial_rows} rows, {initial_cols} cols "
        f"→ {len(df)} rows, {len(df.columns)} cols"
    )

    return df