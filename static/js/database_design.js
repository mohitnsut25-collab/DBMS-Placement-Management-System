/**
 * Database Design & DBMS Analysis JavaScript
 * Manages Interactive SVG ER Diagram (pan/zoom/fit), live INFORMATION_SCHEMA metadata,
 * 3NF normalization analysis, and referential constraints.
 */

let metadataStore = {};
let normalizationStore = {};

// ER Diagram Pan & Zoom State
let currentZoom = 0.85;
let panX = 40;
let panY = 20;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

document.addEventListener('DOMContentLoaded', () => {
    loadDatabaseDesignData();

    // Refresh metadata button
    const refreshBtn = document.getElementById('btnRefreshDesignData');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.classList.add('disabled');
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Refreshing...';
            loadDatabaseDesignData().finally(() => {
                refreshBtn.classList.remove('disabled');
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-1"></i> Refresh Metadata';
                showToast('success', 'Metadata Refreshed', 'Live database schema reloaded from MySQL.');
            });
        });
    }

    // Schema search filter
    const schemaSearch = document.getElementById('schemaSearchInput');
    if (schemaSearch) {
        schemaSearch.addEventListener('input', (e) => {
            filterSchemaTables(e.target.value);
        });
    }

    // Initialize ER Canvas Pan & Zoom controls
    initErCanvasInteractions();
});

async function loadDatabaseDesignData() {
    try {
        const [metaRes, normRes] = await Promise.all([
            fetch('/api/database/metadata').then(r => r.json()),
            fetch('/api/database/normalization').then(r => r.json())
        ]);

        if (metaRes.success && metaRes.data) {
            metadataStore = metaRes.data;
            renderRelationalSchema(metadataStore);
            renderErDiagram(metadataStore);
        }

        if (normRes.success && normRes.data) {
            normalizationStore = normRes.data;
            renderNormalizationTable(normalizationStore);
        }
    } catch (err) {
        console.error('Failed to load database design data:', err);
        showToast('error', 'Metadata Load Error', 'Could not query MySQL information schema.');
    }
}

// ---------------------------------------------------------------------------
// TAB A: INTERACTIVE SVG ER DIAGRAM
// ---------------------------------------------------------------------------

const ER_ENTITIES_LAYOUT = {
    department: { x: 40, y: 40, w: 260, h: 140, title: "DEPARTMENT", type: "Strong Entity" },
    student: { x: 390, y: 40, w: 280, h: 220, title: "STUDENT", type: "Strong Entity" },
    student_phone: { x: 770, y: 40, w: 260, h: 140, title: "STUDENT_PHONE", type: "Weak Entity (1:N)" },

    company: { x: 40, y: 320, w: 260, h: 180, title: "COMPANY", type: "Strong Entity" },
    company_contact: { x: 390, y: 320, w: 280, h: 170, title: "COMPANY_CONTACT", type: "Weak Entity (1:N)" },
    company_contact_phone: { x: 770, y: 320, w: 260, h: 140, title: "COMPANY_CONTACT_PHONE", type: "Weak Entity (1:N)" },

    job: { x: 40, y: 580, w: 270, h: 270, title: "JOB", type: "Entity (1:N from Company)" },
    application: { x: 390, y: 580, w: 280, h: 180, title: "APPLICATION", type: "Bridge Entity (M:N)" },
    interview: { x: 770, y: 580, w: 260, h: 190, title: "INTERVIEW", type: "Weak Entity (1:N)" },

    offer: { x: 390, y: 840, w: 280, h: 180, title: "OFFER", type: "Dependent Entity (1:1)" }
};

