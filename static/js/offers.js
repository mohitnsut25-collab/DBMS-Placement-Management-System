/**
 * Placement Offers Management JavaScript
 * Full CRUD operations via /api/offers
 */

let offersList = [];
let applicationsMap = {};
let offerModalInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    offerModalInstance = new bootstrap.Modal(document.getElementById('offerModal'));

    await loadApplicationsDropdown();
    loadOffers();

    // Filters
    document.getElementById('offerSearchInput').addEventListener('input', applyOfferFilters);
    document.getElementById('offerStatusFilterSelect').addEventListener('change', applyOfferFilters);

    // Refresh
    document.getElementById('btnRefreshOffers').addEventListener('click', async () => {
        await loadApplicationsDropdown();
        loadOffers();
    });

    // Open Add Modal
    document.getElementById('btnOpenAddOfferModal').addEventListener('click', () => {
        resetOfferForm();
        document.getElementById('offerModalTitle').textContent = 'Generate Placement Offer';
        document.getElementById('saveOfferBtnText').textContent = 'Generate Offer';
        document.getElementById('offerApplicationWrapper').style.display = 'block';
        offerModalInstance.show();
    });

    // Form submit
    document.getElementById('offerForm').addEventListener('submit', handleOfferFormSubmit);
});

async function loadApplicationsDropdown() {
    try {
        const res = await fetch('/api/applications');
        const result = await res.json();
        if (result.success && result.data) {
            applicationsMap = {};
            const selectEl = document.getElementById('offerApplicationInput');
            selectEl.innerHTML = '<option value="">Select Selected Application...</option>';

            const allApps = result.data;
            const selectedApps = allApps.filter(a => a.application_status === 'Selected');

            if (selectedApps.length === 0) {
                selectEl.innerHTML = '<option value="">No applications with status "Selected" found (Set application status to "Selected" first)</option>';
            } else {
                selectedApps.forEach(a => {
                    applicationsMap[a.application_id] = a;
                    const opt = `<option value="${a.application_id}">App #${a.application_id}: ${escapeHtml(a.student_name)} (${escapeHtml(a.roll_number)}) - ${escapeHtml(a.job_title)} @ ${escapeHtml(a.company_name)}</option>`;
                    selectEl.insertAdjacentHTML('beforeend', opt);
                });
            }
        }
    } catch (err) {
        console.error('Failed to load applications dropdown:', err);
    }
}

