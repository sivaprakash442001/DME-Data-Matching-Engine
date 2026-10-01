# 🚀 Intelligent Data Matching Engine & Entity Resolution

An enterprise-grade, high-precision Python entity resolution and fuzzy data matching application built with **FastAPI**, **Pandas**, and an interactive modern web interface.

**Site** - https://dme-data-matching-engine.onrender.com/

Designed for robust entity matching across **Addresses**, **Person Names**, **Company Names**, **Emails**, **Phone Numbers**, **IDs / Codes**, and **Generic Text** with **modular multi-algorithm similarity scoring (0–100)** and **deep explainability ("Why did these match?")**.

---

## 🌟 Key Features

1. **Multi-Format Ingestion**:
   - Seamlessly uploads and processes **CSV**, **Excel (.xlsx, .xls)**, and **JSON** files.
   - Automatically detects row counts, columns, and previews.

2. **Smart Type Detection**:
   - Auto-detects column semantics (e.g. Email, Phone, Company, Address, Person Name, ID Code) based on content heuristics and headers.

3. **Multi-Tier Normalization Engine**:
   - **Modes**: *Standard*, *Conservative*, and *Aggressive*.
   - **Abbreviation & Alias Dictionary**: Configurable, extensible dictionary for Company suffixes (`pvt` → `private`, `ltd` → `limited`), Address components (`rd` → `road`, `st` → `street`, `ave` → `avenue`), Directions (`n` → `north`, `w` → `west`), and States (`tn` → `tamil nadu`, `ca` → `california`).
   - **Number Normalization**: Handles `#25`, `No. 25`, `Number 25`, `1st floor` vs `floor 1`, ordinal words, and unit indicators.
   - **Character & Whitespace Cleaning**: Controlled punctuation removal, accent normalization (`café` → `cafe`), and whitespace collapsing.

4. **Specialized Matching Engines**:
   - **📍 Address Engine**: Component parser extracting House/Flat numbers, Street names, Localities, Cities, States, and Postal codes. Applies strict house number discrepancy handling (`100 Main Street` vs `200 Main Street` → ~42% *Possible Match*) and geographic conflict checks.
   - **👤 Person Name Engine**: Resolves inverted name orders (`Smith, John` vs `John Smith`), middle name variations, and initials (`John A Smith` vs `John Albert Smith`).
   - **🏢 Company Name Engine**: Strips legal suffixes (`Pvt Ltd`, `LLC`, `Inc`, `Corp`) to isolate the core brand name, compares acronyms (`A.B.C.` vs `ABC`), and compares corporate types.
   - **✉️ Email Engine**: Conservative matching verifying domain identity (`@gmail.com` vs `@yahoo.com` penalty) and local-part structural variations (dots, plus-aliases).
   - **📞 Phone Engine**: Normalizes international country codes (`+91`, `+1`), leading trunk zeros (`09876543210` → `9876543210`), extensions, and formats.
   - **🔢 ID / Code Engine**: High-strictness alphanumeric matcher with prefix and number sequence alignment.
   - **🔤 Generic Text Engine**: Composite multi-algorithm engine.

5. **Modular Similarity Algorithms**:
   - **Levenshtein Distance & Ratio**
   - **Damerau-Levenshtein** (transposition-aware)
   - **Jaro & Jaro-Winkler** (prefix-boosted)
   - **Token Sort Ratio** (reordered words)
   - **Token Set Ratio** (subset/superset overlap)
   - **Jaccard Token Similarity**
   - **Partial Substring Alignment Ratio**
   - **Character N-Gram Similarity**

6. **Explainability ("Why did these match?")**:
   - Side-by-side comparison of Raw and Normalized strings.
   - Visual matching token tags cloud.
   - Component scores breakdown bar charts.
   - Confidence evaluation (*High*, *Medium*, *Low*) and human-readable narrative summary.

