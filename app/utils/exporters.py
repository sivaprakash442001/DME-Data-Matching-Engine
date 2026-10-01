"""
Export utilities for Match results (CSV and Excel formats).
"""
import io
import json
from typing import List, Dict, Any
import pandas as pd
from app.scoring.scorer import MatchResult


def results_to_dataframe(results: List[MatchResult], col_a_name: str = "Column_A", col_b_name: str = "Column_B") -> pd.DataFrame:
    """
    Convert a list of MatchResult objects into a well-structured DataFrame.
    """
    rows = []
    for idx, r in enumerate(results, start=1):
        explanation = r.explanation
        rows.append({
            "Row": idx,
            f"Original_{col_a_name}": explanation.original_a,
            f"Original_{col_b_name}": explanation.original_b,
            f"Normalized_{col_a_name}": explanation.normalized_a,
            f"Normalized_{col_b_name}": explanation.normalized_b,
            "Match_Score": r.score,
            "Match_Status": r.status,
            "Confidence": r.confidence,
            "Match_Type": r.matching_type,
            "Matching_Tokens": ", ".join(explanation.matching_tokens),
            "Match_Summary": explanation.summary,
            "Component_Scores": json.dumps(explanation.component_scores),
        })
    return pd.DataFrame(rows)


def export_to_csv_bytes(df_results: pd.DataFrame) -> bytes:
    """Generate CSV bytes for download."""
    output = io.StringIO()
    df_results.to_csv(output, index=False)
    return output.getvalue().encode("utf-8")


def export_to_excel_bytes(df_results: pd.DataFrame) -> bytes:
    """Generate Excel (.xlsx) bytes for download with auto-adjusted column widths."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_results.to_excel(writer, index=False, sheet_name="Match Results")
        # Format worksheet columns
        worksheet = writer.sheets["Match Results"]
        for col in worksheet.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = min(len(val_str), 50)
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    return output.getvalue()
