/**
 * Application Management JavaScript
 * Full CRUD operations via /api/applications
 */

let applicationsList = [];
let studentsMap = {};
let jobsMap = {};
let applicationModalInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    applicationModalInstance = new bootstrap.Modal(document.getElementById('applicationModal'));

    await Promise.all([loadStudentsDropdown(), loadJobsDropdown()]);
    loadApplications();

    // Filters
    document.getElementById('applicationSearchInput').addEventListener('input', applyApplicationFilters);
    document.getElementById('applicationStatusFilterSelect').addEventListener('change', applyApplicationFilters);

    // Refresh
    document.getElementById('btnRefreshApplications').addEventListener('click', async () => {
        await Promise.all([loadStudentsDropdown(), loadJobsDropdown()]);
        loadApplications();
    });

    // Open Add Modal
    document.getElementById('btnOpenAddApplicationModal').addEventListener('click', () => {
        resetApplicationForm();
        document.getElementById('applicationModalTitle').textContent = 'Submit Job Application';
        document.getElementById('saveApplicationBtnText').textContent = 'Submit Application';
        document.getElementById('studentSelectWrapper').style.display = 'block';
        document.getElementById('jobSelectWrapper').style.display = 'block';
        applicationModalInstance.show();
    });

    // Form submit
    document.getElementById('applicationForm').addEventListener('submit', handleApplicationFormSubmit);
});

async function loadStudentsDropdown() {
    try {
        const res = await fetch('/api/students');
        const result = await res.json();
        if (result.success && result.data) {
            studentsMap = {};
            const selectEl = document.getElementById('applicationStudentInput');
            selectEl.innerHTML = '<option value="">Select Student...</option>';

            result.data.forEach(s => {
                studentsMap[s.student_id] = s;
                const opt = `<option value="${s.student_id}">${escapeHtml(s.roll_number)} - ${escapeHtml(s.student_name)} (CGPA: ${Number(s.cgpa).toFixed(2)}, Backlogs: ${s.active_backlogs})</option>`;
                selectEl.insertAdjacentHTML('beforeend', opt);
            });
        }
    } catch (err) {
        console.error('Failed to load students dropdown:', err);
    }
}

async function loadJobsDropdown() {
    try {
        const res = await fetch('/api/jobs');
        const result = await res.json();
        if (result.success && result.data) {
            jobsMap = {};
            const selectEl = document.getElementById('applicationJobInput');
            selectEl.innerHTML = '<option value="">Select Job Opening...</option>';

            result.data.forEach(j => {
                jobsMap[j.job_id] = j;
                const statusTag = j.job_status !== 'Open' ? ` [${j.job_status}]` : '';
                const opt = `<option value="${j.job_id}">${escapeHtml(j.job_title)} @ ${escapeHtml(j.company_name)}${statusTag} (Min CGPA: ${Number(j.minimum_cgpa).toFixed(2)})</option>`;
                selectEl.insertAdjacentHTML('beforeend', opt);
            });
        }
    } catch (err) {
        console.error('Failed to load jobs dropdown:', err);
    }
}

