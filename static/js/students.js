/**
 * Student Management JavaScript
 * Full CRUD operations via /api/students supporting 1:N normalized student_phone entries.
 */

let studentsList = [];
let departmentsMap = {};
let studentModalInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
    studentModalInstance = new bootstrap.Modal(document.getElementById('studentModal'));

    await loadDepartmentsDropdown();
    loadStudents();

    // Search & Filter
    document.getElementById('studentSearchInput').addEventListener('input', applyFilters);
    document.getElementById('departmentFilterSelect').addEventListener('change', applyFilters);

    // Refresh button
    document.getElementById('btnRefreshStudents').addEventListener('click', async () => {
        await loadDepartmentsDropdown();
        loadStudents();
    });

    // Add Phone Number Row Button
    document.getElementById('btnAddStudentPhoneRow').addEventListener('click', () => {
        addStudentPhoneRow();
    });

    // Open Add Modal
    document.getElementById('btnOpenAddStudentModal').addEventListener('click', () => {
        resetStudentForm();
        document.getElementById('studentModalTitle').textContent = 'Register New Student';
        document.getElementById('saveStudentBtnText').textContent = 'Register Student';
        studentModalInstance.show();
    });

    // Form Submit
    document.getElementById('studentForm').addEventListener('submit', handleStudentFormSubmit);
});

async function loadDepartmentsDropdown() {
    try {
        const res = await fetch('/api/departments');
        const result = await res.json();
        if (result.success && result.data) {
            const depts = result.data;
            departmentsMap = {};
            const selectForm = document.getElementById('studentDepartmentInput');
            const selectFilter = document.getElementById('departmentFilterSelect');

            selectForm.innerHTML = '<option value="">Select Department...</option>';
            selectFilter.innerHTML = '<option value="">All Departments</option>';

            depts.forEach(d => {
                departmentsMap[d.department_id] = d;
                const optForm = `<option value="${d.department_id}">${escapeHtml(d.department_code)} - ${escapeHtml(d.department_name)}</option>`;
                const optFilter = `<option value="${d.department_id}">${escapeHtml(d.department_code)}</option>`;
                selectForm.insertAdjacentHTML('beforeend', optForm);
                selectFilter.insertAdjacentHTML('beforeend', optFilter);
            });
        }
    } catch (err) {
        console.error('Failed to load departments dropdown:', err);
    }
}