const ER_RELATIONSHIPS = [
    { from: "department", to: "student", label: "Enrolls", cardFrom: "1", cardTo: "N", path: "M 300 110 L 390 110" },
    { from: "student", to: "student_phone", label: "Has_Phone", cardFrom: "1", cardTo: "N", path: "M 670 110 L 770 110" },
    { from: "company", to: "company_contact", label: "Employs_HR", cardFrom: "1", cardTo: "N", path: "M 300 400 L 390 400" },
    { from: "company_contact", to: "company_contact_phone", label: "Reaches_At", cardFrom: "1", cardTo: "N", path: "M 670 400 L 770 400" },
    { from: "company", to: "job", label: "Posts", cardFrom: "1", cardTo: "N", path: "M 170 500 L 170 580" },
    { from: "student", to: "application", label: "Submits", cardFrom: "1", cardTo: "N", path: "M 530 260 L 530 580" },
    { from: "job", to: "application", label: "Receives", cardFrom: "1", cardTo: "N", path: "M 310 670 L 390 670" },
    { from: "application", to: "interview", label: "Conducts", cardFrom: "1", cardTo: "N", path: "M 670 670 L 770 670" },
    { from: "application", to: "offer", label: "Results_In", cardFrom: "1", cardTo: "1", path: "M 530 760 L 530 840" }
];

function renderErDiagram(meta) {
    const group = document.getElementById('erViewportGroup');
    if (!group) return;

    let svgHtml = `
        <defs>
            <filter id="erShadow" x="-10%" y="-10%" width="130%" height="130%">
                <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08" />
            </filter>
            <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 9 5 L 0 9 z" fill="#475569" />
            </marker>
        </defs>
    `;

    // 1. Draw Relationship Lines
    ER_RELATIONSHIPS.forEach(rel => {
        svgHtml += `
            <g class="er-rel-group">
                <path d="${rel.path}" class="er-rel-line" marker-end="url(#arrow)" />
            </g>
        `;
    });

    // 2. Draw Entities
    for (const [tName, cfg] of Object.entries(ER_ENTITIES_LAYOUT)) {
        const tableMeta = meta[tName] || {};
        const columns = tableMeta.columns || [];
        const pkCols = tableMeta.primary_key || [];
        const fkCols = (tableMeta.foreign_keys || []).map(f => f.COLUMN_NAME);

        let attrsSvg = '';
        const visibleCols = columns.slice(0, 7); // Show primary attributes in diagram

        visibleCols.forEach((col, idx) => {
            const isPk = pkCols.includes(col.COLUMN_NAME);
            const isFk = fkCols.includes(col.COLUMN_NAME);
            const yOffset = cfg.y + 58 + (idx * 20);

            let keyBadge = '';
            if (isPk) {
                keyBadge = `<text x="${cfg.x + 12}" y="${yOffset}" class="er-key-pk" font-size="9">PK</text>`;
            } else if (isFk) {
                keyBadge = `<text x="${cfg.x + 12}" y="${yOffset}" class="er-key-fk" font-size="9">FK</text>`;
            }

            const colName = col.COLUMN_NAME;
            const colType = (col.COLUMN_TYPE || col.DATA_TYPE || '').toUpperCase();

            attrsSvg += `
                ${keyBadge}
                <text x="${cfg.x + 36}" y="${yOffset}" class="er-attr-text" font-weight="${isPk ? 'bold' : 'normal'}">
                    ${colName}
                </text>
                <text x="${cfg.x + cfg.w - 12}" y="${yOffset}" text-anchor="end" class="er-attr-type">
                    ${colType}
                </text>
            `;
        });

        if (columns.length > 7) {
            attrsSvg += `
                <text x="${cfg.x + 36}" y="${cfg.y + 58 + (7 * 20)}" class="er-attr-type" font-style="italic">
                    + ${columns.length - 7} more attributes...
                </text>
            `;
        }

        // Entity Box
        svgHtml += `
            <g class="er-entity-group" id="entity_${tName}">
                <!-- Node Rect -->
                <rect x="${cfg.x}" y="${cfg.y}" width="${cfg.w}" height="${cfg.h}" class="er-entity-node" filter="url(#erShadow)" />
                
                <!-- Node Header -->
                <path d="M ${cfg.x} ${cfg.y + 8} 
                         A 8 8 0 0 1 ${cfg.x + 8} ${cfg.y} 
                         L ${cfg.x + cfg.w - 8} ${cfg.y} 
                         A 8 8 0 0 1 ${cfg.x + cfg.w} ${cfg.y + 8} 
                         L ${cfg.x + cfg.w} ${cfg.y + 36} 
                         L ${cfg.x} ${cfg.y + 36} Z" 
                      class="er-entity-header" />
                
                <!-- Table Title -->
                <text x="${cfg.x + 14}" y="${cfg.y + 22}" class="er-header-text">
                    ${cfg.title}
                </text>
                
                <!-- Entity Type Badge -->
                <text x="${cfg.x + cfg.w - 14}" y="${cfg.y + 22}" text-anchor="end" fill="#93C5FD" font-size="9" font-family="sans-serif">
                    ${cfg.type}
                </text>

                <!-- Attributes -->
                ${attrsSvg}
            </g>
        `;
    }

    // 3. Draw Relationship Labels & Cardinalities
    ER_RELATIONSHIPS.forEach(rel => {
        // Label positions
        const parts = rel.path.match(/M\s+([0-9.]+)\s+([0-9.]+)\s+L\s+([0-9.]+)\s+([0-9.]+)/);
        if (parts) {
            const x1 = parseFloat(parts[1]);
            const y1 = parseFloat(parts[2]);
            const x2 = parseFloat(parts[3]);
            const y2 = parseFloat(parts[4]);

            const midX = (x1 + x2) / 2;
            const midY = (y1 + y2) / 2;

            svgHtml += `
                <!-- Cardinality from -->
                <text x="${x1 + (x2 > x1 ? 15 : (x2 < x1 ? -15 : 0))}" y="${y1 + (y2 > y1 ? 15 : (y2 < y1 ? -15 : -8))}" class="er-cardinality-badge">
                    ${rel.cardFrom}
                </text>
                
                <!-- Cardinality to -->
                <text x="${x2 + (x2 > x1 ? -20 : (x2 < x1 ? 20 : 0))}" y="${y2 + (y2 > y1 ? -15 : (y2 < y1 ? 15 : -8))}" class="er-cardinality-badge">
                    ${rel.cardTo}
                </text>

                <!-- Rel Diamond / Label Box -->
                <rect x="${midX - 35}" y="${midY - 10}" width="70" height="20" rx="4" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1" />
                <text x="${midX}" y="${midY + 4}" text-anchor="middle" font-size="10" font-weight="bold" fill="#334155" font-family="sans-serif">
                    ${rel.label}
                </text>
            `;
        }
    });

    group.innerHTML = svgHtml;
    updateSvgTransform();
}

