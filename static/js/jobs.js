/**
 * Job Vacancies Management JavaScript
 * Full CRUD operations via /api/jobs
 */

let jobsList = [];
let companiesMap = {};
let jobModalInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    jobModalInstance = new bootstrap.Modal(document.getElementById('jobModal'));

    await loadCompaniesDropdown();
    loadJobs();

    // Search and Filters
    document.getElementById('jobSearchInput').addEventListener('input', applyJobFilters);
    document.getElementById('jobStatusFilterSelect').addEventListener('change', applyJobFilters);
    document.getElementById('jobTypeFilterSelect').addEventListener('change', applyJobFilters);

    // Refresh
    document.getElementById('btnRefreshJobs').addEventListener('click', async () => {
        await loadCompaniesDropdown();
        loadJobs();
    });

    // Open Add Modal
    document.getElementById('btnOpenAddJobModal').addEventListener('click', () => {
        resetJobForm();
        document.getElementById('jobModalTitle').textContent = 'Post New Job Vacancy';
        document.getElementById('saveJobBtnText').textContent = 'Post Vacancy';
        jobModalInstance.show();
    });

    // Form submission
    document.getElementById('jobForm').addEventListener('submit', handleJobFormSubmit);
});

async function loadCompaniesDropdown() {
    try {
        const res = await fetch('/api/companies');
        const result = await res.json();
        if (result.success && result.data) {
            companiesMap = {};
            const selectEl = document.getElementById('jobCompanyInput');
            selectEl.innerHTML = '<option value="">Select Company...</option>';

            result.data.forEach(c => {
                companiesMap[c.company_id] = c;
                const opt = `<option value="${c.company_id}">${escapeHtml(c.company_name)} (${escapeHtml(c.industry)})</option>`;
                selectEl.insertAdjacentHTML('beforeend', opt);
            });
        }
    } catch (err) {
        console.error('Failed to load companies dropdown:', err);
    }
}

