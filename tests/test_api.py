"""
Integration tests for FastAPI endpoints.
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_home_page():
    res = client.get("/")
    assert res.status_code == 200
    assert "Data Matching Engine" in res.text


def test_quick_match_api():
    payload = {
        "str_a": "ABC Pvt. Ltd.",
        "str_b": "abc private limited",
        "matching_type": "company",
    }
    res = client.post("/api/quick-match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    result = data["result"]
    assert result["score"] >= 95.0
    assert result["status"] == "Strong Match"
    assert "explanation" in result
    assert "matching_tokens" in result["explanation"]


def test_sample_loader_and_match_job():
    # 1. Load sample dataset
    sample_res = client.get("/api/sample/addresses")
    assert sample_res.status_code == 200
    sample_data = sample_res.json()
    file_id = sample_data["file_id"]
    col_a = sample_data["default_col_a"]
    col_b = sample_data["default_col_b"]

    assert file_id is not None
    assert col_a == "Address_A"
    assert col_b == "Address_B"
    assert sample_data["rows"] == 10

    # 2. Run matching job
    match_payload = {
        "file_id": file_id,
        "col_a": col_a,
        "col_b": col_b,
        "matching_type": "address",
    }
    match_res = client.post("/api/match", json=match_payload)
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert match_data["status"] == "success"
    job_id = match_data["job_id"]
    stats = match_data["stats"]
    assert stats["total"] == 10
    assert stats["strong"] >= 5
    assert len(match_data["results"]) == 10

    # 3. Export CSV
    export_csv_res = client.get(f"/api/export/{job_id}?format=csv")
    assert export_csv_res.status_code == 200
    assert "Original_Address_A" in export_csv_res.text
    assert "Match_Score" in export_csv_res.text

    # 4. Export XLSX
    export_xlsx_res = client.get(f"/api/export/{job_id}?format=xlsx")
    assert export_xlsx_res.status_code == 200
    assert len(export_xlsx_res.content) > 0


def test_dictionary_endpoints():
    # Fetch dictionary
    res = client.get("/api/dictionary")
    assert res.status_code == 200
    data = res.json()
    assert "categories" in data
    assert "company" in data["categories"]

    # Add custom rule
    add_res = client.post("/api/dictionary/rule", json={"abbreviation": "clg", "expansion": "college"})
    assert add_res.status_code == 200
    assert add_res.json()["custom_rules"]["clg"] == "college"

    # Delete rule
    del_res = client.delete("/api/dictionary/rule/clg")
    assert del_res.status_code == 200
    assert "clg" not in del_res.json()["custom_rules"]


def test_progress_tracking_api():
    import time
    # Load sample
    sample_res = client.get("/api/sample/addresses")
    file_id = sample_res.json()["file_id"]

    # Start matching job asynchronously
    start_payload = {
        "file_id": file_id,
        "col_a": "Address_A",
        "col_b": "Address_B",
        "matching_type": "address",
    }
    start_res = client.post("/api/match/start", json=start_payload)
    assert start_res.status_code == 200
    job_id = start_res.json()["job_id"]
    assert job_id is not None

    # Poll progress until completion
    completed = False
    for _ in range(30):
        prog_res = client.get(f"/api/match/progress/{job_id}")
        assert prog_res.status_code == 200
        prog_data = prog_res.json()
        assert "percentage" in prog_data
        assert "processed" in prog_data
        if prog_data["status"] == "completed":
            assert prog_data["percentage"] == 100.0
            assert len(prog_data["results"]) == 10
            completed = True
            break
        time.sleep(0.1)

    assert completed, "Matching job did not complete in time"


if __name__ == "__main__":
    test_home_page()
    test_quick_match_api()
    test_sample_loader_and_match_job()
    test_progress_tracking_api()
    test_dictionary_endpoints()
    print("All API integration tests passed successfully!")