7. **Configurable Categorization & Thresholds**:
   - **Strong Match**: 85–100%
   - **Likely Match**: 70–84%
   - **Possible Match**: 40–69%
   - **Weak Match**: 20–39%
   - **No Match**: 0–19%

8. **Multi-Column Matching**:
   - Compare multiple column pairs simultaneously (e.g. *First Name* + *Last Name* + *City*) with custom weighted combinations.

9. **Interactive Web UI & Real-Time Sandbox**:
   - Drag & drop upload with instant sample datasets.
   - Real-time search, status filtering, and score sliders.
   - Interactive Quick-Match Sandbox to test arbitrary strings on the fly.
   - One-click export to **CSV** and **Excel (.xlsx)**.

---

## 🏗️ Architecture & Directory Structure

```
MM/
├── app/
│   ├── main.py                     # FastAPI application setup and routing
│   │
│   ├── web/
│   │   ├── routes.py               # REST API endpoints & upload handlers
│   │   ├── templates/
│   │   │   └── index.html          # Responsive HTML5 UI dashboard
│   │   └── static/
│   │       ├── css/style.css       # Clean, modern CSS styling
│   │       └── js/app.js           # Client-side state, filtering, and modals
│   │
│   ├── normalization/
│   │   ├── __init__.py
│   │   ├── cleaner.py              # TextNormalizer with modes & settings
│   │   ├── abbreviations.py        # AbbreviationManager with customizable rules
│   │   ├── numbers.py              # Number and ordinal normalization
│   │   ├── addresses.py            # Address component parser (House, Street, Locality, City, State, PIN)
│   │   └── names.py                # Person name parser (First, Middle, Last, Initials)
│   │
│   ├── matching/
│   │   ├── __init__.py
│   │   ├── algorithms.py           # Levenshtein, Jaro-Winkler, Token Sort/Set, Jaccard, N-Gram
│   │   ├── detector.py             # Column & value data type detector
│   │   ├── engine.py               # Master MatchingEngine coordinator
│   │   ├── generic.py              # Generic text matcher
│   │   ├── address.py              # Address matcher with component breakdown
│   │   ├── name.py                 # Person name matcher with inverted order handling
│   │   ├── company.py              # Company matcher with legal suffix canonicalization
│   │   ├── email.py                # Email matcher with domain verification
│   │   ├── phone.py                # Phone matcher with international prefix handling
│   │   └── id_code.py              # ID / Code matcher with alphanumeric strictness
│   │
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── weights.py              # Default and custom weight profiles
│   │   └── scorer.py               # MatchScorer, categories, and explainability generator
│   │
│   └── utils/
│       ├── __init__.py
│       ├── file_reader.py          # CSV/XLSX/XLS/JSON file reader
│       ├── exporters.py            # CSV and Excel export generators
│       └── sample_generator.py     # Built-in demo datasets generator
│
├── tests/
│   ├── test_matching.py            # Unit test suite for matching & normalization
│   └── test_api.py                 # Integration test suite for FastAPI endpoints
│
├── data/
│   ├── samples/                    # Sample CSV/Excel test datasets
│   ├── uploads/                    # Temporary uploaded files
│   └── exports/                    # Generated export files
│
├── requirements.txt
├── Dockerfile
├── run.py                          # Development launcher
└── README.md
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.12)
- pip

### 2. Installation
```bash
# Clone or navigate to the directory
cd MM

# Install dependencies
pip install -r requirements.txt
```

### 3. Running the Web Application
```bash
python run.py
```
Open your browser at: **`http://127.0.0.1:8000`**

### 4. Running Automated Tests
```bash
# Run unit test suite
python tests/test_matching.py

# Run API integration test suite
python tests/test_api.py
```

---

## 🐳 Docker Deployment

To build and run as a Docker container:
```bash
# Build image
docker build -t data-match-engine .

# Run container
docker run -p 8000:8000 data-match-engine
```
Visit `http://localhost:8000` in your browser.

---

## 📡 REST API Reference

