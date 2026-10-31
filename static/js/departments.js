/**
 * Department Management JavaScript
 * Full CRUD operations via /api/departments
 */

let departmentsList = [];
let departmentModalInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    departmentModalInstance = new bootstrap.Modal(document.getElementById('departmentModal'));

    loadDepartments();

    // Search filter
    document.getElementById('departmentSearchInput').addEventListener('input', (e) => {
        filterDepartments(e.target.value);
    });

    // Refresh button
    document.getElementById('btnRefreshDepartments').addEventListener('click', loadDepartments);

    // Open Add Modal
    document.getElementById('btnOpenAddDepartmentModal').addEventListener('click', () => {
        resetDepartmentForm();
        document.getElementById('departmentModalTitle').textContent = 'Add New Department';
        document.getElementById('saveDepartmentBtnText').textContent = 'Create Department';
        departmentModalInstance.show();
    });

    // Form submission
    document.getElementById('departmentForm').addEventListener('submit', handleDepartmentFormSubmit);
});

async function loadDepartments() {
    const tbody = document.getElementById('departmentsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="4" class="text-center py-4 text-muted">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                Loading departments from MySQL...
            </td>
        </tr>
    `;

    try {
        const res = await fetch('/api/departments');
        const result = await res.json();

        if (result.success) {
            departmentsList = result.data || [];
            document.getElementById('departmentRecordCount').textContent = `${departmentsList.length} Departments`;
            renderDepartmentsTable(departmentsList);
        } else {
            showToast('error', 'Failed to Load', result.error || 'Could not retrieve departments.');
        }
    } catch (err) {
        console.error('Error fetching departments:', err);
        showToast('error', 'Network Error', 'Failed to connect to backend server.');
    }
}

function renderDepartmentsTable(list) {
    const tbody = document.getElementById('departmentsTableBody');
    if (!list || list.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    <div class="empty-state">
                        <div class="empty-state-icon"><i class="bi bi-diagram-3"></i></div>
                        <h6 class="empty-state-title">No Departments Found</h6>
                        <p class="empty-state-desc">Get started by creating your first academic department.</p>
                        <button class="btn btn-sm btn-primary rounded-pill px-3" onclick="document.getElementById('btnOpenAddDepartmentModal').click()">
                            <i class="bi bi-plus-lg me-1"></i> Add Department
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    list.forEach(dept => {
        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${dept.department_id}</span></td>
                <td><span class="badge bg-primary-subtle text-primary border border-primary-subtle fw-semibold px-2 py-1">${escapeHtml(dept.department_code)}</span></td>
                <td class="fw-semibold text-dark">${escapeHtml(dept.department_name)}</td>
                <td class="text-end">
                    <div class="btn-group">
                        <button class="btn btn-action btn-action-edit me-1" title="Edit Department" onclick="openEditDepartmentModal(${dept.department_id})">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-action btn-action-delete" title="Delete Department" onclick="handleDeleteDepartment(${dept.department_id}, '${escapeHtml(dept.department_code)}')">
                            <i class="bi bi-trash3-fill"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function filterDepartments(searchTerm) {
    const term = (searchTerm || '').toLowerCase().trim();
    if (!term) {
        renderDepartmentsTable(departmentsList);
        return;
    }

    const filtered = departmentsList.filter(d => 
        (d.department_code && d.department_code.toLowerCase().includes(term)) ||
        (d.department_name && d.department_name.toLowerCase().includes(term)) ||
        String(d.department_id).includes(term)
    );

    renderDepartmentsTable(filtered);
}

function resetDepartmentForm() {
    document.getElementById('departmentForm').reset();
    document.getElementById('departmentIdInput').value = '';
}

function openEditDepartmentModal(departmentId) {
    const dept = departmentsList.find(d => d.department_id === departmentId);
    if (!dept) return;

    document.getElementById('departmentIdInput').value = dept.department_id;
    document.getElementById('departmentCodeInput').value = dept.department_code;
    document.getElementById('departmentNameInput').value = dept.department_name;

    document.getElementById('departmentModalTitle').textContent = `Edit Department: ${dept.department_code}`;
    document.getElementById('saveDepartmentBtnText').textContent = 'Update Department';
    departmentModalInstance.show();
}

async function handleDepartmentFormSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('departmentIdInput').value;
    const code = document.getElementById('departmentCodeInput').value.trim();
    const name = document.getElementById('departmentNameInput').value.trim();

    if (!code || !name) {
        showToast('warning', 'Validation', 'Please fill in all required fields.');
        return;
    }

    const payload = {
        department_code: code.toUpperCase(),
        department_name: name
    };

    const isEdit = Boolean(id);
    const url = isEdit ? `/api/departments/${id}` : '/api/departments';
    const method = isEdit ? 'PUT' : 'POST';

    const saveBtn = document.getElementById('btnSaveDepartment');
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
            departmentModalInstance.hide();
            showToast('success', isEdit ? 'Department Updated' : 'Department Created', result.message || 'Saved successfully.');
            loadDepartments();
        } else {
            showToast('error', 'Operation Failed', result.error || (result.details || 'Unable to save department.'));
        }
    } catch (err) {
        console.error('Error saving department:', err);
        showToast('error', 'Server Error', 'Failed to save department data.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = `<span id="saveDepartmentBtnText">${isEdit ? 'Update Department' : 'Create Department'}</span>`;
    }
}

function handleDeleteDepartment(id, code) {
    confirmAction(
        'Delete Department',
        `Are you sure you want to delete department "${code}"? If any students are enrolled in this department, deletion will be blocked by relational constraints.`,
        'Delete Department',
        async () => {
            try {
                const res = await fetch(`/api/departments/${id}`, { method: 'DELETE' });
                const result = await res.json();

                if (result.success) {
                    showToast('success', 'Department Deleted', result.message || 'Department successfully removed.');
                    loadDepartments();
                } else {
                    showToast('error', 'Deletion Prevented', result.error || 'Foreign-key restriction: students belong to this department.');
                }
            } catch (err) {
                console.error('Error deleting department:', err);
                showToast('error', 'Server Error', 'Could not delete department.');
            }
        }
    );
}

