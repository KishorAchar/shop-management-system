// Main JavaScript for Shop Management System

// Global Quick Action Handler
window.quickAction = function() {
    // Immediate visual feedback (Heartbeat)
    if (typeof showToast === 'function') {
        showToast('System Pulse: Action detected...', 'info');
    }
    
    // Normalize path
    const path = window.location.pathname.replace(/\/$/, "");
    console.log("[Quick Action] Executing for path:", path);
    
    // 1. Inventory Action
    if (path.endsWith('/dashboard/bay')) {
        const modal = document.getElementById('addProductModal');
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
            console.log("[Quick Action] Opened Add Product Modal");
            return;
        }
    }
    
    // 2. Orders Action
    if (path.endsWith('/orders')) {
        showToast('Scanning orbital transmissions...', 'info');
        console.log("[Quick Action] Orders status reported");
        return;
    }

    // 3. Navigation Check/Fallback
    const navItems = document.querySelectorAll('.nav-dock .nav-item');
    if (navItems.length > 0) {
        const urls = Array.from(navItems).map(item => item.getAttribute('href'));
        const currentPath = window.location.pathname;
        
        let nextIndex = 0;
        for (let i = 0; i < urls.length; i++) {
            if (urls[i] && (currentPath === urls[i] || currentPath === urls[i] + '/')) {
                nextIndex = (i + 1) % urls.length;
                break;
            }
        }
        
        showToast('Engaging warp drive...', 'info');
        setTimeout(() => {
            window.location.href = urls[nextIndex];
        }, 300);
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Add listener to FAB button
    const fab = document.querySelector('.fab');
    if (fab) {
        fab.addEventListener('click', window.quickAction);
        console.log("[Quick Action] FAB listener initialized.");
    }

    // Remove loader
    setTimeout(() => {
        const loader = document.getElementById('loader');
        if (loader) {
            loader.classList.add('hidden');
        }
    }, 500);

    // Initialize UI
    initializeUI();
});

function initializeUI() {
    // Add hover effects to hex stats
    const hexStats = document.querySelectorAll('.hex-stat');
    hexStats.forEach(stat => {
        stat.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05)';
        });
        stat.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Animate stats on dashboard load
    if (document.getElementById('page-dashboard')?.classList.contains('active')) {
        animateStats();
    }
}

// Navigation function
function showPage(pageName) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    if (event && event.target) {
        event.target.closest('.nav-item').classList.add('active');
    }

    // Switch page
    document.querySelectorAll('.page-section').forEach(page => {
        page.classList.remove('active');
    });
    
    const targetPage = document.getElementById(`page-${pageName}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }

    // Special animations
    if (pageName === 'dashboard') animateStats();
    if (pageName === 'analytics') animateBars();
}

// Animate hex stats
function animateStats() {
    const stats = document.querySelectorAll('.hex-stat');
    stats.forEach((stat, index) => {
        setTimeout(() => {
            stat.style.transform = 'scale(1.1)';
            setTimeout(() => {
                stat.style.transform = 'scale(1)';
            }, 200);
        }, index * 100);
    });
}

// Animate progress bars
function animateBars() {
    document.querySelectorAll('.stat-bar-fill').forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}



// Modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId + 'Modal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId + 'Modal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
            modal.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
});

// Toast notification system
function showToast(message, type = 'success') {
    // Remove existing toasts
    const existingToast = document.querySelector('.toast');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${type === 'success' ? '✓' : '⚠'}</div>
        <div class="toast-message">${message}</div>
    `;
    
    // Add styles
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        right: 30px;
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 3000;
        animation: slideIn 0.3s ease;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    `;
    
    const icon = toast.querySelector('.toast-icon');
    icon.style.cssText = `
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: ${type === 'success' ? 'var(--success)' : (type === 'info' ? 'var(--neon-blue)' : 'var(--danger)')};
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Add animation keyframes dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100px); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Form validation helper
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = 'var(--danger)';
            input.style.boxShadow = '0 0 10px rgba(239, 68, 68, 0.3)';
        } else {
            input.style.borderColor = '';
            input.style.boxShadow = '';
        }
    });
    
    return isValid;
}

// AJAX helper
function ajaxRequest(url, method = 'GET', data = null) {
    return fetch(url, {
        method: method,
        body: data,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCookie('csrftoken')
        }
    }).then(response => response.json());
}

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Real-time clock for dashboard
function updateClock() {
    const clockElements = document.querySelectorAll('.live-clock');
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour12: false, 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    clockElements.forEach(el => {
        el.textContent = timeString;
    });
}

// Update clock every second if on dashboard
if (document.getElementById('page-dashboard')) {
    setInterval(updateClock, 1000);
}

// Export functions for global access
window.showPage = showPage;
window.openModal = openModal;
window.closeModal = closeModal;
window.quickAction = quickAction;
window.showToast = showToast;
window.validateForm = validateForm;
window.ajaxRequest = ajaxRequest;

function deleteOrder(orderId){

    Swal.fire({
        title: 'Delete Order?',
        text: 'This action cannot be undone.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e53935',
        cancelButtonColor: '#666',
        confirmButtonText: 'Yes, Delete'
    }).then((result) => {

        if(result.isConfirmed){

            fetch(`/orders/${orderId}/delete/`,{
                method:'POST',
                headers:{
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With':'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {

                if(data.success){

                    Swal.fire(
                        'Deleted!',
                        'Order deleted successfully.',
                        'success'
                    );

                    setTimeout(() => {
                        location.reload();
                    }, 1000);

                }else{
                    Swal.fire('Error', data.error, 'error');
                }

            });

        }

    });
}

window.deleteOrder = deleteOrder;