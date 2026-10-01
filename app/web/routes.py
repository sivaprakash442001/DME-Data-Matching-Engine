"""
Web and REST API routes for Data Matching Engine.
"""
import os
import uuid
from typing import Dict, List, Optional, Any
import pandas as pd
import gc
import threading
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, Response, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.normalization.cleaner import NormalizationSettings, default_normalizer
from app.normalization.abbreviations import global_abbrev_manager
from app.matching.engine import default_engine, MatchingEngine
from app.matching.detector import detect_column_type
from app.scoring.scorer import MatchThresholds, MatchScorer, MatchResult
from app.scoring.weights import DEFAULT_WEIGHT_PROFILES, get_weights_for_type
from app.utils.file_reader import read_uploaded_file
from app.utils.exporters import results_to_dataframe, export_to_csv_bytes, export_to_excel_bytes
from app.utils.sample_generator import (
    SAMPLE_ADDRESS_DATA,
    SAMPLE_COMPANY_DATA,
    SAMPLE_PERSON_DATA,
    SAMPLE_CUSTOMER_DATA,
)

router = APIRouter()

# In-memory storage for active sessions/jobs (persisted for the application lifecycle)
UPLOAD_CACHE: Dict[str, Dict[str, Any]] = {}
JOB_CACHE: Dict[str, Dict[str, Any]] = {}
JOB_PROGRESS: Dict[str, Dict[str, Any]] = {}

