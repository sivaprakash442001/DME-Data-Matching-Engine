/**
 * Data Matching Engine Client Application.
 */

// State
let currentFileId = null;
let currentJobId = null;
let currentResults = [];
let filteredResults = [];
let activeFilter = 'all';
let currentSort = { column: 'row', ascending: true };
let currentDetectedTypes = {};

// DOM Elements
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initDropzone();
    initEventListeners();
    initSandbox();
    loadDictionary();
});

// Tab navigation
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const target = btn.dataset.tab;
            document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
            document.getElementById(target).classList.remove('hidden');
        });
    });
}

// Drag and drop file handling
function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });
}

// Event Listeners for actions & filters
function initEventListeners() {
    document.getElementById('btnStartMatch').addEventListener('click', runMatching);
    document.getElementById('btnSettings').addEventListener('click', () => openModal('settingsModal'));
    document.getElementById('btnDictionary').addEventListener('click', () => openModal('dictModal'));
    document.getElementById('btnExportCsv').addEventListener('click', () => exportResults('csv'));
    document.getElementById('btnExportXlsx').addEventListener('click', () => exportResults('xlsx'));
    
    // Search input
    document.getElementById('tableSearch').addEventListener('input', (e) => {
        applyFilters();
    });

    // Score filter slider
    const scoreSlider = document.getElementById('scoreFilterSlider');
    const scoreVal = document.getElementById('scoreFilterVal');
    scoreSlider.addEventListener('input', (e) => {
        scoreVal.textContent = e.target.value;
        applyFilters();
    });

    // Filter status pills
    document.querySelectorAll('.filter-pill').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            activeFilter = pill.dataset.filter;
            applyFilters();
        });
    });

    // Multi-column toggle
    document.getElementById('multiColToggle').addEventListener('change', (e) => {
        const isMulti = e.target.checked;
        document.getElementById('singleColSection').classList.toggle('hidden', isMulti);
        document.getElementById('multiColSection').classList.toggle('hidden', !isMulti);
    });

    document.getElementById('btnAddColPair').addEventListener('click', addMultiColumnRow);

    // Modal close triggers
    document.querySelectorAll('.close-modal-trigger').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modal = e.target.closest('.modal-overlay');
            if (modal) modal.classList.remove('active');
        });
    });

    // Add dictionary rule form
    document.getElementById('formAddDictRule').addEventListener('submit', async (e) => {
        e.preventDefault();
        const abbr = document.getElementById('inputDictAbbr').value.trim();
        const exp = document.getElementById('inputDictExp').value.trim();
        if (!abbr || !exp) return;

        try {
            const res = await fetch('/api/dictionary/rule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ abbreviation: abbr, expansion: exp }),
            });
            if (res.ok) {
                document.getElementById('inputDictAbbr').value = '';
                document.getElementById('inputDictExp').value = '';
                loadDictionary();
            }
        } catch (err) {
            console.error('Failed to add rule', err);
        }
    });

    // Column change detected type hint
    document.getElementById('colSelectA').addEventListener('change', updateDetectedTypeBadge);
}

// Upload file to backend
async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const btnStart = document.getElementById('btnStartMatch');
    btnStart.disabled = true;

    try {
        showLoading(true, `Uploading & analyzing ${file.name}...`);
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
        });

        const data = await res.json();
        showLoading(false);

        if (!res.ok) {
            alert(data.detail || 'Upload failed');
            return;
        }

        populateFileMetadata(data);
    } catch (err) {
        showLoading(false);
        alert('File upload failed: ' + err.message);
    }
}

// Load built-in sample dataset
async function loadSample(sampleName) {
    try {
        showLoading(true, `Loading sample dataset (${sampleName})...`);
        const res = await fetch(`/api/sample/${sampleName}`);
        const data = await res.json();
        showLoading(false);

        if (!res.ok) {
            alert('Failed to load sample dataset');
            return;
        }

        populateFileMetadata(data);

        // Auto-select columns and type for convenience
        if (data.default_col_a) document.getElementById('colSelectA').value = data.default_col_a;
        if (data.default_col_b) document.getElementById('colSelectB').value = data.default_col_b;
        if (data.suggested_type) document.getElementById('matchingTypeSelect').value = data.suggested_type;

        updateDetectedTypeBadge();
    } catch (err) {
        showLoading(false);
        alert('Error loading sample: ' + err.message);
    }
}

