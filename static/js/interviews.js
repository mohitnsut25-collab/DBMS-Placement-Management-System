/**
 * Interview Rounds Management JavaScript
 * Full CRUD operations via /api/interviews
 */

let interviewsList = [];
let applicationsMap = {};
let interviewModalInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    interviewModalInstance = new bootstrap.Modal(document.getElementById('interviewModal'));

    await loadApplicationsDropdown();
    loadInterviews();

    // Filters
    document.getElementById('interviewSearchInput').addEventListener('input', applyInterviewFilters);
    document.getElementById('interviewResultFilterSelect').addEventListener('change', applyInterviewFilters);
    document.getElementById('interviewModeFilterSelect').addEventListener('change', applyInterviewFilters);

    // Refresh
    document.getElementById('btnRefreshInterviews').addEventListener('click', async () => {
        await loadApplicationsDropdown();
        loadInterviews();
    });

    // Open Add Modal
    document.getElementById('btnOpenAddInterviewModal').addEventListener('click', () => {
        resetInterviewForm();
        document.getElementById('interviewModalTitle').textContent = 'Schedule Interview Round';
        document.getElementById('saveInterviewBtnText').textContent = 'Schedule Round';
        document.getElementById('applicationSelectWrapper').style.display = 'block';
        interviewModalInstance.show();
    });

    // Form submit
    document.getElementById('interviewForm').addEventListener('submit', handleInterviewFormSubmit);
});

async function loadApplicationsDropdown() {
    try {
        const res = await fetch('/api/applications');
        const result = await res.json();
        if (result.success && result.data) {
            applicationsMap = {};
            const selectEl = document.getElementById('interviewApplicationInput');
            selectEl.innerHTML = '<option value="">Select Application...</option>';

            result.data.forEach(a => {
                applicationsMap[a.application_id] = a;
                const opt = `<option value="${a.application_id}">App #${a.application_id}: ${escapeHtml(a.student_name)} (${escapeHtml(a.roll_number)}) - ${escapeHtml(a.job_title)} @ ${escapeHtml(a.company_name)}</option>`;
                selectEl.insertAdjacentHTML('beforeend', opt);
            });
        }
    } catch (err) {
        console.error('Failed to load applications dropdown:', err);
    }
}