async function loadStudents() {
    const tbody = document.getElementById('studentsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="7" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading students from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/students');
        const result = await res.json();

        if (result.success) {
            studentsList = result.data || [];
            document.getElementById('studentRecordCount').textContent = `${studentsList.length} Students`;
            applyFilters();
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve students.');
        }
    } catch (err) {
        console.error('Error fetching students:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function applyFilters() {
    const term = (document.getElementById('studentSearchInput').value || '').toLowerCase().trim();
    const deptFilter = document.getElementById('departmentFilterSelect').value;

    let filtered = studentsList;

    if (deptFilter) {
        filtered = filtered.filter(s => String(s.department_id) === String(deptFilter));
    }

    if (term) {
        filtered = filtered.filter(s => {
            const hasPhone = s.phone_numbers && s.phone_numbers.some(p => p.phone_number && p.phone_number.includes(term));
            return (s.student_name && s.student_name.toLowerCase().includes(term)) ||
                   (s.roll_number && s.roll_number.toLowerCase().includes(term)) ||
                   (s.email && s.email.toLowerCase().includes(term)) ||
                   hasPhone ||
                   (s.phone && s.phone.includes(term)) ||
                   (s.department_code && s.department_code.toLowerCase().includes(term));
        });
    }

    renderStudentsTable(filtered);
}

function renderStudentsTable(list) {
    const tbody = document.getElementById('studentsTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-people"></i></div>
                        <h6 class="empty-state-title">No Students Found</h6>
                        <p class="empty-state-desc">Register eligible students to begin tracking their placement journey.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddStudentModal').click()">
                            <i class="bi bi-person-plus-fill me-1"></i> Register Student
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(s => {
        const backlogBadge = s.active_backlogs > 0 
            ? `<span class="badge bg-danger-subtle text-danger border border-danger-subtle px-2 py-0">${s.active_backlogs} Backlog${s.active_backlogs > 1 ? 's' : ''}</span>`
            : `<span class="badge bg-success-subtle text-success border border-success-subtle px-2 py-0">Clean (0)</span>`;

        // Render phone pills
        let phonesHtml = '';
        if (s.phone_numbers && s.phone_numbers.length > 0) {
            phonesHtml = s.phone_numbers.map(p => 
                `<span class="badge bg-white text-dark border me-1 mb-1 font-monospace" style="font-size:0.75rem;">
                    <i class="bi bi-telephone text-primary me-1"></i>${escapeHtml(p.phone_number)}
                    <span class="text-muted fw-normal">(${escapeHtml(p.phone_type || 'Primary')})</span>
                </span>`
            ).join(' ');
        } else if (s.phone) {
            phonesHtml = `<span class="badge bg-white text-dark border font-monospace" style="font-size:0.75rem;"><i class="bi bi-telephone text-primary me-1"></i>${escapeHtml(s.phone)}</span>`;
        } else {
            phonesHtml = '<span class="text-muted small">No phone</span>';
        }

        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${s.student_id}</span></td>
                <td>
                    <div class="fw-bold text-dark">${escapeHtml(s.student_name)}</div>
                    <div class="text-primary small font-monospace" style="font-size:0.78rem;">${escapeHtml(s.roll_number)}</div>
                </td>
                <td>
                    <span class="badge bg-light text-dark border fw-medium">${escapeHtml(s.department_code || '—')}</span>
                    <div class="text-muted small" style="font-size:0.75rem;">${escapeHtml(s.department_name || '')}</div>
                </td>
                <td>
                    <div class="text-dark small mb-1"><i class="bi bi-envelope text-muted me-1"></i>${escapeHtml(s.email)}</div>
                    <div class="d-flex flex-wrap">${phonesHtml}</div>
                </td>
                <td>
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <span class="fw-bold text-dark">CGPA: ${Number(s.cgpa).toFixed(2)}</span>
                    </div>
                    <div>${backlogBadge}</div>
                </td>
                <td>
                    <span class="badge bg-secondary-subtle text-secondary">${s.batch_year}</span>
                </td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Edit Student" onclick="openEditStudentModal(${s.student_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Student" onclick="handleDeleteStudent(${s.student_id}, '${escapeHtml(s.student_name)}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// Manage dynamic repeatable phone rows
function addStudentPhoneRow(phoneNumber = '', phoneType = 'Primary') {
    const container = document.getElementById('studentPhonesContainer');
    const rowId = 'phone_row_' + Math.random().toString(36).substring(2, 9);

    const row = document.createElement('div');
    row.className = 'd-flex align-items-center gap-2 student-phone-row';
    row.id = rowId;

    row.innerHTML = `
        <div class="input-group input-group-sm flex-grow-1">
            <span class="input-group-text bg-white"><i class="bi bi-telephone text-primary"></i></span>
            <input type="text" class="form-control phone-number-input" placeholder="e.g. +91 9876543210" value="${escapeHtml(phoneNumber)}" maxlength="20" required>
        </div>
        <select class="form-select form-select-sm phone-type-select" style="width: 140px;">
            <option value="Primary" ${phoneType === 'Primary' ? 'selected' : ''}>Primary</option>
            <option value="Mobile" ${phoneType === 'Mobile' ? 'selected' : ''}>Mobile</option>
            <option value="WhatsApp" ${phoneType === 'WhatsApp' ? 'selected' : ''}>WhatsApp</option>
            <option value="Home" ${phoneType === 'Home' ? 'selected' : ''}>Home</option>
            <option value="Alternate" ${phoneType === 'Alternate' ? 'selected' : ''}>Alternate</option>
        </select>
        <button type="button" class="btn btn-sm btn-outline-danger btn-remove-phone" title="Remove" onclick="removeStudentPhoneRow('${rowId}')">
            <i class="bi bi-trash3"></i>
        </button>
    `;

    container.appendChild(row);
}

function removeStudentPhoneRow(rowId) {
    const container = document.getElementById('studentPhonesContainer');
    const row = document.getElementById(rowId);
    if (container.children.length <= 1) {
        showToast('warning', 'Requirement', 'At least one contact number is required.');
        return;
    }
    if (row) row.remove();
}

function resetStudentForm() {
    document.getElementById('studentForm').reset();
    document.getElementById('studentIdInput').value = '';
    document.getElementById('studentBatchInput').value = '2026';
    document.getElementById('studentBacklogsInput').value = '0';

    const container = document.getElementById('studentPhonesContainer');
    container.innerHTML = '';
    addStudentPhoneRow('', 'Primary');
}

function openEditStudentModal(studentId) {
    const s = studentsList.find(st => st.student_id === studentId);
    if (!s) return;

    document.getElementById('studentIdInput').value = s.student_id;
    document.getElementById('studentRollInput').value = s.roll_number;
    document.getElementById('studentNameInput').value = s.student_name;
    document.getElementById('studentEmailInput').value = s.email;
    document.getElementById('studentDepartmentInput').value = s.department_id;
    document.getElementById('studentDobInput').value = s.date_of_birth;
    document.getElementById('studentBatchInput').value = s.batch_year;
    document.getElementById('studentCgpaInput').value = s.cgpa;
    document.getElementById('studentBacklogsInput').value = s.active_backlogs;

    // Populate phone numbers
    const container = document.getElementById('studentPhonesContainer');
    container.innerHTML = '';

    if (s.phone_numbers && s.phone_numbers.length > 0) {
        s.phone_numbers.forEach(p => {
            addStudentPhoneRow(p.phone_number, p.phone_type || 'Primary');
        });
    } else if (s.phone) {
        addStudentPhoneRow(s.phone, 'Primary');
    } else {
        addStudentPhoneRow('', 'Primary');
    }

    document.getElementById('studentModalTitle').textContent = `Edit Student: ${s.student_name} (${s.roll_number})`;
    document.getElementById('saveStudentBtnText').textContent = 'Update Student';
    studentModalInstance.show();
}

async function handleStudentFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('studentIdInput').value;
    const roll = document.getElementById('studentRollInput').value.trim().toUpperCase();
    const name = document.getElementById('studentNameInput').value.trim();
    const email = document.getElementById('studentEmailInput').value.trim().toLowerCase();
    const deptId = document.getElementById('studentDepartmentInput').value;
    const dob = document.getElementById('studentDobInput').value;
    const batch = parseInt(document.getElementById('studentBatchInput').value, 10);
    const cgpa = parseFloat(document.getElementById('studentCgpaInput').value);
    const backlogs = parseInt(document.getElementById('studentBacklogsInput').value, 10);

    // Collect phones
    const phoneRows = document.querySelectorAll('#studentPhonesContainer .student-phone-row');
    const phoneNumbers = [];
    const seenPhones = new Set();

    for (const r of phoneRows) {
        const numInput = r.querySelector('.phone-number-input');
        const typeSelect = r.querySelector('.phone-type-select');
        const num = numInput ? numInput.value.trim() : '';
        const ptype = typeSelect ? typeSelect.value : 'Primary';

        if (num) {
            if (seenPhones.has(num)) {
                showToast('warning', 'Duplicate Phone', `Phone number "${num}" is listed more than once for this student.`);
                return;
            }
            seenPhones.add(num);
            phoneNumbers.push({ phone_number: num, phone_type: ptype });
        }
    }

    if (phoneNumbers.length === 0) {
        showToast('warning', 'Validation', 'Please provide at least one valid contact phone number.');
        return;
    }

    // Business validations
    if (isNaN(cgpa) || cgpa < 0.0 || cgpa > 10.0) {
        showToast('warning', 'Validation', 'Student CGPA must be between 0.00 and 10.00.');
        return;
    }
    if (isNaN(backlogs) || backlogs < 0) {
        showToast('warning', 'Validation', 'Active backlogs cannot be negative.');
        return;
    }
    if (!deptId) {
        showToast('warning', 'Validation', 'Please select an academic department.');
        return;
    }

    const payload = {
        roll_number: roll,
        student_name: name,
        email: email,
        phone_numbers: phoneNumbers,
        department_id: parseInt(deptId, 10),
        date_of_birth: dob,
        batch_year: batch,
        cgpa: cgpa,
        active_backlogs: backlogs
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/students/${id}` : '/api/students';
    const method = isEdit ? 'PUT' : 'POST';

    const saveBtn = document.getElementById('btnSaveStudent');
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
            studentModalInstance.hide();
            showToast('success', isEdit ? 'Student Updated' : 'Student Registered', result.message || 'Saved successfully.');
            loadStudents();
        } else {
            showToast('error', 'Operation Failed', result.error || (result.details || 'Unable to save student.'));
        }
    } catch (err) {
        console.error('Error saving student:', err);
        showToast('error', 'Server Error', 'Failed to save student record.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveStudentBtnText">${isEdit ? 'Update Student' : 'Register Student'}</span>`;
    }
}

function handleDeleteStudent(id, name) {
    confirmAction(
        'Delete Student Profile',
        `Are you sure you want to delete student "${name}"? If this student has active job applications, deletion will be blocked by foreign-key constraints.`,
        'Delete Student',
        async () => {
            try {
                const res = await fetch(`/api/students/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Student Deleted', result.message || 'Student record removed.');
                    loadStudents();
                } else {
                    showToast('error', 'Deletion Prevented', result.error || 'Foreign-key restriction: student has submitted applications.');
                }
            } catch (err) {
                console.error('Error deleting student:', err);
                showToast('error', 'Server Error', 'Could not delete student record.');
            }
        }
    );
}