// Populate file details and column dropdowns
function populateFileMetadata(data) {
    currentFileId = data.file_id;
    currentDetectedTypes = data.detected_types || {};

    document.getElementById('fileBadge').classList.remove('hidden');
    document.getElementById('fileNameText').textContent = data.filename;
    document.getElementById('fileRowsCount').textContent = `${data.rows.toLocaleString()} rows`;
    document.getElementById('fileColsCount').textContent = `${data.columns.length} columns`;

    const colA = document.getElementById('colSelectA');
    const colB = document.getElementById('colSelectB');

    colA.innerHTML = '<option value="">-- Select Column 1 --</option>';
    colB.innerHTML = '<option value="">-- Select Column 2 --</option>';

    data.columns.forEach((col, idx) => {
        const typeInfo = currentDetectedTypes[col] || { type: 'generic_text' };
        const optA = document.createElement('option');
        optA.value = col;
        optA.textContent = `${col} (${typeInfo.type})`;
        colA.appendChild(optA);

        const optB = document.createElement('option');
        optB.value = col;
        optB.textContent = `${col} (${typeInfo.type})`;
        colB.appendChild(optB);
    });

    // Heuristic default selection
    if (data.columns.length >= 2) {
        colA.selectedIndex = 1;
        colB.selectedIndex = 2;
    }

    document.getElementById('btnStartMatch').disabled = false;
    document.getElementById('configCard').classList.remove('hidden');
    updateDetectedTypeBadge();
}

