"""
File reader utility.
Handles CSV, XLSX, XLS, and JSON formats with encoding detection and metadata inspection.
"""
import io
import json
import os
from typing import Dict, Any, Tuple
import pandas as pd


def read_uploaded_file(file_path_or_bytes: Any, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Read an uploaded file (CSV, XLSX, XLS, JSON) into a pandas DataFrame.
    Returns (DataFrame, metadata_dict).
    """
    ext = os.path.splitext(filename)[1].lower()
    df = None

    if ext == ".csv":
        # Handle multiple possible encodings
        if isinstance(file_path_or_bytes, (str, os.PathLike)):
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    df = pd.read_csv(file_path_or_bytes, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                df = pd.read_csv(file_path_or_bytes, encoding="utf-8", errors="replace")
        else:
            # Bytes or file-like
            raw_bytes = file_path_or_bytes.read() if hasattr(file_path_or_bytes, "read") else file_path_or_bytes
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    df = pd.read_csv(io.BytesIO(raw_bytes), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                df = pd.read_csv(io.BytesIO(raw_bytes), encoding="utf-8", errors="replace")

    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path_or_bytes)

    elif ext == ".json":
        if isinstance(file_path_or_bytes, (str, os.PathLike)):
            df = pd.read_json(file_path_or_bytes)
        else:
            raw_bytes = file_path_or_bytes.read() if hasattr(file_path_or_bytes, "read") else file_path_or_bytes
            df = pd.read_json(io.BytesIO(raw_bytes))

    else:
        raise ValueError(f"Unsupported file format '{ext}'. Supported formats: .csv, .xlsx, .xls, .json")

    # Clean column names
    df.columns = [str(c).strip() for c in df.columns]

    # Replace all NaN with empty strings for consistency
    df = df.fillna("")

    metadata = {
        "filename": filename,
        "rows": len(df),
        "columns_count": len(df.columns),
        "columns": list(df.columns),
        "preview": df.head(5).to_dict(orient="records"),
    }

    return df, metadata
