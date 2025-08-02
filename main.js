/**
 * QuickDesk Main JavaScript
 * Handles interactive functionality for the help desk application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize vote buttons
    initializeVoteButtons();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize file upload preview
    initializeFileUpload();
    
    // Initialize auto-refresh for dashboard
    initializeAutoRefresh();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize keyboard shortcuts
    initializeKeyboardShortcuts();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize vote button functionality
 */
function initializeVoteButtons() {
    const voteButtons = document.querySelectorAll('.vote-button');
    
    voteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const form = this.closest('form');
            const ticketId = form.querySelector('input[name="ticket_id"]').value;
            const voteType = this.dataset.voteType;
            
            // Add loading state
            this.disabled = true;
            const originalHtml = this.innerHTML;
            this.innerHTML = '<i class="bi bi-arrow-repeat spin"></i>';
            
            // Submit vote
            submitVote(ticketId, voteType, this, originalHtml);
        });
    });
}

/**
 * Submit vote via AJAX
 */
function submitVote(ticketId, voteType, button, originalHtml) {
    const formData = new FormData();
    formData.append('vote_type', voteType);
    formData.append('csrf_token', document.querySelector('[name="csrf_token"]').value);
    
    fetch(`/tickets/${ticketId}/vote`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateVoteButtons(data, button);
        button.innerHTML = originalHtml;
        button.disabled = false;
    })
    .catch(error => {
        console.error('Vote submission failed:', error);
        button.innerHTML = originalHtml;
        button.disabled = false;
        showToast('Vote submission failed. Please try again.', 'error');
    });
}

/**
 * Update vote button states
 */
function updateVoteButtons(data, clickedButton) {
    const voteContainer = clickedButton.closest('.vote-buttons');
    const upButton = voteContainer.querySelector('[data-vote-type="up"]');
    const downButton = voteContainer.querySelector('[data-vote-type="down"]');
    
    // Update vote counts
    const upCount = upButton.querySelector('.vote-count');
    const downCount = downButton.querySelector('.vote-count');
    
    if (upCount) upCount.textContent = data.upvotes;
    if (downCount) downCount.textContent = data.downvotes;
    
    // Update button states
    upButton.classList.toggle('active-up', data.user_vote === 'up');
    downButton.classList.toggle('active-down', data.user_vote === 'down');
}

/**
 * Initialize search functionality
 */
function initializeSearch() {
    const searchInput = document.querySelector('#searchInput');
    const searchForm = document.querySelector('#searchForm');
    
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            
            // Add debounce to prevent too many requests
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 3 || this.value.length === 0) {
                    searchForm.submit();
                }
            }, 500);
        });
    }
    
    // Initialize filter changes
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            searchForm.submit();
        });
    });
}

/**
 * Initialize file upload preview
 */
function initializeFileUpload() {
    const fileInput = document.querySelector('input[type="file"]');
    
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            const preview = document.querySelector('#filePreview');
            
            if (file) {
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                const fileName = file.name;
                
                if (preview) {
                    preview.innerHTML = `
                        <div class="alert alert-info">
                            <i class="bi bi-file-earmark"></i>
                            <strong>${fileName}</strong> (${fileSize} MB)
                        </div>
                    `;
                    preview.style.display = 'block';
                }
                
                // Validate file size (16MB limit)
                if (file.size > 16 * 1024 * 1024) {
                    showToast('File size must be less than 16MB', 'error');
                    this.value = '';
                    if (preview) preview.style.display = 'none';
                }
            } else {
                if (preview) preview.style.display = 'none';
            }
        });
    }
}

/**
 * Initialize auto-refresh for dashboard
 */
function initializeAutoRefresh() {
    const dashboard = document.querySelector('.dashboard');
    
    if (dashboard) {
        // Refresh statistics every 5 minutes
        setInterval(() => {
            refreshDashboardStats();
        }, 5 * 60 * 1000);
    }
}

/**
 * Refresh dashboard statistics
 */
function refreshDashboardStats() {
    const statCards = document.querySelectorAll('.stat-card');
    
    fetch('/dashboard/stats', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateStatCards(data);
    })
    .catch(error => {
        console.error('Failed to refresh dashboard stats:', error);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
    
    // Real-time validation feedback
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

/**
 * Validate individual form field
 */
function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.toggle('is-valid', isValid);
    field.classList.toggle('is-invalid', !isValid);
    
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback && !isValid) {
        feedback.textContent = field.validationMessage;
    }
}

/**
 * Initialize keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Only activate shortcuts when not typing in form fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Ctrl/Cmd + N: New ticket
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            const newTicketBtn = document.querySelector('[href*="create"]');
            if (newTicketBtn) newTicketBtn.click();
        }
        
        // Ctrl/Cmd + /: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
            e.preventDefault();
            const searchInput = document.querySelector('#searchInput, input[name="query"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape: Close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) modal.hide();
            }
        }
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('#toastContainer') || createToastContainer();
    const toastId = 'toast-' + Date.now();
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-bg-${type === 'error' ? 'danger' : type}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-${getToastIcon(type)}"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: type === 'error' ? 8000 : 5000
    });
    
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1080';
    document.body.appendChild(container);
    return container;
}

/**
 * Get appropriate icon for toast type
 */
function getToastIcon(type) {
    const icons = {
        success: 'check-circle',
        error: 'exclamation-triangle',
        warning: 'exclamation-circle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Utility function to format dates
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return 'Yesterday';
    } else if (diffDays < 7) {
        return `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}

/**
 * Utility function to debounce functions
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func.apply(context, args);
    };
}

/**
 * Utility function to animate numbers
 */
function animateNumber(element, start, end, duration) {
    if (start === end) return;
    
    const range = end - start;
    let current = start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    
    const timer = setInterval(function() {
        current += increment;
        element.textContent = current;
        
        if (current === end) {
            clearInterval(timer);
        }
    }, stepTime);
}

/**
 * Handle connection errors gracefully
 */
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showToast('Connection lost. Some features may not work properly.', 'warning');
});

/**
 * Export functions for use in other scripts
 */
window.QuickDesk = {
    showToast,
    formatDate,
    debounce,
    animateNumber
};