### 1. `POST /api/upload`
Upload a CSV, Excel, or JSON file.
- **Request**: Multipart `file`
- **Response**:
```json
{
  "status": "success",
  "file_id": "993a4b6c-...",
  "filename": "customers.xlsx",
  "rows": 125430,
  "columns": ["Customer ID", "Full Name", "Company Name", "Address", "Phone", "Email"],
  "detected_types": {
    "Address": { "type": "address", "confidence": 0.95 },
    "Email": { "type": "email", "confidence": 0.98 }
  }
}
```

### 2. `POST /api/match`
Execute matching on uploaded dataset.
- **Request Body**:
```json
{
  "file_id": "993a4b6c-...",
  "col_a": "Address",
  "col_b": "Billing Address",
  "matching_type": "auto",
  "normalization_mode": "standard",
  "expand_abbreviations": true
}
```

### 3. `POST /api/quick-match`
Compare two strings directly without file upload.
- **Request Body**:
```json
{
  "str_a": "12, MG Road, Chennai",
  "str_b": "12 MG Rd Chennai",
  "matching_type": "address"
}
```
- **Response**:
```json
{
  "status": "success",
  "result": {
    "score": 96.0,
    "status": "Strong Match",
    "confidence": "High",
    "matching_type": "address",
    "explanation": {
      "original_a": "12, MG Road, Chennai",
      "original_b": "12 MG Rd Chennai",
      "normalized_a": "12 mg road chennai",
      "normalized_b": "12 mg road chennai",
      "matching_tokens": ["12", "chennai", "mg", "road"],
      "component_scores": {
        "house_number": 100.0,
        "street": 100.0,
        "locality": 100.0,
        "city_state": 100.0,
        "postal_code": 75.0,
        "token_similarity": 100.0
      },
      "summary": "City match (Chennai); House/unit match (#12)"
    }
  }
}
```

### 4. `GET /api/export/{job_id}?format=csv|xlsx`
Download the evaluated results in CSV or formatted Excel spreadsheet format.

### 5. `GET /api/dictionary` & `POST /api/dictionary/rule`
Retrieve and manage custom abbreviation rules dynamically.

---

## 📊 Verification Examples

| Column A | Column B | Match % | Result Category | Key Explainability Signal |
| :--- | :--- | :--- | :--- | :--- |
| `12, MG Road, Chennai` | `12 MG Rd Chennai` | **96%** | **Strong Match** | Normalized `rd` → `road`, matching house number `12`, matching city `Chennai` |
| `45 Anna Nagar West` | `45 Anna Nagar W` | **91%** | **Strong Match** | Normalized `w` → `west`, matching house number `45` |
| `100 Main Street` | `200 Main Street` | **42%** | **Possible Match** | Street matched, but different house numbers (`100` vs `200`) penalized |
| `Chennai, Tamil Nadu` | `Mumbai, Maharashtra` | **8%** | **No Match** | Geographic mismatch (`Chennai` != `Mumbai`, `Tamil Nadu` != `Maharashtra`) |
| `ABC Pvt. Ltd.` | `abc private limited` | **98%** | **Strong Match** | Canonicalized legal suffixes `pvt ltd` → `private limited`, identical core brand `abc` |
| `John Michael Smith` | `Smith, John M.` | **94%** | **Strong Match** | Inverted comma order detected, middle initial `M.` aligned to `Michael` |
| `John Smith` | `Smith John` | **96%** | **Strong Match** | Inverted first/last name order detected |
| `+91 98765 43210` | `09876543210` | **97%** | **Strong Match** | International code `+91` and trunk prefix `0` resolved to national number `9876543210` |
| `john.smith@gmail.com` | `John.Smith@gmail.com` | **100%** | **Strong Match** | Case-insensitive exact email match |
| `johnsmith@gmail.com` | `john.smith@gmail.com` | **88%** | **Likely Match** | Conservative scoring on dot variation in email handle |

---

## 📄 License
MIT License.