async function loadInterviews() {
    const tbody = document.getElementById('interviewsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading interviews from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/interviews');
        const result = await res.json();

        if (result.success) {
            interviewsList = result.data || [];
            document.getElementById('interviewRecordCount').textContent = `${interviewsList.length} Interviews`;
            applyInterviewFilters();
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve interview records.');
        }
    } catch (err) {
        console.error('Error fetching interviews:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function applyInterviewFilters() {
    const term = (document.getElementById('interviewSearchInput').value || '').toLowerCase().trim();
    const resultFilter = document.getElementById('interviewResultFilterSelect').value;
    const modeFilter = document.getElementById('interviewModeFilterSelect').value;

    let filtered = interviewsList;

    if (resultFilter) {
        filtered = filtered.filter(i => i.interview_result === resultFilter);
    }

    if (modeFilter) {
        filtered = filtered.filter(i => i.interview_mode === modeFilter);
    }

    if (term) {
        filtered = filtered.filter(i =>
            (i.student_name && i.student_name.toLowerCase().includes(term)) ||
            (i.roll_number && i.roll_number.toLowerCase().includes(term)) ||
            (i.job_title && i.job_title.toLowerCase().includes(term)) ||
            (i.company_name && i.company_name.toLowerCase().includes(term)) ||
            (i.interview_mode && i.interview_mode.toLowerCase().includes(term)) ||
            (i.interview_result && i.interview_result.toLowerCase().includes(term)) ||
            String(i.interview_id).includes(term) ||
            String(i.application_id).includes(term)
        );
    }

    renderInterviewsTable(filtered);
}

function renderInterviewsTable(list) {
    const tbody = document.getElementById('interviewsTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-calendar-check"></i></div>
                        <h6 class="empty-state-title">No Interviews Scheduled</h6>
                        <p class="empty-state-desc">Schedule evaluation rounds for active student applications.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddInterviewModal').click()">
                            <i class="bi bi-calendar-plus-fill me-1"></i> Schedule Interview
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(i => {
        const feedbackPreview = i.feedback 
            ? `<div class="small text-muted text-truncate mt-1" style="max-width: 200px;" title="${escapeHtml(i.feedback)}"><i class="bi bi-chat-left-text me-1"></i>${escapeHtml(i.feedback)}</div>`
            : '';

        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${i.interview_id}</span></td>
                <td>
                    <span class="badge bg-primary-subtle text-primary border border-primary-subtle px-2 py-1">Round ${i.round_number}</span>
                </td>
                <td>
                    <div class="fw-bold text-dark">${escapeHtml(i.student_name || '—')}</div>
                    <div class="text-primary small font-monospace">App #${i.application_id} (${escapeHtml(i.roll_number || '—')})</div>
                </td>
                <td>
                    <div class="fw-semibold text-dark">${escapeHtml(i.job_title || '—')}</div>
                    <div class="text-muted small"><i class="bi bi-building me-1"></i>${escapeHtml(i.company_name || '—')}</div>
                </td>
                <td>
                    <div class="small text-dark fw-medium">${formatDateTime(i.interview_date)}</div>
                </td>
                <td>
                    <span class="badge bg-light text-secondary border">${escapeHtml(i.interview_mode)}</span>
                </td>
                <td>
                    ${renderStatusBadge(i.interview_result)}
                    ${feedbackPreview}
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Edit Interview" onclick="openEditInterviewModal(${i.interview_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Interview" onclick="handleDeleteInterview(${i.interview_id}, ${i.round_number}, '${escapeHtml(i.student_name || '')}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function resetInterviewForm() {
    document.getElementById('interviewForm').reset();
    document.getElementById('interviewIdInput').value = '';
    document.getElementById('interviewRoundInput').value = '1';
    document.getElementById('interviewModeInput').value = 'Online';
    document.getElementById('interviewResultInput').value = 'Pending';

    // Default datetime to tomorrow 10:00 AM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    const dtStr = tomorrow.toISOString().slice(0, 16);
    document.getElementById('interviewDateInput').value = dtStr;
}

function openEditInterviewModal(interviewId) {
    const i = interviewsList.find(item => item.interview_id === interviewId);
    if (!i) return;

    document.getElementById('interviewIdInput').value = i.interview_id;
    document.getElementById('interviewApplicationInput').value = i.application_id;
    document.getElementById('interviewRoundInput').value = i.round_number;
    document.getElementById('interviewModeInput').value = i.interview_mode;
    document.getElementById('interviewResultInput').value = i.interview_result;
    document.getElementById('interviewFeedbackInput').value = i.feedback || '';

    // Format datetime for datetime-local input (YYYY-MM-DDTHH:MM)
    if (i.interview_date) {
        const dt = new Date(i.interview_date);
        const yyyy = dt.getFullYear();
        const mm = String(dt.getMonth() + 1).padStart(2, '0');
        const dd = String(dt.getDate()).padStart(2, '0');
        const hh = String(dt.getHours()).padStart(2, '0');
        const min = String(dt.getMinutes()).padStart(2, '0');
        document.getElementById('interviewDateInput').value = `${yyyy}-${mm}-${dd}T${hh}:${min}`;
    }

    // In edit mode, application is fixed
    document.getElementById('applicationSelectWrapper').style.display = 'none';

    document.getElementById('interviewModalTitle').textContent = `Edit Interview Round #${i.round_number} (${i.student_name})`;
    document.getElementById('saveInterviewBtnText').textContent = 'Update Interview';
    interviewModalInstance.show();
}

async function handleInterviewFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('interviewIdInput').value;
    const roundNumber = parseInt(document.getElementById('interviewRoundInput').value, 10);
    const mode = document.getElementById('interviewModeInput').value;
    const resultVal = document.getElementById('interviewResultInput').value;
    const dtInput = document.getElementById('interviewDateInput').value;
    const feedback = document.getElementById('interviewFeedbackInput').value.trim();

    if (isNaN(roundNumber) || roundNumber <= 0) {
        showToast('warning', 'Validation', 'Round number must be greater than zero.');
        return;
    }
    if (!dtInput) {
        showToast('warning', 'Validation', 'Please provide a valid date and time.');
        return;
    }

    const isEdit = Boolean(id);
    let url, method, payload;

    if (isEdit) {
        url = `/api/interviews/${id}`;
        method = 'PUT';
        payload = {
            round_number: roundNumber,
            interview_date: dtInput.replace('T', ' ') + ':00',
            interview_mode: mode,
            interview_result: resultVal,
            feedback: feedback || null
        };
    } else {
        const appId = document.getElementById('interviewApplicationInput').value;
        if (!appId) {
            showToast('warning', 'Validation', 'Please select an application.');
            return;
        }

        url = '/api/interviews';
        method = 'POST';
        payload = {
            application_id: parseInt(appId, 10),
            round_number: roundNumber,
            interview_date: dtInput.replace('T', ' ') + ':00',
            interview_mode: mode,
            interview_result: resultVal,
            feedback: feedback || null
        };
    }

    const saveBtn = document.getElementById('btnSaveInterview');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await res.json();

        if (result.success) {
            interviewModalInstance.hide();
            showToast('success', isEdit ? 'Interview Updated' : 'Interview Scheduled', result.message || 'Saved successfully.');
            loadInterviews();
        } else {
            showToast('error', 'Operation Failed', result.error || (result.details || 'Unable to schedule interview round.'));
        }
    } catch (err) {
        console.error('Error saving interview:', err);
        showToast('error', 'Server Error', 'Failed to save interview record.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveInterviewBtnText">${isEdit ? 'Update Interview' : 'Schedule Round'}</span>`;
    }
}

function handleDeleteInterview(id, round, studentName) {
    confirmAction(
        'Delete Interview Round',
        `Are you sure you want to delete Round ${round} for "${studentName}"?`,
        'Delete Round',
        async () => {
            try {
                const res = await fetch(`/api/interviews/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Interview Deleted', result.message || 'Interview round removed.');
                    loadInterviews();
                } else {
                    showToast('error', 'Deletion Failed', result.error || 'Could not delete interview round.');
                }
            } catch (err) {
                console.error('Error deleting interview:', err);
                showToast('error', 'Server Error', 'Could not delete interview round.');
            }
        }
    );
}