function initErCanvasInteractions() {
    const svg = document.getElementById('erSvgViewport');
    if (!svg) return;

    svg.addEventListener('mousedown', (e) => {
        isPanning = true;
        startPanX = e.clientX - panX;
        startPanY = e.clientY - panY;
    });

    window.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        panX = e.clientX - startPanX;
        panY = e.clientY - startPanY;
        updateSvgTransform();
    });

    window.addEventListener('mouseup', () => {
        isPanning = false;
    });

    // Zoom buttons
    document.getElementById('btnZoomIn')?.addEventListener('click', () => {
        currentZoom = Math.min(currentZoom + 0.15, 2.5);
        updateSvgTransform();
    });

    document.getElementById('btnZoomOut')?.addEventListener('click', () => {
        currentZoom = Math.max(currentZoom - 0.15, 0.4);
        updateSvgTransform();
    });

    document.getElementById('btnResetZoom')?.addEventListener('click', () => {
        currentZoom = 0.85;
        panX = 40;
        panY = 20;
        updateSvgTransform();
    });

    document.getElementById('btnFitScreen')?.addEventListener('click', () => {
        currentZoom = 0.65;
        panX = 10;
        panY = 10;
        updateSvgTransform();
    });

    // Wheel zooming
    svg.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 0.1 : -0.1;
        currentZoom = Math.min(Math.max(currentZoom + delta, 0.4), 2.5);
        updateSvgTransform();
    }, { passive: false });
}