UPLOAD_DIR = os.path.abspath("data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
EXPORT_DIR = os.path.abspath("data/exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


class QuickMatchRequest(BaseModel):
    str_a: str
    str_b: str
    matching_type: str = "auto"
    normalization_mode: str = "standard"
    case_sensitive: bool = False
    remove_punctuation: bool = True
    normalize_whitespace: bool = True
    expand_abbreviations: bool = True
    normalize_numbers: bool = True
    custom_weights: Optional[Dict[str, float]] = None


class ColumnMatchConfig(BaseModel):
    col_a: str
    col_b: str
    type: str = "auto"
    weight: float = 1.0


class MatchJobRequest(BaseModel):
    file_id: str
    col_a: Optional[str] = None
    col_b: Optional[str] = None
    matching_type: str = "auto"
    normalization_mode: str = "standard"
    case_sensitive: bool = False
    remove_punctuation: bool = True
    normalize_whitespace: bool = True
    expand_abbreviations: bool = True
    normalize_numbers: bool = True
    custom_weights: Optional[Dict[str, float]] = None
    thresholds: Optional[Dict[str, float]] = None
    is_multi_column: bool = False
    multi_columns: Optional[List[ColumnMatchConfig]] = None


class AddDictionaryRuleRequest(BaseModel):
    abbreviation: str
    expansion: str


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handle CSV, XLSX, XLS, or JSON upload. Returns column list and detected types.
    """
    try:
        content = await file.read()
        file_id = str(uuid.uuid4())
        filename = file.filename or "uploaded_data.csv"

        saved_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
        with open(saved_path, "wb") as f:
            f.write(content)

        df, meta = read_uploaded_file(saved_path, filename)

        # Detect column types
        detected_types = {}
        for col in df.columns:
            samples = list(df[col].dropna().astype(str).head(30))
            col_type, conf = detect_column_type(samples, col)
            detected_types[col] = {
                "type": col_type,
                "confidence": conf,
            }

        UPLOAD_CACHE[file_id] = {
            "file_id": file_id,
            "filename": filename,
            "path": saved_path,
            "df": df,
            "columns": list(df.columns),
            "rows": len(df),
            "detected_types": detected_types,
            "preview": meta["preview"],
        }

        return {
            "status": "success",
            "file_id": file_id,
            "filename": filename,
            "rows": len(df),
            "columns": list(df.columns),
            "detected_types": detected_types,
            "preview": meta["preview"],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")


@router.get("/api/sample/{sample_name}")
async def load_sample_dataset(sample_name: str):
    """
    Quickly load one of the built-in demo datasets (addresses, companies, names, customers).
    """
    sample_name = sample_name.lower().strip()
    data_map = {
        "addresses": (SAMPLE_ADDRESS_DATA, "sample_addresses.csv", "Address_A", "Address_B", "address"),
        "companies": (SAMPLE_COMPANY_DATA, "sample_companies.csv", "Company_A", "Company_B", "company"),
        "names": (SAMPLE_PERSON_DATA, "sample_names.csv", "Name_A", "Name_B", "person_name"),
        "customers": (SAMPLE_CUSTOMER_DATA, "sample_customers.xlsx", "Address_1", "Address_2", "address"),
    }

    if sample_name not in data_map:
        raise HTTPException(status_code=404, detail="Sample dataset not found")

    data, filename, default_col_a, default_col_b, suggested_type = data_map[sample_name]
    df = pd.DataFrame(data)

    file_id = f"sample_{sample_name}_{uuid.uuid4().hex[:6]}"
    saved_path = os.path.join(UPLOAD_DIR, f"{file_id}_{filename}")
    df.to_csv(saved_path, index=False)

    detected_types = {}
    for col in df.columns:
        samples = list(df[col].dropna().astype(str).head(30))
        col_type, conf = detect_column_type(samples, col)
        detected_types[col] = {
            "type": col_type,
            "confidence": conf,
        }

    UPLOAD_CACHE[file_id] = {
        "file_id": file_id,
        "filename": filename,
        "path": saved_path,
        "df": df,
        "columns": list(df.columns),
        "rows": len(df),
        "detected_types": detected_types,
        "preview": df.head(5).to_dict(orient="records"),
    }

    return {
        "status": "success",
        "file_id": file_id,
        "filename": filename,
        "rows": len(df),
        "columns": list(df.columns),
        "detected_types": detected_types,
        "default_col_a": default_col_a,
        "default_col_b": default_col_b,
        "suggested_type": suggested_type,
        "preview": df.head(5).to_dict(orient="records"),
    }


def execute_matching_job_worker(job_id: str, req: MatchJobRequest, df: pd.DataFrame):
    try:
        # Construct NormalizationSettings
        settings = NormalizationSettings(
            mode=req.normalization_mode,
            case_sensitive=req.case_sensitive,
            remove_punctuation=req.remove_punctuation,
            normalize_whitespace=req.normalize_whitespace,
            expand_abbreviations=req.expand_abbreviations,
            normalize_numbers=req.normalize_numbers,
        )

        # Thresholds
        thresholds = MatchThresholds()
        if req.thresholds:
            thresholds.strong = req.thresholds.get("strong", 85.0)
            thresholds.likely = req.thresholds.get("likely", 70.0)
            thresholds.possible = req.thresholds.get("possible", 40.0)
            thresholds.weak = req.thresholds.get("weak", 20.0)

        scorer = MatchScorer(thresholds=thresholds)
        engine = MatchingEngine(scorer=scorer)

        total_rows = len(df)

        def progress_cb(processed, total):
            pct = round((processed / total) * 100.0, 1) if total > 0 else 0
            if job_id in JOB_PROGRESS:
                JOB_PROGRESS[job_id]["processed"] = processed
                JOB_PROGRESS[job_id]["total"] = total
                JOB_PROGRESS[job_id]["percentage"] = pct
                JOB_PROGRESS[job_id]["message"] = f"Processed {processed:,} of {total:,} rows ({pct}%)"

        # Perform matching
        if req.is_multi_column and req.multi_columns:
            configs = [c.dict() for c in req.multi_columns]
            results = engine.match_multi_column(df, configs, settings=settings, progress_callback=progress_cb)
            col_a_name = "Multi_A"
            col_b_name = "Multi_B"
        else:
            results = engine.match_dataframe(
                df=df,
                col_a=req.col_a,
                col_b=req.col_b,
                matching_type=req.matching_type,
                settings=settings,
                custom_weights=req.custom_weights,
                progress_callback=progress_cb,
            )
            col_a_name = req.col_a
            col_b_name = req.col_b

        # Calculate summary statistics
        strong_count = sum(1 for r in results if r.status == "Strong Match")
        likely_count = sum(1 for r in results if r.status == "Likely Match")
        possible_count = sum(1 for r in results if r.status == "Possible Match")
        weak_count = sum(1 for r in results if r.status == "Weak Match")
        no_match_count = sum(1 for r in results if r.status == "No Match")
        avg_score = round(sum(r.score for r in results) / len(results), 1) if results else 0.0

        df_results = results_to_dataframe(results, col_a_name=col_a_name, col_b_name=col_b_name)

        # Pre-save export CSV directly to disk for 0-RAM streaming download
        export_csv_path = os.path.join(EXPORT_DIR, f"{job_id}.csv")
        try:
            df_results.to_csv(export_csv_path, index=False)
        except Exception:
            pass

        stats = {
            "total": len(results),
            "strong": strong_count,
            "likely": likely_count,
            "possible": possible_count,
            "weak": weak_count,
            "no_match": no_match_count,
            "avg_score": avg_score,
        }

        JOB_CACHE[job_id] = {
            "job_id": job_id,
            "file_id": req.file_id,
            "col_a": col_a_name,
            "col_b": col_b_name,
            "results": results,
            "df_results": df_results,
            "matching_type": req.matching_type,
            "total_rows": len(results),
            "stats": stats,
            "export_csv": export_csv_path,
        }

        # Build lightweight row summaries (only ~1MB for 15,000 rows instead of 15MB+)
        lightweight_results = []
        for idx, r in enumerate(results, start=1):
            lightweight_results.append({
                "row_index": idx,
                "score": r.score,
                "status": r.status,
                "confidence": r.confidence,
                "matching_type": r.matching_type,
                "original_a": r.explanation.original_a,
                "original_b": r.explanation.original_b,
                "summary": r.explanation.summary,
            })

        if job_id in JOB_PROGRESS:
            JOB_PROGRESS[job_id]["status"] = "completed"
            JOB_PROGRESS[job_id]["percentage"] = 100.0
            JOB_PROGRESS[job_id]["processed"] = total_rows
            JOB_PROGRESS[job_id]["message"] = f"Finished matching all {total_rows:,} records!"
            JOB_PROGRESS[job_id]["stats"] = stats
            JOB_PROGRESS[job_id]["results"] = lightweight_results

        # Keep only latest 2 jobs in memory to protect 512MB RAM
        while len(JOB_CACHE) > 2:
            old_k = next(iter(JOB_CACHE))
            del JOB_CACHE[old_k]
        while len(UPLOAD_CACHE) > 2:
            old_k = next(iter(UPLOAD_CACHE))
            del UPLOAD_CACHE[old_k]
        gc.collect()

        return {
            "status": "success",
            "job_id": job_id,
            "stats": stats,
            "results": lightweight_results,
        }

    except Exception as e:
        if job_id in JOB_PROGRESS:
            JOB_PROGRESS[job_id]["status"] = "error"
            JOB_PROGRESS[job_id]["error"] = str(e)
            JOB_PROGRESS[job_id]["message"] = f"Error: {str(e)}"
        raise e


@router.post("/api/match")
async def run_match_job(req: MatchJobRequest):
    """
    Execute matching on the uploaded file synchronously.
    """
    if req.file_id not in UPLOAD_CACHE:
        raise HTTPException(status_code=404, detail="File session expired or not found. Please upload again.")

    session = UPLOAD_CACHE[req.file_id]
    df = session["df"]

    if not req.is_multi_column:
        if not req.col_a or not req.col_b:
            raise HTTPException(status_code=400, detail="col_a and col_b must be specified for single-pair matching.")
        if req.col_a not in df.columns or req.col_b not in df.columns:
            raise HTTPException(status_code=400, detail="Selected columns not found in dataset.")

    job_id = str(uuid.uuid4())
    JOB_PROGRESS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "processed": 0,
        "total": len(df),
        "percentage": 0.0,
        "message": f"Processing {len(df):,} rows...",
    }

    return execute_matching_job_worker(job_id, req, df)


@router.post("/api/match/start")
async def start_match_job(req: MatchJobRequest):
    """
    Start matching job asynchronously in background and return job_id for progress polling.
    """
    if req.file_id not in UPLOAD_CACHE:
        raise HTTPException(status_code=404, detail="File session expired or not found. Please upload again.")

    session = UPLOAD_CACHE[req.file_id]
    df = session["df"]

    if not req.is_multi_column:
        if not req.col_a or not req.col_b:
            raise HTTPException(status_code=400, detail="col_a and col_b must be specified for single-pair matching.")
        if req.col_a not in df.columns or req.col_b not in df.columns:
            raise HTTPException(status_code=400, detail="Selected columns not found in dataset.")

    job_id = str(uuid.uuid4())
    total_rows = len(df)
    JOB_PROGRESS[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "processed": 0,
        "total": total_rows,
        "percentage": 0.0,
        "message": f"Starting matching engine on {total_rows:,} rows...",
        "stats": None,
        "results": None,
        "error": None,
    }

    t = threading.Thread(target=execute_matching_job_worker, args=(job_id, req, df))
    t.daemon = True
    t.start()

    return {"status": "started", "job_id": job_id, "total": total_rows}


@router.get("/api/match/progress/{job_id}")
async def get_match_progress(job_id: str):
    """
    Poll live progress (percentage, row count, status, and results upon completion).
    """
    if job_id not in JOB_PROGRESS:
        raise HTTPException(status_code=404, detail="Matching job not found.")
    return JOB_PROGRESS[job_id]


@router.get("/api/match/explain/{job_id}/{row_index}")
async def get_match_row_explanation(job_id: str, row_index: int):
    """
    Fetch on-demand deep explainability and component breakdown for a specific row.
    """
    if job_id not in JOB_CACHE:
        raise HTTPException(status_code=404, detail="Matching session expired or not found.")
    results = JOB_CACHE[job_id]["results"]
    if row_index < 1 or row_index > len(results):
        raise HTTPException(status_code=400, detail="Row index out of range.")
    r = results[row_index - 1]
    return {
        "row_index": row_index,
        "score": r.score,
        "status": r.status,
        "confidence": r.confidence,
        "matching_type": r.matching_type,
        "explanation": r.explanation.to_dict(),
    }


@router.post("/api/quick-match")
async def quick_match(req: QuickMatchRequest):
    """
    Real-time interactive matching sandbox for any two strings.
    """
    settings = NormalizationSettings(
        mode=req.normalization_mode,
        case_sensitive=req.case_sensitive,
        remove_punctuation=req.remove_punctuation,
        normalize_whitespace=req.normalize_whitespace,
        expand_abbreviations=req.expand_abbreviations,
        normalize_numbers=req.normalize_numbers,
    )

    result = default_engine.match_pair(
        val_a=req.str_a,
        val_b=req.str_b,
        matching_type=req.matching_type,
        settings=settings,
        custom_weights=req.custom_weights,
    )

    return {
        "status": "success",
        "result": result.to_dict(),
    }


@router.get("/api/results/{job_id}")
async def get_job_results(job_id: str):
    """Retrieve existing job results."""
    if job_id not in JOB_CACHE:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOB_CACHE[job_id]
    lightweight = []
    for idx, r in enumerate(job["results"], start=1):
        lightweight.append({
            "row_index": idx,
            "score": r.score,
            "status": r.status,
            "confidence": r.confidence,
            "matching_type": r.matching_type,
            "original_a": r.explanation.original_a,
            "original_b": r.explanation.original_b,
            "summary": r.explanation.summary,
        })

    return {
        "status": "success",
        "job_id": job_id,
        "stats": job["stats"],
        "results": lightweight,
    }


@router.get("/api/export/{job_id}")
async def export_job_results(job_id: str, format: str = Query("csv", pattern="^(csv|xlsx)$")):
    """
    Export results as CSV or Excel (.xlsx). CSV is streamed directly from disk with 0 RAM usage.
    """
    csv_disk_path = os.path.join(EXPORT_DIR, f"{job_id}.csv")
    if format.lower() == "csv" and os.path.exists(csv_disk_path):
        return FileResponse(
            csv_disk_path,
            media_type="text/csv; charset=utf-8",
            filename=f"match_results_{job_id[:8]}.csv",
        )

    if job_id not in JOB_CACHE:
        raise HTTPException(status_code=404, detail="Job not found")

    job = JOB_CACHE[job_id]
    df_results = job["df_results"]

    if format.lower() == "xlsx":
        content = export_to_excel_bytes(df_results)
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"match_results_{job_id[:8]}.xlsx"
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    else:
        content = export_to_csv_bytes(df_results)
        media_type = "text/csv; charset=utf-8"
        filename = f"match_results_{job_id[:8]}.csv"
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )


@router.get("/api/dictionary")
async def get_dictionary():
    """Get active abbreviation dictionary grouped by categories."""
    return {
        "categories": {
            "company": global_abbrev_manager.categories.get("company", {}),
            "address": global_abbrev_manager.categories.get("address", {}),
            "direction": global_abbrev_manager.categories.get("direction", {}),
            "name": global_abbrev_manager.categories.get("name", {}),
            "state": global_abbrev_manager.categories.get("state", {}),
        },
        "custom_rules": global_abbrev_manager.custom_dict,
    }


@router.post("/api/dictionary/rule")
async def add_dictionary_rule(req: AddDictionaryRuleRequest):
    """Add or update a custom abbreviation rule."""
    if not req.abbreviation or not req.expansion:
        raise HTTPException(status_code=400, detail="Abbreviation and expansion cannot be empty.")
    global_abbrev_manager.add_custom_rule(req.abbreviation, req.expansion)
    return {"status": "success", "custom_rules": global_abbrev_manager.custom_dict}


@router.delete("/api/dictionary/rule/{abbr}")
async def delete_dictionary_rule(abbr: str):
    """Delete a custom abbreviation rule."""
    global_abbrev_manager.remove_custom_rule(abbr)
    return {"status": "success", "custom_rules": global_abbrev_manager.custom_dict}


@router.get("/api/weights")
async def get_default_weights():
    """Get default weight profiles for all matching types."""
    return DEFAULT_WEIGHT_PROFILES
