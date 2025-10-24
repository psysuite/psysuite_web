// PsySuite Web Manager JavaScript

// Global variables
let selectedTestId = null;
let selectedExperiments = [];

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const content = document.querySelector('.content');
    content.insertBefore(alertDiv, content.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Navigation functions
function goBack() {
    window.history.back();
}

function logout() {
    // Use the web logout route directly for simplicity and reliability
    window.location.href = '/logout';
}

// Test management functions
function selectTest(testId) {
    // Remove previous selection
    document.querySelectorAll('.test-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked item
    const testItem = document.querySelector(`[data-test-id="${testId}"]`);
    if (testItem) {
        testItem.classList.add('selected');
        selectedTestId = testId;
        loadTestParameters(testId);
    }
}

function loadTestParameters(testId) {
    fetch(`/api/tests/${testId}`)
        .then(response => response.json())
        .then(test => {
            const tbody = document.getElementById('parametersBody');
            tbody.innerHTML = '';
            
            // Add default parameters
            if (test.default_parameters) {
                Object.entries(test.default_parameters).forEach(([key, value]) => {
                    const row = tbody.insertRow();
                    row.insertCell(0).textContent = key;
                    row.insertCell(1).textContent = value;
                });
            }
            
            // Add separator
            const separatorRow = tbody.insertRow();
            separatorRow.insertCell(0).innerHTML = '<strong>Trial Columns</strong>';
            separatorRow.insertCell(1).innerHTML = '<strong>Type</strong>';
            
            // Add trial columns
            if (test.trial_columns) {
                Object.entries(test.trial_columns).forEach(([key, value]) => {
                    const row = tbody.insertRow();
                    row.insertCell(0).textContent = key;
                    row.insertCell(1).textContent = value;
                });
            }
        })
        .catch(error => {
            console.error('Error loading test parameters:', error);
            showAlert('Error loading test parameters', 'danger');
        });
}

function createTest() {
    window.location.href = '/admin/test/new';
}

function editTest() {
    if (!selectedTestId) {
        showAlert('Please select a test first', 'warning');
        return;
    }
    window.location.href = `/admin/test/${selectedTestId}/edit`;
}

function deleteTest() {
    if (!selectedTestId) {
        showAlert('Please select a test first', 'warning');
        return;
    }
    
    confirmAction('Are you sure you want to delete this test? This action cannot be undone.', () => {
        fetch(`/api/tests/${selectedTestId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                showAlert('Test deleted successfully', 'success');
                location.reload();
            } else {
                showAlert('Error deleting test', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting test:', error);
            showAlert('Error deleting test', 'danger');
        });
    });
}

function viewExperiments(testId = null) {
    const id = testId || selectedTestId;
    if (!id) {
        showAlert('Please select a test first', 'warning');
        return;
    }
    window.location.href = `/experiments/${id}`;
}

// Experiment management functions
function toggleExperimentSelection(experimentId) {
    const checkbox = document.querySelector(`input[data-experiment-id="${experimentId}"]`);
    if (checkbox) {
        checkbox.checked = !checkbox.checked;
        updateSelectedExperiments();
    }
}

function selectAllExperiments() {
    const checkboxes = document.querySelectorAll('input[data-experiment-id]');
    const allSelected = Array.from(checkboxes).every(cb => cb.checked);
    
    checkboxes.forEach(cb => {
        cb.checked = !allSelected;
    });
    
    updateSelectedExperiments();
}

function updateSelectedExperiments() {
    const checkboxes = document.querySelectorAll('input[data-experiment-id]:checked');
    selectedExperiments = Array.from(checkboxes).map(cb => cb.dataset.experimentId);
    
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.disabled = selectedExperiments.length === 0;
    }
}

function downloadSelectedExperiments() {
    if (selectedExperiments.length === 0) {
        showAlert('Please select experiments to download', 'warning');
        return;
    }
    
    const params = new URLSearchParams();
    selectedExperiments.forEach(id => params.append('experiment_ids', id));
    
    window.location.href = `/api/experiments/download?${params.toString()}`;
}

// User management functions
function createUser() {
    window.location.href = '/admin/user/new';
}

function deleteUser(userId) {
    confirmAction('Are you sure you want to delete this user?', () => {
        fetch(`/api/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => {
            if (response.ok) {
                showAlert('User deleted successfully', 'success');
                location.reload();
            } else {
                showAlert('Error deleting user', 'danger');
            }
        })
        .catch(error => {
            console.error('Error deleting user:', error);
            showAlert('Error deleting user', 'danger');
        });
    });
}

function assignTests(userId) {
    // This will open a modal dialog for test assignment
    // Implementation will be added in the web interface tasks
    console.log('Assign tests to user:', userId);
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for experiment checkboxes
    document.querySelectorAll('input[data-experiment-id]').forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedExperiments);
    });
    
    // Initialize selected experiments count
    updateSelectedExperiments();
});