function updateSvgTransform() {
    const group = document.getElementById('erViewportGroup');
    if (group) {
        group.setAttribute('transform', `translate(${panX}, ${panY}) scale(${currentZoom})`);
    }
}

// ---------------------------------------------------------------------------
// TAB B: RELATIONAL SCHEMA
// ---------------------------------------------------------------------------

function renderRelationalSchema(meta) {
    const container = document.getElementById('schemaTablesContainer');
    if (!container) return;

    if (!meta || Object.keys(meta).length === 0) {
        container.innerHTML = '<div class="alert alert-warning">No relational tables found in current database.</div>';
        return;
    }

    let html = '';

    for (const [tableName, t] of Object.entries(meta)) {
        const columns = t.columns || [];
        const pks = t.primary_key || [];
        const fks = t.foreign_keys || [];
        const checks = t.check_constraints || [];

        // Build columns table
        let colsHtml = '';
        columns.forEach(col => {
            const isPk = pks.includes(col.COLUMN_NAME);
            const fkRef = fks.find(f => f.COLUMN_NAME === col.COLUMN_NAME);
            const isNullable = col.IS_NULLABLE === 'YES';

            let badges = '';
            if (isPk) badges += '<span class="badge-key badge-key-pk me-1">PRIMARY KEY</span>';
            if (fkRef) {
                badges += `<span class="badge-key badge-key-fk me-1" title="References ${fkRef.REFERENCED_TABLE_NAME}(${fkRef.REFERENCED_COLUMN_NAME})">FK &rarr; ${fkRef.REFERENCED_TABLE_NAME}</span>`;
            }
            if (col.COLUMN_KEY === 'UNI') badges += '<span class="badge-key badge-key-uk me-1">UNIQUE</span>';
            if (!isNullable && !isPk) badges += '<span class="badge-key badge-key-nn me-1">NOT NULL</span>';

            colsHtml += `
                <tr>
                    <td class="font-monospace fw-bold text-dark">${escapeHtml(col.COLUMN_NAME)}</td>
                    <td><code class="text-primary small">${escapeHtml(col.COLUMN_TYPE || col.DATA_TYPE)}</code></td>
                    <td>${badges || '<span class="text-muted small">—</span>'}</td>
                    <td class="small">${isNullable ? '<span class="text-muted">YES</span>' : '<span class="text-dark fw-medium">NO</span>'}</td>
                    <td class="small font-monospace text-muted">${col.COLUMN_DEFAULT !== null ? escapeHtml(col.COLUMN_DEFAULT) : 'NULL'}</td>
                    <td class="small text-muted font-monospace">${escapeHtml(col.EXTRA || '—')}</td>
                </tr>
            `;
        });

        // Foreign keys list
        let fksHtml = '';
        if (fks.length > 0) {
            fksHtml = fks.map(f => `
                <div class="small p-2 bg-light rounded border mb-1">
                    <i class="bi bi-arrow-return-right text-primary me-1"></i>
                    <strong>${escapeHtml(f.COLUMN_NAME)}</strong> references 
                    <code>${escapeHtml(f.REFERENCED_TABLE_NAME)}(${escapeHtml(f.REFERENCED_COLUMN_NAME)})</code>
                    <span class="ms-2 badge bg-light text-dark border">ON DELETE ${escapeHtml(f.DELETE_RULE || 'RESTRICT')}</span>
                    <span class="badge bg-light text-dark border">ON UPDATE ${escapeHtml(f.UPDATE_RULE || 'CASCADE')}</span>
                </div>
            `).join('');
        }

        // Checks list
        let checksHtml = '';
        if (checks.length > 0) {
            checksHtml = checks.map(c => `
                <div class="small p-2 bg-light rounded border mb-1">
                    <span class="badge bg-success-subtle text-success me-1">CHECK</span>
                    <code class="text-dark">${escapeHtml(c.CHECK_CLAUSE)}</code>
                </div>
            `).join('');
        }

        html += `
            <div class="content-card mb-0 schema-table-card" data-table="${escapeHtml(tableName)}">
                <div class="content-card-header d-flex align-items-center justify-content-between flex-wrap gap-2">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-primary rounded-pill px-2 py-1 font-monospace" style="font-size:0.8rem;">TABLE</span>
                        <h5 class="fw-bold text-dark mb-0 font-monospace">${escapeHtml(tableName)}</h5>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge bg-light text-dark border">Engine: InnoDB</span>
                        <span class="badge bg-light text-primary border">${t.row_count} live records</span>
                        <span class="badge bg-light text-secondary border">${columns.length} columns</span>
                    </div>
                </div>
                <div class="card-body p-3">
                    <div class="table-responsive mb-3">
                        <table class="table table-custom align-middle mb-0">
                            <thead>
                                <tr>
                                    <th>Column Name</th>
                                    <th>Type</th>
                                    <th>Key Constraints</th>
                                    <th>Nullable</th>
                                    <th>Default</th>
                                    <th>Extra</th>
                                </tr>
                            </thead>
                            <tbody>${colsHtml}</tbody>
                        </table>
                    </div>

                    ${fks.length > 0 ? `<div class="mb-2"><span class="fw-bold small text-dark"><i class="bi bi-link me-1"></i>Foreign Key Relationships:</span>${fksHtml}</div>` : ''}
                    ${checks.length > 0 ? `<div><span class="fw-bold small text-dark"><i class="bi bi-shield-check me-1"></i>Check Constraints:</span>${checksHtml}</div>` : ''}
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

function filterSchemaTables(term) {
    const q = (term || '').toLowerCase().trim();
    const cards = document.querySelectorAll('.schema-table-card');

    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (!q || text.includes(q)) {
            card.classList.remove('d-none');
        } else {
            card.classList.add('d-none');
        }
    });
}

// ---------------------------------------------------------------------------
// TAB C: NORMALIZATION TABLE
// ---------------------------------------------------------------------------

function renderNormalizationTable(norm) {
    const tbody = document.getElementById('normalizationTableBody');
    if (!tbody) return;

    const list = norm.entities_analysis || [];
    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4">No normalization records found.</td></tr>';
        return;
    }

    let html = '';
    list.forEach(item => {
        const pks = (item.primary_key || []).map(p => `<code>${escapeHtml(p)}</code>`).join(', ');
        const cks = (item.candidate_keys || []).map(ck => `(${ck.map(k => escapeHtml(k)).join(', ')})`).join(', ');
        const fds = (item.functional_dependencies || []).map(fd => `<div class="font-monospace small mb-1 text-dark">&bull; ${escapeHtml(fd)}</div>`).join('');

        html += `
            <tr>
                <td>
                    <div class="fw-bold font-monospace text-primary fs-6">${escapeHtml(item.table)}</div>
                </td>
                <td>
                    <div class="small mb-1"><strong>PK:</strong> ${pks}</div>
                    <div class="small text-muted"><strong>CKs:</strong> ${cks}</div>
                </td>
                <td style="min-width: 260px;">
                    ${fds}
                </td>
                <td>
                    <span class="badge bg-warning-subtle text-dark border border-warning-subtle px-2 py-1 fw-bold">
                        ${escapeHtml(item.normal_form || '3NF')}
                    </span>
                </td>
                <td class="small text-secondary" style="max-width: 320px; line-height: 1.45;">
                    ${escapeHtml(item.explanation || '')}
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

