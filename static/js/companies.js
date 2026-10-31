/**
 * Company Management JavaScript
 * Full CRUD operations via /api/companies supporting 1:N normalized company_contact 
 * and 1:M company_contact_phone structures.
 */

let companiesList = [];
let companyModalInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    companyModalInstance = new bootstrap.Modal(document.getElementById('companyModal'));

    loadCompanies();

    // Search filter
    document.getElementById('companySearchInput').addEventListener('input', (e) => {
        filterCompanies(e.target.value);
    });

    // Refresh button
    document.getElementById('btnRefreshCompanies').addEventListener('click', loadCompanies);

    // Add HR Contact button
    document.getElementById('btnAddCompanyContactBtn').addEventListener('click', () => {
        addCompanyContactCard();
    });

    // Open Add Modal
    document.getElementById('btnOpenAddCompanyModal').addEventListener('click', () => {
        resetCompanyForm();
        document.getElementById('companyModalTitle').textContent = 'Add Recruiting Company';
        document.getElementById('saveCompanyBtnText').textContent = 'Create Company';
        companyModalInstance.show();
    });

    // Form submission
    document.getElementById('companyForm').addEventListener('submit', handleCompanyFormSubmit);
});

async function loadCompanies() {
    const tbody = document.getElementById('companiesTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading corporate partners from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/companies');
        const result = await res.json();

        if (result.success) {
            companiesList = result.data || [];
            document.getElementById('companyRecordCount').textContent = `${companiesList.length} Companies`;
            renderCompaniesTable(companiesList);
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve companies.');
        }
    } catch (err) {
        console.error('Error fetching companies:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function renderCompaniesTable(list) {
    const tbody = document.getElementById('companiesTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-building"></i></div>
                        <h6 class="empty-state-title">No Recruiting Companies</h6>
                        <p class="empty-state-desc">Register hiring corporate partners and their HR contact details.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddCompanyModal').click()">
                            <i class="bi bi-building-add me-1"></i> Add Company
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(c => {
        const websiteLink = c.website 
            ? `<a href="${escapeHtml(c.website)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none small text-primary"><i class="bi bi-link-45deg"></i> Website</a>`
            : '<span class="text-muted small">—</span>';

        // Render contacts list
        let contactsHtml = '';
        if (c.contacts && c.contacts.length > 0) {
            contactsHtml = c.contacts.map(ct => {
                let phonesBadges = '';
                if (ct.phones && ct.phones.length > 0) {
                    phonesBadges = ct.phones.map(p => 
                        `<span class="badge bg-white text-dark border me-1 font-monospace" style="font-size:0.72rem;">
                            <i class="bi bi-telephone text-primary me-1"></i>${escapeHtml(p.phone_number)}
                            <small class="text-muted">(${escapeHtml(p.phone_type || 'Work')})</small>
                        </span>`
                    ).join(' ');
                } else if (ct.phone) {
                    phonesBadges = `<span class="badge bg-white text-dark border font-monospace" style="font-size:0.72rem;"><i class="bi bi-telephone text-primary me-1"></i>${escapeHtml(ct.phone)}</span>`;
                } else {
                    phonesBadges = '<span class="text-muted" style="font-size:0.72rem;">No phone</span>';
                }

                return `
                    <div class="p-2 mb-2 bg-light rounded border border-light-subtle">
                        <div class="d-flex align-items-center justify-content-between mb-1">
                            <span class="fw-semibold text-dark small"><i class="bi bi-person-circle text-primary me-1"></i>${escapeHtml(ct.contact_name)}</span>
                            <span class="badge bg-secondary-subtle text-secondary small" style="font-size:0.7rem;">${escapeHtml(ct.designation || 'HR')}</span>
                        </div>
                        <div class="text-muted small mb-1" style="font-size:0.75rem;"><i class="bi bi-envelope me-1"></i>${escapeHtml(ct.email)}</div>
                        <div class="d-flex flex-wrap">${phonesBadges}</div>
                    </div>
                `;
            }).join('');
        } else if (c.hr_contact_name) {
            contactsHtml = `
                <div class="p-2 bg-light rounded border">
                    <div class="fw-semibold text-dark small">${escapeHtml(c.hr_contact_name)}</div>
                    <div class="text-muted small">${escapeHtml(c.hr_email)}</div>
                    <div class="text-muted small font-monospace">${escapeHtml(c.hr_phone)}</div>
                </div>
            `;
        } else {
            contactsHtml = '<span class="text-muted small">No HR contacts listed</span>';
        }

        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${c.company_id}</span></td>
                <td>
                    <div class="fw-bold text-dark fs-6">${escapeHtml(c.company_name)}</div>
                    <div class="d-flex align-items-center gap-2 mt-1">
                        <span class="badge bg-light text-secondary border small">${escapeHtml(c.industry)}</span>
                        ${websiteLink}
                    </div>
                </td>
                <td style="min-width: 280px; max-width: 380px;">
                    ${contactsHtml}
                </td>
                <td>
                    <div class="small text-muted" title="${escapeHtml(c.company_address)}">
                        <i class="bi bi-geo-alt text-danger me-1"></i>${escapeHtml(c.company_address)}
                    </div>
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Edit Company" onclick="openEditCompanyModal(${c.company_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Company" onclick="handleDeleteCompany(${c.company_id}, '${escapeHtml(c.company_name)}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function filterCompanies(searchTerm) {
    const term = (searchTerm || '').toLowerCase().trim();
    if (!term) {
        renderCompaniesTable(companiesList);
        return;
    }

    const filtered = companiesList.filter(c => {
        const matchesBasic = (c.company_name && c.company_name.toLowerCase().includes(term)) ||
                             (c.industry && c.industry.toLowerCase().includes(term)) ||
                             (c.company_address && c.company_address.toLowerCase().includes(term)) ||
                             String(c.company_id).includes(term);

        const matchesContacts = c.contacts && c.contacts.some(ct => 
            (ct.contact_name && ct.contact_name.toLowerCase().includes(term)) ||
            (ct.email && ct.email.toLowerCase().includes(term)) ||
            (ct.designation && ct.designation.toLowerCase().includes(term)) ||
            (ct.phones && ct.phones.some(p => p.phone_number && p.phone_number.includes(term)))
        );

        return matchesBasic || matchesContacts;
    });

    renderCompaniesTable(filtered);
}

// Manage Dynamic Contact Cards and Nested Phone Rows
function addCompanyContactCard(contactData = null) {
    const container = document.getElementById('companyContactsContainer');
    const cardId = 'contact_card_' + Math.random().toString(36).substring(2, 9);

    const name = contactData ? contactData.contact_name || contactData.name || '' : '';
    const designation = contactData ? contactData.designation || 'HR Manager' : 'HR Manager';
    const email = contactData ? contactData.email || '' : '';

    const card = document.createElement('div');
    card.className = 'card border p-3 company-contact-card shadow-xs bg-white';
    card.id = cardId;

    card.innerHTML = `
        <div class="d-flex align-items-center justify-content-between mb-3 border-bottom pb-2">
            <span class="fw-bold small text-primary">
                <i class="bi bi-person-badge-fill me-1"></i> HR Contact Details
            </span>
            <button type="button" class="btn btn-xs btn-outline-danger" onclick="removeCompanyContactCard('${cardId}')" title="Remove HR Contact">
                <i class="bi bi-trash3 me-1"></i> Remove Contact
            </button>
        </div>
        <div class="row g-2 mb-2">
            <div class="col-md-4">
                <label class="form-label small mb-1">Contact Name <span class="req">*</span></label>
                <input type="text" class="form-control form-control-sm contact-name-input" placeholder="e.g. Priya Sharma" value="${escapeHtml(name)}" maxlength="100" required>
            </div>
            <div class="col-md-4">
                <label class="form-label small mb-1">Designation <span class="req">*</span></label>
                <input type="text" class="form-control form-control-sm contact-desig-input" placeholder="e.g. Campus Talent Lead" value="${escapeHtml(designation)}" maxlength="100" required>
            </div>
            <div class="col-md-4">
                <label class="form-label small mb-1">Official Email <span class="req">*</span></label>
                <input type="email" class="form-control form-control-sm contact-email-input" placeholder="hr@company.com" value="${escapeHtml(email)}" maxlength="254" required>
            </div>
        </div>

        <div class="p-2 rounded bg-light border">
            <div class="d-flex align-items-center justify-content-between mb-2">
                <span class="small fw-semibold text-secondary">
                    <i class="bi bi-telephone text-primary me-1"></i> Phone Numbers for this Contact
                </span>
                <button type="button" class="btn btn-xs btn-outline-primary rounded-pill px-2 py-0" onclick="addContactPhoneRow('${cardId}')" style="font-size:0.75rem;">
                    <i class="bi bi-plus-lg me-1"></i> Add Phone
                </button>
            </div>
            <div class="contact-phones-container d-flex flex-column gap-2" id="${cardId}_phones">
                <!-- Phone rows here -->
            </div>
        </div>
    `;

    container.appendChild(card);

    // Add phone numbers
    if (contactData && contactData.phones && contactData.phones.length > 0) {
        contactData.phones.forEach(p => {
            const num = typeof p === 'object' ? p.phone_number : p;
            const type = typeof p === 'object' ? p.phone_type : 'Work';
            addContactPhoneRow(cardId, num, type);
        });
    } else if (contactData && contactData.phone) {
        addContactPhoneRow(cardId, contactData.phone, 'Work');
    } else {
        addContactPhoneRow(cardId, '', 'Work');
    }
}

function removeCompanyContactCard(cardId) {
    const container = document.getElementById('companyContactsContainer');
    const card = document.getElementById(cardId);
    if (container.children.length <= 1) {
        showToast('warning', 'Requirement', 'At least one HR contact is required for every recruiting company.');
        return;
    }
    if (card) card.remove();
}

function addContactPhoneRow(cardId, phoneNumber = '', phoneType = 'Work') {
    const phonesContainer = document.getElementById(`${cardId}_phones`);
    if (!phonesContainer) return;

    const rowId = 'cphone_' + Math.random().toString(36).substring(2, 9);
    const row = document.createElement('div');
    row.className = 'd-flex align-items-center gap-2 contact-phone-row';
    row.id = rowId;

    row.innerHTML = `
        <div class="input-group input-group-sm flex-grow-1">
            <span class="input-group-text bg-white"><i class="bi bi-telephone"></i></span>
            <input type="text" class="form-control cphone-number-input" placeholder="e.g. +91 9876543210" value="${escapeHtml(phoneNumber)}" maxlength="20" required>
        </div>
        <select class="form-select form-select-sm cphone-type-select" style="width: 130px;">
            <option value="Work" ${phoneType === 'Work' ? 'selected' : ''}>Work</option>
            <option value="Mobile" ${phoneType === 'Mobile' ? 'selected' : ''}>Mobile</option>
            <option value="Primary" ${phoneType === 'Primary' ? 'selected' : ''}>Primary</option>
            <option value="Direct" ${phoneType === 'Direct' ? 'selected' : ''}>Direct</option>
            <option value="Alternate" ${phoneType === 'Alternate' ? 'selected' : ''}>Alternate</option>
        </select>
        <button type="button" class="btn btn-sm btn-outline-danger" title="Remove" onclick="removeContactPhoneRow('${cardId}', '${rowId}')">
            <i class="bi bi-trash3"></i>
        </button>
    `;

    phonesContainer.appendChild(row);
}

function removeContactPhoneRow(cardId, rowId) {
    const phonesContainer = document.getElementById(`${cardId}_phones`);
    const row = document.getElementById(rowId);
    if (phonesContainer && phonesContainer.children.length <= 1) {
        showToast('warning', 'Requirement', 'Each HR contact must have at least one phone number.');
        return;
    }
    if (row) row.remove();
}

function resetCompanyForm() {
    document.getElementById('companyForm').reset();
    document.getElementById('companyIdInput').value = '';

    const container = document.getElementById('companyContactsContainer');
    container.innerHTML = '';
    addCompanyContactCard();
}

function openEditCompanyModal(companyId) {
    const c = companiesList.find(comp => comp.company_id === companyId);
    if (!c) return;

    document.getElementById('companyIdInput').value = c.company_id;
    document.getElementById('companyNameInput').value = c.company_name;
    document.getElementById('companyIndustryInput').value = c.industry;
    document.getElementById('companyWebsiteInput').value = c.website || '';
    document.getElementById('companyAddressInput').value = c.company_address;

    const container = document.getElementById('companyContactsContainer');
    container.innerHTML = '';

    if (c.contacts && c.contacts.length > 0) {
        c.contacts.forEach(ct => addCompanyContactCard(ct));
    } else if (c.hr_contact_name) {
        addCompanyContactCard({
            contact_name: c.hr_contact_name,
            designation: 'HR Manager',
            email: c.hr_email,
            phone: c.hr_phone
        });
    } else {
        addCompanyContactCard();
    }

    document.getElementById('companyModalTitle').textContent = `Edit Company: ${c.company_name}`;
    document.getElementById('saveCompanyBtnText').textContent = 'Update Company';
    companyModalInstance.show();
}

async function handleCompanyFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('companyIdInput').value;
    const name = document.getElementById('companyNameInput').value.trim();
    const industry = document.getElementById('companyIndustryInput').value.trim();
    const website = document.getElementById('companyWebsiteInput').value.trim();
    const address = document.getElementById('companyAddressInput').value.trim();

    // Parse Contacts
    const contactCards = document.querySelectorAll('#companyContactsContainer .company-contact-card');
    const parsedContacts = [];
    const seenEmails = new Set();

    for (const card of contactCards) {
        const cName = card.querySelector('.contact-name-input').value.trim();
        const cDesig = card.querySelector('.contact-desig-input').value.trim();
        const cEmail = card.querySelector('.contact-email-input').value.trim().toLowerCase();

        if (!cName || !cEmail) {
            showToast('warning', 'Validation', 'Every HR contact must include both a name and a valid email.');
            return;
        }

        if (seenEmails.has(cEmail)) {
            showToast('warning', 'Duplicate Email', `HR Email "${cEmail}" is repeated across contacts for this company.`);
            return;
        }
        seenEmails.add(cEmail);

        // Parse phones for this contact
        const phoneRows = card.querySelectorAll('.contact-phone-row');
        const phones = [];
        const seenPhones = new Set();

        for (const pr of phoneRows) {
            const pNum = pr.querySelector('.cphone-number-input').value.trim();
            const pType = pr.querySelector('.cphone-type-select').value;

            if (pNum) {
                if (seenPhones.has(pNum)) {
                    showToast('warning', 'Duplicate Phone', `Phone number "${pNum}" is listed twice for contact "${cName}".`);
                    return;
                }
                seenPhones.add(pNum);
                phones.push({ phone_number: pNum, phone_type: pType });
            }
        }

        if (phones.length === 0) {
            showToast('warning', 'Validation', `Please provide at least one phone number for contact "${cName}".`);
            return;
        }

        parsedContacts.push({
            contact_name: cName,
            designation: cDesig,
            email: cEmail,
            phones: phones
        });
    }

    if (parsedContacts.length === 0) {
        showToast('warning', 'Validation', 'At least one HR contact is required.');
        return;
    }

    const payload = {
        company_name: name,
        industry: industry,
        website: website || null,
        company_address: address,
        contacts: parsedContacts
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/companies/${id}` : '/api/companies';
    const method = isEdit ? 'PUT' : 'POST';

    const saveBtn = document.getElementById('btnSaveCompany');
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
            companyModalInstance.hide();
            showToast('success', isEdit ? 'Company Updated' : 'Company Added', result.message || 'Saved successfully.');
            loadCompanies();
        } else {
            showToast('error', 'Operation Failed', result.error || (result.details || 'Unable to save company record.'));
        }
    } catch (err) {
        console.error('Error saving company:', err);
        showToast('error', 'Server Error', 'Failed to communicate with server.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveCompanyBtnText">${isEdit ? 'Update Company' : 'Save Company'}</span>`;
    }
}

function handleDeleteCompany(id, name) {
    confirmAction(
        'Delete Recruiting Company',
        `Are you sure you want to delete company "${name}"? All associated contacts and phone records will be removed. If this company has posted job openings with candidate applications, deletion will be blocked by foreign-key constraints.`,
        'Delete Company',
        async () => {
            try {
                const res = await fetch(`/api/companies/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Company Deleted', result.message || 'Company removed successfully.');
                    loadCompanies();
                } else {
                    showToast('error', 'Deletion Prevented', result.error || 'Foreign-key restriction: Company has associated job openings.');
                }
            } catch (err) {
                console.error('Error deleting company:', err);
                showToast('error', 'Server Error', 'Could not delete company.');
            }
        }
    );
}
