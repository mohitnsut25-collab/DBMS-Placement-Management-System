/**
 * Dashboard JavaScript Handler
 * Fetches dynamic statistics, recent applications, and upcoming interviews directly from MySQL APIs.
 */

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardMetrics();

    const refreshBtn = document.getElementById('refreshDashboardBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.classList.add('disabled');
            refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Refreshing...';
            loadDashboardMetrics().finally(() => {
                refreshBtn.classList.remove('disabled');
                refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise"></i> <span>Refresh Data</span>';
                showToast('success', 'Dashboard Refreshed', 'Latest data loaded from MySQL database.');
            });
        });
    }
});

async function loadDashboardMetrics() {
    try {
        // Fetch data concurrently from all core endpoints
        const [
            deptRes,
            studentsRes,
            companiesRes,
            jobsRes,
            appsRes,
            interviewsRes,
            offersRes
        ] = await Promise.all([
            fetch('/api/departments').then(r => r.json()).catch(() => ({ data: [] })),
            fetch('/api/students').then(r => r.json()).catch(() => ({ data: [] })),
            fetch('/api/companies').then(r => r.json()).catch(() => ({ data: [] })),
            fetch('/api/jobs').then(r => r.json()).catch(() => ({ data: [] })),
            fetch('/api/applications').then(r => r.json()).catch(() => ({ data: [] })),
            fetch('/api/interviews').then(r => r.json()).catch(() => ({ data: [] })),
            fetch('/api/offers').then(r => r.json()).catch(() => ({ data: [] }))
        ]);

        const departments = deptRes.data || [];
        const students = studentsRes.data || [];
        const companies = companiesRes.data || [];
        const jobs = jobsRes.data || [];
        const applications = appsRes.data || [];
        const interviews = interviewsRes.data || [];
        const offers = offersRes.data || [];

        // Count Accepted Offers
        const acceptedOffers = offers.filter(o => (o.offer_status || '').trim() === 'Accepted');

        // Update 8 Stat Badges
        animateCounter('statTotalDepartments', departments.length);
        animateCounter('statTotalStudents', students.length);
        animateCounter('statTotalCompanies', companies.length);
        animateCounter('statTotalJobs', jobs.length);
        animateCounter('statTotalApplications', applications.length);
        animateCounter('statTotalInterviews', interviews.length);
        animateCounter('statTotalOffers', offers.length);
        animateCounter('statTotalAcceptedOffers', acceptedOffers.length);

        // Update Pipeline Distribution
        updatePipelineCounts(applications);

        // Render Recent Applications Table
        renderRecentApplications(applications);

        // Render Upcoming / Scheduled Interviews
        renderUpcomingInterviews(interviews);

    } catch (err) {
        console.error('Error loading dashboard statistics:', err);
        showToast('error', 'Data Load Error', 'Failed to retrieve live metrics from backend.');
    }
}

function animateCounter(elementId, targetValue) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = targetValue.toLocaleString();
}

function updatePipelineCounts(applications) {
    let applied = 0, underReview = 0, shortlisted = 0, selected = 0, rejected = 0;

    applications.forEach(a => {
        const s = (a.application_status || '').trim();
        if (s === 'Applied') applied++;
        else if (s === 'Under Review') underReview++;
        else if (s === 'Shortlisted') shortlisted++;
        else if (s === 'Selected') selected++;
        else if (s === 'Rejected' || s === 'Withdrawn') rejected++;
    });

    const setBadge = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setBadge('badgeCountApplied', applied);
    setBadge('badgeCountUnderReview', underReview);
    setBadge('badgeCountShortlisted', shortlisted);
    setBadge('badgeCountSelected', selected);
    setBadge('badgeCountRejected', rejected);
}

function renderRecentApplications(applications) {
    const tbody = document.getElementById('recentApplicationsTableBody');
    if (!tbody) return;

    if (!applications || applications.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <i class="bi bi-inbox fs-4 d-block mb-1 text-secondary"></i>
                    No student applications submitted yet.
                </td>
            </tr>
        `;
        return;
    }

    // Sort descending by ID or application_date, take top 6
    const recent = [...applications].reverse().slice(0, 6);

    let html = '';
    recent.forEach(app => {
        html += `
            <tr>
                <td><span class="badge bg-light text-dark border">#${app.application_id}</span></td>
                <td>
                    <div class="fw-semibold text-dark">${escapeHtml(app.student_name || '—')}</div>
                    <div class="text-muted small" style="font-size:0.75rem;">Roll: ${escapeHtml(app.roll_number || '—')}</div>
                </td>
                <td><span class="text-dark fw-medium">${escapeHtml(app.job_title || '—')}</span></td>
                <td><span class="text-secondary">${escapeHtml(app.company_name || '—')}</span></td>
                <td class="text-muted small">${formatDate(app.application_date)}</td>
                <td>${renderStatusBadge(app.application_status)}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function renderUpcomingInterviews(interviews) {
    const tbody = document.getElementById('upcomingInterviewsTableBody');
    if (!tbody) return;

    if (!interviews || interviews.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-4 text-muted">
                    <i class="bi bi-calendar-x fs-4 d-block mb-1 text-secondary"></i>
                    No scheduled interviews found.
                </td>
            </tr>
        `;
        return;
    }

    // Sort or filter recent / scheduled
    const recentInterviews = [...interviews].reverse().slice(0, 5);

    let html = '';
    recentInterviews.forEach(inv => {
        html += `
            <tr>
                <td>
                    <div class="fw-semibold text-dark small">${escapeHtml(inv.student_name || 'Student #' + inv.application_id)}</div>
                    <div class="text-muted" style="font-size:0.72rem;">${escapeHtml(inv.company_name || '—')}</div>
                </td>
                <td>
                    <span class="badge bg-light text-dark border me-1">R${inv.round_number}</span>
                    <span class="text-secondary small">${escapeHtml(inv.interview_mode || '—')}</span>
                </td>
                <td class="text-muted small" style="font-size:0.75rem;">${formatDateTime(inv.interview_date)}</td>
                <td>${renderStatusBadge(inv.interview_result)}</td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}