async function loadApplications() {
    const tbody = document.getElementById('applicationsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading applications from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/applications');
        const result = await res.json();

        if (result.success) {
            applicationsList = result.data || [];
            document.getElementById('applicationRecordCount').textContent = `${applicationsList.length} Applications`;
            applyApplicationFilters();
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve applications.');
        }
    } catch (err) {
        console.error('Error fetching applications:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function applyApplicationFilters() {
    const term = (document.getElementById('applicationSearchInput').value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('applicationStatusFilterSelect').value;

    let filtered = applicationsList;

    if (statusFilter) {
        filtered = filtered.filter(a => a.application_status === statusFilter);
    }

    if (term) {
        filtered = filtered.filter(a =>
            (a.student_name && a.student_name.toLowerCase().includes(term)) ||
            (a.roll_number && a.roll_number.toLowerCase().includes(term)) ||
            (a.job_title && a.job_title.toLowerCase().includes(term)) ||
            (a.company_name && a.company_name.toLowerCase().includes(term)) ||
            (a.application_status && a.application_status.toLowerCase().includes(term)) ||
            String(a.application_id).includes(term)
        );
    }

    renderApplicationsTable(filtered);
}

function renderApplicationsTable(list) {
    const tbody = document.getElementById('applicationsTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-file-earmark-text"></i></div>
                        <h6 class="empty-state-title">No Applications Found</h6>
                        <p class="empty-state-desc">Students can apply for active company job vacancies.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddApplicationModal').click()">
                            <i class="bi bi-send-plus-fill me-1"></i> Submit Application
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(app => {
        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${app.application_id}</span></td>
                <td>
                    <div class="fw-bold text-dark">${escapeHtml(app.student_name || '—')}</div>
                    <div class="text-primary small font-monospace">${escapeHtml(app.roll_number || '—')}</div>
                </td>
                <td>
                    <div class="fw-semibold text-dark">${escapeHtml(app.job_title || '—')}</div>
                    <div class="text-muted small"><i class="bi bi-building me-1"></i>${escapeHtml(app.company_name || '—')}</div>
                </td>
                <td>
                    <div class="small text-dark">CGPA: ${app.student_cgpa !== undefined ? Number(app.student_cgpa).toFixed(2) : '—'}</div>
                    <div class="small text-muted">Backlogs: ${app.student_backlogs !== undefined ? app.student_backlogs : '0'}</div>
                </td>
                <td>
                    <div class="small text-muted">${formatDateTime(app.application_date)}</div>
                </td>
                <td>
                    ${renderStatusBadge(app.application_status)}
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Update Application Status" onclick="openEditApplicationModal(${app.application_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Application" onclick="handleDeleteApplication(${app.application_id}, '${escapeHtml(app.student_name || '')}', '${escapeHtml(app.job_title || '')}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function resetApplicationForm() {
    document.getElementById('applicationForm').reset();
    document.getElementById('applicationIdInput').value = '';
    document.getElementById('applicationStatusInput').value = 'Applied';
}

function openEditApplicationModal(applicationId) {
    const app = applicationsList.find(a => a.application_id === applicationId);
    if (!app) return;

    document.getElementById('applicationIdInput').value = app.application_id;
    document.getElementById('applicationStatusInput').value = app.application_status;

    // In edit mode, student and job are fixed
    document.getElementById('studentSelectWrapper').style.display = 'none';
    document.getElementById('jobSelectWrapper').style.display = 'none';

    document.getElementById('applicationModalTitle').textContent = `Update Application #${app.application_id}: ${app.student_name} (${app.job_title})`;
    document.getElementById('saveApplicationBtnText').textContent = 'Update Status';
    applicationModalInstance.show();
}

async function handleApplicationFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('applicationIdInput').value;
    const status = document.getElementById('applicationStatusInput').value;
    const isEdit = Boolean(id);

    let url, method, payload;

    if (isEdit) {
        url = `/api/applications/${id}`;
        method = 'PUT';
        payload = { application_status: status };
    } else {
        const studentId = document.getElementById('applicationStudentInput').value;
        const jobId = document.getElementById('applicationJobInput').value;

        if (!studentId || !jobId) {
            showToast('warning', 'Validation', 'Please select both a student and a job vacancy.');
            return;
        }

        url = '/api/applications';
        method = 'POST';
        payload = {
            student_id: parseInt(studentId, 10),
            job_id: parseInt(jobId, 10),
            application_status: status
        };
    }

    const saveBtn = document.getElementById('btnSaveApplication');
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
            applicationModalInstance.hide();
            showToast('success', isEdit ? 'Status Updated' : 'Application Submitted', result.message || 'Saved successfully.');
            loadApplications();
        } else {
            showToast('error', 'Submission Rejected', result.error || (result.details || 'Eligibility check or vacancy restriction failed.'));
        }
    } catch (err) {
        console.error('Error saving application:', err);
        showToast('error', 'Server Error', 'Failed to process application.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveApplicationBtnText">${isEdit ? 'Update Status' : 'Submit Application'}</span>`;
    }
}

function handleDeleteApplication(id, studentName, jobTitle) {
    confirmAction(
        'Delete Application',
        `Are you sure you want to delete application #${id} (${studentName} for "${jobTitle}")? If interview rounds or an offer exist for this application, deletion will be blocked.`,
        'Delete Application',
        async () => {
            try {
                const res = await fetch(`/api/applications/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Application Deleted', result.message || 'Application removed.');
                    loadApplications();
                } else {
                    showToast('error', 'Deletion Prevented', result.error || 'Foreign-key restriction: interviews or offers are linked to this application.');
                }
            } catch (err) {
                console.error('Error deleting application:', err);
                showToast('error', 'Server Error', 'Could not delete application.');
            }
        }
    );
}