async function loadJobs() {
    const tbody = document.getElementById('jobsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading job openings from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/jobs');
        const result = await res.json();

        if (result.success) {
            jobsList = result.data || [];
            document.getElementById('jobRecordCount').textContent = `${jobsList.length} Vacancies`;
            applyJobFilters();
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve job postings.');
        }
    } catch (err) {
        console.error('Error fetching jobs:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function applyJobFilters() {
    const term = (document.getElementById('jobSearchInput').value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('jobStatusFilterSelect').value;
    const typeFilter = document.getElementById('jobTypeFilterSelect').value;

    let filtered = jobsList;

    if (statusFilter) {
        filtered = filtered.filter(j => j.job_status === statusFilter);
    }

    if (typeFilter) {
        filtered = filtered.filter(j => j.job_type === typeFilter);
    }

    if (term) {
        filtered = filtered.filter(j =>
            (j.job_title && j.job_title.toLowerCase().includes(term)) ||
            (j.company_name && j.company_name.toLowerCase().includes(term)) ||
            (j.job_location && j.job_location.toLowerCase().includes(term)) ||
            (j.job_type && j.job_type.toLowerCase().includes(term)) ||
            String(j.job_id).includes(term)
        );
    }

    renderJobsTable(filtered);
}

function renderJobsTable(list) {
    const tbody = document.getElementById('jobsTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-briefcase"></i></div>
                        <h6 class="empty-state-title">No Job Vacancies Found</h6>
                        <p class="empty-state-desc">Post active placement openings from corporate hiring partners.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddJobModal').click()">
                            <i class="bi bi-briefcase-fill me-1"></i> Post Vacancy
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(j => {
        const pkgStr = `${formatCurrency(j.minimum_package)} - ${formatCurrency(j.maximum_package)}`;
        
        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${j.job_id}</span></td>
                <td>
                    <div class="fw-bold text-dark">${escapeHtml(j.job_title)}</div>
                    <div class="text-primary small fw-medium"><i class="bi bi-building me-1"></i>${escapeHtml(j.company_name || '—')}</div>
                </td>
                <td>
                    <div><span class="badge bg-light text-secondary border small">${escapeHtml(j.job_type)}</span></div>
                    <div class="small text-muted mt-1"><i class="bi bi-geo-alt me-1"></i>${escapeHtml(j.job_location)}</div>
                </td>
                <td>
                    <div class="small fw-semibold text-dark">Min CGPA: ${Number(j.minimum_cgpa).toFixed(2)}</div>
                    <div class="small text-muted">Max Backlogs: ${j.maximum_backlogs}</div>
                </td>
                <td>
                    <div class="fw-semibold text-dark small">${pkgStr}</div>
                </td>
                <td>
                    <div class="small text-dark fw-medium">${j.number_of_openings} Openings</div>
                    <div class="small text-muted" style="font-size: 0.74rem;">Deadline: ${formatDate(j.application_deadline)}</div>
                </td>
                <td>
                    ${renderStatusBadge(j.job_status)}
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Edit Job" onclick="openEditJobModal(${j.job_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Job" onclick="handleDeleteJob(${j.job_id}, '${escapeHtml(j.job_title)}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function resetJobForm() {
    document.getElementById('jobForm').reset();
    document.getElementById('jobIdInput').value = '';
    document.getElementById('jobTypeInput').value = 'Full-time';
    document.getElementById('jobStatusInput').value = 'Open';
    document.getElementById('jobMinCgpaInput').value = '7.00';
    document.getElementById('jobMaxBacklogsInput').value = '0';
    document.getElementById('jobOpeningsInput').value = '5';

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('jobPostingDateInput').value = today;

    const future = new Date();
    future.setDate(future.getDate() + 45);
    document.getElementById('jobDeadlineInput').value = future.toISOString().split('T')[0];
}

function openEditJobModal(jobId) {
    const j = jobsList.find(job => job.job_id === jobId);
    if (!j) return;

    document.getElementById('jobIdInput').value = j.job_id;
    document.getElementById('jobCompanyInput').value = j.company_id;
    document.getElementById('jobTitleInput').value = j.job_title;
    document.getElementById('jobDescriptionInput').value = j.job_description;
    document.getElementById('jobTypeInput').value = j.job_type;
    document.getElementById('jobLocationInput').value = j.job_location;
    document.getElementById('jobStatusInput').value = j.job_status;
    document.getElementById('jobMinCgpaInput').value = j.minimum_cgpa;
    document.getElementById('jobMaxBacklogsInput').value = j.maximum_backlogs;
    document.getElementById('jobMinPackageInput').value = j.minimum_package;
    document.getElementById('jobMaxPackageInput').value = j.maximum_package;
    document.getElementById('jobOpeningsInput').value = j.number_of_openings;
    document.getElementById('jobPostingDateInput').value = j.posting_date;
    document.getElementById('jobDeadlineInput').value = j.application_deadline;

    document.getElementById('jobModalTitle').textContent = `Edit Vacancy: ${j.job_title}`;
    document.getElementById('saveJobBtnText').textContent = 'Update Vacancy';
    jobModalInstance.show();
}

async function handleJobFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('jobIdInput').value;
    const companyId = document.getElementById('jobCompanyInput').value;
    const title = document.getElementById('jobTitleInput').value.trim();
    const description = document.getElementById('jobDescriptionInput').value.trim();
    const type = document.getElementById('jobTypeInput').value;
    const location = document.getElementById('jobLocationInput').value.trim();
    const status = document.getElementById('jobStatusInput').value;
    const minCgpa = parseFloat(document.getElementById('jobMinCgpaInput').value);
    const maxBacklogs = parseInt(document.getElementById('jobMaxBacklogsInput').value, 10);
    const minPkg = parseFloat(document.getElementById('jobMinPackageInput').value);
    const maxPkg = parseFloat(document.getElementById('jobMaxPackageInput').value);
    const openings = parseInt(document.getElementById('jobOpeningsInput').value, 10);
    const postDate = document.getElementById('jobPostingDateInput').value;
    const deadline = document.getElementById('jobDeadlineInput').value;

    // Business validations
    if (!companyId) {
        showToast('warning', 'Validation', 'Please select a recruiting company.');
        return;
    }
    if (minPkg < 0 || maxPkg < minPkg) {
        showToast('warning', 'Validation', 'Maximum package cannot be less than minimum package.');
        return;
    }
    if (openings <= 0) {
        showToast('warning', 'Validation', 'Number of openings must be greater than zero.');
        return;
    }
    if (deadline < postDate) {
        showToast('warning', 'Validation', 'Application deadline cannot be earlier than posting date.');
        return;
    }

    const payload = {
        company_id: parseInt(companyId, 10),
        job_title: title,
        job_description: description,
        job_type: type,
        job_location: location,
        job_status: status,
        minimum_cgpa: minCgpa,
        maximum_backlogs: maxBacklogs,
        minimum_package: minPkg,
        maximum_package: maxPkg,
        number_of_openings: openings,
        posting_date: postDate,
        application_deadline: deadline
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/jobs/${id}` : '/api/jobs';
    const method = isEdit ? 'PUT' : 'POST';

    const saveBtn = document.getElementById('btnSaveJob');
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
            jobModalInstance.hide();
            showToast('success', isEdit ? 'Job Updated' : 'Job Posted', result.message || 'Saved successfully.');
            loadJobs();
        } else {
            showToast('error', 'Operation Failed', result.error || (result.details || 'Unable to save job vacancy.'));
        }
    } catch (err) {
        console.error('Error saving job:', err);
        showToast('error', 'Server Error', 'Failed to save job vacancy.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveJobBtnText">${isEdit ? 'Update Vacancy' : 'Post Vacancy'}</span>`;
    }
}

function handleDeleteJob(id, title) {
    confirmAction(
        'Delete Job Vacancy',
        `Are you sure you want to delete "${title}"? If students have submitted applications for this job, deletion will be blocked by foreign-key relational constraints.`,
        'Delete Vacancy',
        async () => {
            try {
                const res = await fetch(`/api/jobs/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Job Deleted', result.message || 'Job vacancy removed.');
                    loadJobs();
                } else {
                    showToast('error', 'Deletion Prevented', result.error || 'Foreign-key restriction: students have applied for this job.');
                }
            } catch (err) {
                console.error('Error deleting job:', err);
                showToast('error', 'Server Error', 'Could not delete job vacancy.');
            }
        }
    );
}