function updateDetectedTypeBadge() {
    const colA = document.getElementById('colSelectA').value;
    const badge = document.getElementById('colTypeBadge');
    if (colA && currentDetectedTypes[colA]) {
        const info = currentDetectedTypes[colA];
        badge.textContent = `Auto-Detected: ${info.type} (${Math.round(info.confidence * 100)}%)`;
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

// Run Match Job
async function runMatching() {
    if (!currentFileId) {
        alert('Please upload a file or load a sample dataset first.');
        return;
    }

    const isMulti = document.getElementById('multiColToggle').checked;
    const matchingType = document.getElementById('matchingTypeSelect').value;
    const normMode = document.getElementById('normModeSelect').value;

    const payload = {
        file_id: currentFileId,
        matching_type: matchingType,
        normalization_mode: normMode,
        case_sensitive: document.getElementById('normCaseSensitive').checked,
        remove_punctuation: document.getElementById('normRemovePunct').checked,
        normalize_whitespace: document.getElementById('normWhitespace').checked,
        expand_abbreviations: document.getElementById('normExpandAbbr').checked,
        normalize_numbers: document.getElementById('normNumbers').checked,
        is_multi_column: isMulti,
    };

    if (isMulti) {
        const pairs = [];
        document.querySelectorAll('.multi-col-row').forEach(row => {
            const ca = row.querySelector('.multi-col-a').value;
            const cb = row.querySelector('.multi-col-b').value;
            const mt = row.querySelector('.multi-col-type').value;
            const wt = parseFloat(row.querySelector('.multi-col-weight').value || 1);
            if (ca && cb) {
                pairs.push({ col_a: ca, col_b: cb, type: mt, weight: wt });
            }
        });
        if (pairs.length === 0) {
            alert('Please configure at least one column pair for multi-column matching.');
            return;
        }
        payload.multi_columns = pairs;
    } else {
        const colA = document.getElementById('colSelectA').value;
        const colB = document.getElementById('colSelectB').value;
        if (!colA || !colB) {
            alert('Please select both Column 1 and Column 2.');
            return;
        }
        payload.col_a = colA;
        payload.col_b = colB;
    }

    const statusCard = document.getElementById('processStatusCard');
    const progressBar = document.getElementById('processProgressBar');
    const pctBadge = document.getElementById('processPercentageBadge');
    const rowsMsg = document.getElementById('processRowsMessage');
    const processTitle = document.getElementById('processTitle');
    const spinner = document.getElementById('processSpinner');

    // Show Progress Card
    statusCard.classList.remove('hidden');
    progressBar.style.width = '0%';
    progressBar.style.background = 'linear-gradient(90deg, #4f46e5, #06b6d4)';
    pctBadge.textContent = '0%';
    processTitle.textContent = 'Starting Matching Engine...';
    rowsMsg.innerHTML = '<i class="fa-solid fa-list-check"></i> Initializing workers & normalizing data...';
    if (spinner) spinner.style.display = 'inline-block';

    setProcessing(true);

    try {
        const startRes = await fetch('/api/match/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const startData = await startRes.json();
        if (!startRes.ok) {
            setProcessing(false);
            statusCard.classList.add('hidden');
            alert(startData.detail || 'Failed to start matching job.');
            return;
        }

        const jobId = startData.job_id;
        const totalRows = startData.total || 0;

        // Poll progress every 200ms
        const pollInterval = setInterval(async () => {
            try {
                const progRes = await fetch(`/api/match/progress/${jobId}`);
                if (!progRes.ok) return;

                const prog = await progRes.json();
                const pct = prog.percentage || 0;
                const processed = prog.processed || 0;
                const total = prog.total || totalRows;

                progressBar.style.width = `${Math.min(pct, 100)}%`;
                pctBadge.textContent = `${Math.round(pct)}%`;
                rowsMsg.innerHTML = `<i class="fa-solid fa-list-check"></i> Rows processed: <strong>${processed.toLocaleString()}</strong> / <strong>${total.toLocaleString()}</strong> (${Math.round(pct)}%)`;

                if (prog.status === 'processing') {
                    processTitle.textContent = `Processing records... (${Math.round(pct)}%)`;
                } else if (prog.status === 'completed') {
                    clearInterval(pollInterval);
                    setProcessing(false);

                    progressBar.style.width = '100%';
                    progressBar.style.background = 'linear-gradient(90deg, #10b981, #059669)';
                    pctBadge.textContent = '100%';
                    pctBadge.style.color = '#10b981';
                    processTitle.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Matching Complete!`;
                    rowsMsg.innerHTML = `<i class="fa-solid fa-circle-check" style="color: #10b981;"></i> Successfully matched <strong>${total.toLocaleString()}</strong> rows.`;

                    currentJobId = jobId;
                    currentResults = prog.results || [];
                    displayResults({ stats: prog.stats, results: prog.results });

                    // Smooth scroll down to results
                    setTimeout(() => {
                        document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 400);

                } else if (prog.status === 'error') {
                    clearInterval(pollInterval);
                    setProcessing(false);
                    processTitle.textContent = 'Error during matching!';
                    alert('Matching error: ' + (prog.error || 'Unknown error'));
                }
            } catch (pollErr) {
                console.error('Polling error', pollErr);
            }
        }, 200);

    } catch (err) {
        setProcessing(false);
        statusCard.classList.add('hidden');
        alert('Matching error: ' + err.message);
    }
}

// Render Results & Statistics
function displayResults(data) {
    document.getElementById('resultsSection').classList.remove('hidden');

    // Update Stats
    const stats = data.stats;
    document.getElementById('statTotalRows').textContent = stats.total.toLocaleString();
    document.getElementById('statStrong').textContent = stats.strong.toLocaleString();
    document.getElementById('statLikely').textContent = stats.likely.toLocaleString();
    document.getElementById('statPossible').textContent = stats.possible.toLocaleString();
    document.getElementById('statWeak').textContent = stats.weak.toLocaleString();
    document.getElementById('statNoMatch').textContent = stats.no_match.toLocaleString();
    document.getElementById('statAvgScore').textContent = `${stats.avg_score}%`;

    // Reset filters
    activeFilter = 'all';
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    document.querySelector('.filter-pill[data-filter="all"]').classList.add('active');
    document.getElementById('scoreFilterSlider').value = 0;
    document.getElementById('scoreFilterVal').textContent = '0';
    document.getElementById('tableSearch').value = '';

    applyFilters();
}

// Filter and search results in table
function applyFilters() {
    const query = document.getElementById('tableSearch').value.toLowerCase().trim();
    const minScore = parseFloat(document.getElementById('scoreFilterSlider').value) || 0;

    filteredResults = currentResults.filter(r => {
        // Status filter
        if (activeFilter === 'strong' && r.status !== 'Strong Match') return false;
        if (activeFilter === 'likely' && r.status !== 'Likely Match') return false;
        if (activeFilter === 'possible' && r.status !== 'Possible Match') return false;
        if (activeFilter === 'weak' && r.status !== 'Weak Match') return false;
        if (activeFilter === 'no_match' && r.status !== 'No Match') return false;

        // Score filter
        if (r.score < minScore) return false;

        // Text query
        if (query) {
            const exp = r.explanation;
            const strA = (exp.original_a || '').toLowerCase();
            const strB = (exp.original_b || '').toLowerCase();
            const summary = (exp.summary || '').toLowerCase();
            if (!strA.includes(query) && !strB.includes(query) && !summary.includes(query)) {
                return false;
            }
        }
        return true;
    });

    // Apply current sort
    if (currentSort && currentSort.column) {
        const dir = currentSort.ascending ? 1 : -1;
        filteredResults.sort((a, b) => {
            if (currentSort.column === 'row') return (a.row_index - b.row_index) * dir;
            if (currentSort.column === 'score') return (a.score - b.score) * dir;
            if (currentSort.column === 'val_a') return (a.explanation.original_a || '').localeCompare(b.explanation.original_a || '') * dir;
            if (currentSort.column === 'val_b') return (a.explanation.original_b || '').localeCompare(b.explanation.original_b || '') * dir;
            if (currentSort.column === 'status') return (a.status || '').localeCompare(b.status || '') * dir;
            return 0;
        });
    }

    renderTable();
}

// Column header sorting
window.sortTable = function(column) {
    if (currentSort.column === column) {
        currentSort.ascending = !currentSort.ascending;
    } else {
        currentSort.column = column;
        currentSort.ascending = column === 'score' ? false : true;
    }

    // Update icons
    const iconMap = {
        'row': 'sortIconRow',
        'val_a': 'sortIconValA',
        'val_b': 'sortIconValB',
        'score': 'sortIconScore',
        'status': 'sortIconStatus',
    };
    for (const [col, id] of Object.entries(iconMap)) {
        const icon = document.getElementById(id);
        if (!icon) continue;
        if (col === column) {
            icon.className = currentSort.ascending ? 'fa-solid fa-sort-up' : 'fa-solid fa-sort-down';
        } else {
            icon.className = 'fa-solid fa-sort';
        }
    }

    applyFilters();
};

// Render Results Table Rows
function renderTable() {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';

    document.getElementById('showingCountText').textContent = `Showing ${filteredResults.length} of ${currentResults.length} records`;

    if (filteredResults.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: #94a3b8;">No matching records found.</td></tr>`;
        return;
    }

    filteredResults.forEach(r => {
        const tr = document.createElement('tr');
        const exp = r.explanation;

        // Color badge determination
        let badgeClass = 'badge-none';
        let barColor = '#ef4444';
        if (r.status === 'Strong Match') {
            badgeClass = 'badge-strong';
            barColor = '#10b981';
        } else if (r.status === 'Likely Match') {
            badgeClass = 'badge-likely';
            barColor = '#06b6d4';
        } else if (r.status === 'Possible Match') {
            badgeClass = 'badge-possible';
            barColor = '#f59e0b';
        } else if (r.status === 'Weak Match') {
            badgeClass = 'badge-weak';
            barColor = '#f97316';
        }

        tr.innerHTML = `
            <td><strong>#${r.row_index}</strong></td>
            <td><div style="font-weight: 500;">${escapeHtml(exp.original_a)}</div></td>
            <td><div style="font-weight: 500;">${escapeHtml(exp.original_b)}</div></td>
            <td>
                <div class="score-cell">
                    <span class="score-number">${r.score}%</span>
                    <div class="score-bar-bg">
                        <div class="score-bar-fill" style="width: ${r.score}%; background: ${barColor};"></div>
                    </div>
                </div>
            </td>
            <td><span class="badge ${badgeClass}">${r.status}</span></td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="showExplanation(${r.row_index})">
                    Explain Match
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Open Explainability Modal for selected row
window.showExplanation = function(rowIndex) {
    const record = currentResults.find(r => r.row_index === rowIndex);
    if (!record) return;

    const exp = record.explanation;

    document.getElementById('modalOriginalA').textContent = exp.original_a || '(empty)';
    document.getElementById('modalOriginalB').textContent = exp.original_b || '(empty)';
    document.getElementById('modalNormA').textContent = exp.normalized_a || '(empty)';
    document.getElementById('modalNormB').textContent = exp.normalized_b || '(empty)';

    document.getElementById('modalScoreDisplay').textContent = `${record.score}%`;
    document.getElementById('modalStatusDisplay').textContent = record.status;
    document.getElementById('modalConfidenceDisplay').textContent = `Confidence: ${record.confidence}`;
    document.getElementById('modalSummaryText').textContent = exp.summary || 'Entity matching evaluated successfully.';

    // Shared Tokens
    const tokenContainer = document.getElementById('modalMatchingTokens');
    tokenContainer.innerHTML = '';
    if (exp.matching_tokens && exp.matching_tokens.length > 0) {
        exp.matching_tokens.forEach(tok => {
            const span = document.createElement('span');
            span.className = 'token-pill token-match';
            span.textContent = tok;
            tokenContainer.appendChild(span);
        });
    } else {
        tokenContainer.innerHTML = '<span style="color: #94a3b8; font-size: 0.8rem;">No identical tokens</span>';
    }

    // Component Scores Breakdown Bars
    const compContainer = document.getElementById('modalComponentsList');
    compContainer.innerHTML = '';
    for (const [key, val] of Object.entries(exp.component_scores || {})) {
        const weight = exp.applied_weights[key] ? ` (${exp.applied_weights[key]}% wt)` : '';
        const row = document.createElement('div');
        row.className = 'metric-row';
        row.innerHTML = `
            <span style="font-weight: 500; text-transform: capitalize;">${key.replace(/_/g, ' ')}${weight}</span>
            <div class="metric-bar-bg">
                <div class="metric-bar-fill" style="width: ${Math.min(val, 100)}%;"></div>
            </div>
            <span style="font-weight: 600; min-width: 40px; text-align: right;">${val}%</span>
        `;
        compContainer.appendChild(row);
    }

    openModal('explainModal');
};

// Export Handler
function exportResults(format) {
    if (!currentJobId) {
        alert('Please run a matching task first.');
        return;
    }
    window.location.href = `/api/export/${currentJobId}?format=${format}`;
}

// Multi-Column Row addition
function addMultiColumnRow() {
    const container = document.getElementById('multiColRowsContainer');
    const cols = Object.keys(currentDetectedTypes);

    const row = document.createElement('div');
    row.className = 'multi-col-row';
    row.style = 'display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem;';

    let optA = cols.map(c => `<option value="${c}">${c}</option>`).join('');
    let optB = cols.map(c => `<option value="${c}">${c}</option>`).join('');

    row.innerHTML = `
        <select class="form-select multi-col-a" style="flex: 2;">${optA}</select>
        <span>↔</span>
        <select class="form-select multi-col-b" style="flex: 2;">${optB}</select>
        <select class="form-select multi-col-type" style="flex: 1.5;">
            <option value="auto">Auto Detect</option>
            <option value="generic_text">Generic Text</option>
            <option value="address">Address</option>
            <option value="person_name">Person Name</option>
            <option value="company">Company</option>
            <option value="email">Email</option>
            <option value="phone">Phone</option>
        </select>
        <input type="number" class="form-input multi-col-weight" value="1.0" step="0.1" min="0.1" style="width: 70px;" placeholder="Wt" />
        <button type="button" class="btn btn-secondary btn-sm" onclick="this.parentElement.remove()">✕</button>
    `;
    container.appendChild(row);
}

// Sandbox (Quick Match) Logic
function initSandbox() {
    const btnCalculate = document.getElementById('btnQuickCalculate');
    btnCalculate.addEventListener('click', async () => {
        const strA = document.getElementById('quickInputA').value.trim();
        const strB = document.getElementById('quickInputB').value.trim();
        const matchType = document.getElementById('quickMatchType').value;

        if (!strA || !strB) {
            alert('Please enter both String A and String B to compare.');
            return;
        }

        try {
            btnCalculate.disabled = true;
            btnCalculate.innerHTML = '<span class="spinner"></span> Comparing...';

            const res = await fetch('/api/quick-match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    str_a: strA,
                    str_b: strB,
                    matching_type: matchType,
                }),
            });

            const data = await res.json();
            btnCalculate.disabled = false;
            btnCalculate.innerHTML = 'Compare Strings';

            if (res.ok) {
                renderSandboxResult(data.result);
            }
        } catch (err) {
            btnCalculate.disabled = false;
            btnCalculate.innerHTML = 'Compare Strings';
            alert('Error running quick match: ' + err.message);
        }
    });
}

function renderSandboxResult(result) {
    document.getElementById('quickResultBox').classList.remove('hidden');
    document.getElementById('quickScore').textContent = `${result.score}%`;
    document.getElementById('quickStatus').textContent = result.status;
    document.getElementById('quickConfidence').textContent = `Confidence: ${result.confidence} (${result.matching_type})`;
    document.getElementById('quickSummary').textContent = result.explanation.summary;

    const list = document.getElementById('quickComponents');
    list.innerHTML = '';
    for (const [k, v] of Object.entries(result.explanation.component_scores || {})) {
        const div = document.createElement('div');
        div.className = 'metric-row';
        div.innerHTML = `
            <span style="font-weight: 500; text-transform: capitalize;">${k.replace(/_/g, ' ')}</span>
            <div class="metric-bar-bg"><div class="metric-bar-fill" style="width: ${Math.min(v, 100)}%;"></div></div>
            <span style="font-weight: 600;">${v}%</span>
        `;
        list.appendChild(div);
    }
}

// Load Abbreviation Dictionary
async function loadDictionary() {
    try {
        const res = await fetch('/api/dictionary');
        if (!res.ok) return;
        const data = await res.json();

        const customTable = document.getElementById('customDictTableBody');
        customTable.innerHTML = '';

        const customRules = data.custom_rules || {};
        if (Object.keys(customRules).length === 0) {
            customTable.innerHTML = '<tr><td colspan="3" style="text-align: center; color: #94a3b8;">No custom rules defined yet.</td></tr>';
        } else {
            for (const [abbr, exp] of Object.entries(customRules)) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${escapeHtml(abbr)}</strong></td>
                    <td>${escapeHtml(exp)}</td>
                    <td><button class="btn btn-secondary btn-sm" onclick="deleteDictRule('${escapeHtml(abbr)}')">Delete</button></td>
                `;
                customTable.appendChild(tr);
            }
        }
    } catch (err) {
        console.error('Failed to load dictionary', err);
    }
}

window.deleteDictRule = async function(abbr) {
    try {
        const res = await fetch(`/api/dictionary/rule/${encodeURIComponent(abbr)}`, { method: 'DELETE' });
        if (res.ok) loadDictionary();
    } catch (err) {
        console.error('Failed to delete rule', err);
    }
};

// Modals
window.openModal = function(id) {
    document.getElementById(id).classList.add('active');
};

function showLoading(show, msg = 'Processing...') {
    const overlay = document.getElementById('loadingOverlay');
    document.getElementById('loadingMessage').textContent = msg;
    overlay.classList.toggle('active', show);
}

function setProcessing(isProcessing) {
    const btn = document.getElementById('btnStartMatch');
    if (isProcessing) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Processing Matching Engine...';
    } else {
        btn.disabled = false;
        btn.innerHTML = '⚡ Start Matching';
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
    }[tag] || tag));
}