async function loadOffers() {
    const tbody = document.getElementById('offersTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="8" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading placement offers from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/offers');
        const result = await res.json();

        if (result.success) {
            offersList = result.data || [];
            document.getElementById('offerRecordCount').textContent = `${offersList.length} Offers`;
            applyOfferFilters();
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve offers.');
        }
    } catch (err) {
        console.error('Error fetching offers:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function applyOfferFilters() {
    const term = (document.getElementById('offerSearchInput').value || '').toLowerCase().trim();
    const statusFilter = document.getElementById('offerStatusFilterSelect').value;

    let filtered = offersList;

    if (statusFilter) {
        filtered = filtered.filter(o => o.offer_status === statusFilter);
    }

    if (term) {
        filtered = filtered.filter(o =>
            (o.student_name && o.student_name.toLowerCase().includes(term)) ||
            (o.roll_number && o.roll_number.toLowerCase().includes(term)) ||
            (o.job_title && o.job_title.toLowerCase().includes(term)) ||
            (o.company_name && o.company_name.toLowerCase().includes(term)) ||
            (o.offer_status && o.offer_status.toLowerCase().includes(term)) ||
            String(o.offer_id).includes(term) ||
            String(o.application_id).includes(term)
        );
    }

    renderOffersTable(filtered);
}

function renderOffersTable(list) {
    const tbody = document.getElementById('offersTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-award"></i></div>
                        <h6 class="empty-state-title">No Placement Offers Recorded</h6>
                        <p class="empty-state-desc">Offers can be generated for applications marked as 'Selected'.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddOfferModal').click()">
                            <i class="bi bi-award-fill me-1"></i> Generate Offer
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(o => {
        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${o.offer_id}</span></td>
                <td>
                    <div class="fw-bold text-dark">${escapeHtml(o.student_name || '—')}</div>
                    <div class="text-primary small font-monospace">App #${o.application_id} (${escapeHtml(o.roll_number || '—')})</div>
                </td>
                <td>
                    <div class="fw-semibold text-dark">${escapeHtml(o.company_name || '—')}</div>
                    <div class="text-muted small">${escapeHtml(o.job_title || '—')}</div>
                </td>
                <td>
                    <span class="fw-bold text-success fs-6">${formatCurrency(o.offered_ctc)}</span>
                    <span class="text-muted small">/ annum</span>
                </td>
                <td>
                    <div class="small text-muted">${formatDate(o.offer_date)}</div>
                </td>
                <td>
                    <div class="small text-dark fw-medium">${formatDate(o.joining_date)}</div>
                </td>
                <td>
                    ${renderStatusBadge(o.offer_status)}
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Update Offer Status" onclick="openEditOfferModal(${o.offer_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Offer" onclick="handleDeleteOffer(${o.offer_id}, '${escapeHtml(o.student_name || '')}', '${escapeHtml(o.company_name || '')}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function resetOfferForm() {
    document.getElementById('offerForm').reset();
    document.getElementById('offerIdInput').value = '';
    document.getElementById('offerStatusInput').value = 'Pending';

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('offerDateInput').value = today;

    const joining = new Date();
    joining.setDate(joining.getDate() + 60);
    document.getElementById('offerJoiningDateInput').value = joining.toISOString().split('T')[0];
}

function openEditOfferModal(offerId) {
    const o = offersList.find(item => item.offer_id === offerId);
    if (!o) return;

    document.getElementById('offerIdInput').value = o.offer_id;
    document.getElementById('offerCtcInput').value = o.offered_ctc;
    document.getElementById('offerStatusInput').value = o.offer_status;
    document.getElementById('offerDateInput').value = o.offer_date;
    document.getElementById('offerJoiningDateInput').value = o.joining_date;

    // In edit mode, application is fixed
    document.getElementById('offerApplicationWrapper').style.display = 'none';

    document.getElementById('offerModalTitle').textContent = `Update Offer #${o.offer_id} for ${o.student_name}`;
    document.getElementById('saveOfferBtnText').textContent = 'Update Offer';
    offerModalInstance.show();
}

async function handleOfferFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('offerIdInput').value;
    const ctc = parseFloat(document.getElementById('offerCtcInput').value);
    const status = document.getElementById('offerStatusInput').value;
    const offerDate = document.getElementById('offerDateInput').value;
    const joiningDate = document.getElementById('offerJoiningDateInput').value;

    if (isNaN(ctc) || ctc <= 0) {
        showToast('warning', 'Validation', 'Offered CTC must be greater than zero.');
        return;
    }
    if (joiningDate < offerDate) {
        showToast('warning', 'Validation', 'Joining date cannot be earlier than offer date.');
        return;
    }

    const isEdit = Boolean(id);
    let url, method, payload;

    if (isEdit) {
        url = `/api/offers/${id}`;
        method = 'PUT';
        payload = {
            offered_ctc: ctc,
            offer_date: offerDate,
            joining_date: joiningDate,
            offer_status: status
        };
    } else {
        const appId = document.getElementById('offerApplicationInput').value;
        if (!appId) {
            showToast('warning', 'Validation', 'Please select a selected application.');
            return;
        }

        url = '/api/offers';
        method = 'POST';
        payload = {
            application_id: parseInt(appId, 10),
            offered_ctc: ctc,
            offer_date: offerDate,
            joining_date: joiningDate,
            offer_status: status
        };
    }

    const saveBtn = document.getElementById('btnSaveOffer');
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
            offerModalInstance.hide();
            showToast('success', isEdit ? 'Offer Updated' : 'Offer Issued', result.message || 'Saved successfully.');
            loadOffers();
        } else {
            showToast('error', 'Operation Failed', result.error || (result.details || 'Unable to record placement offer.'));
        }
    } catch (err) {
        console.error('Error saving offer:', err);
        showToast('error', 'Server Error', 'Failed to save offer record.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveOfferBtnText">${isEdit ? 'Update Offer' : 'Generate Offer'}</span>`;
    }
}

function handleDeleteOffer(id, studentName, companyName) {
    confirmAction(
        'Delete Placement Offer',
        `Are you sure you want to delete offer #${id} issued to "${studentName}" by "${companyName}"?`,
        'Delete Offer',
        async () => {
            try {
                const res = await fetch(`/api/offers/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Offer Deleted', result.message || 'Offer record removed.');
                    loadOffers();
                } else {
                    showToast('error', 'Deletion Failed', result.error || 'Could not delete offer record.');
                }
            } catch (err) {
                console.error('Error deleting offer:', err);
                showToast('error', 'Server Error', 'Could not delete offer record.');
            }
        }
    );
}

