/**
 * Integrated Learning Platform - Main JavaScript
 * Shared utilities and helper functions
 */

// ==================== UTILITY FUNCTIONS ====================

/**
 * Show loading spinner
 */
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="spinner"></div>
            <div class="loading-text">Loading...</div>
        `;
        element.classList.remove('hidden');
    }
}

/**
 * Hide loading spinner
 */
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('hidden');
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    
    const icons = {
        success: '✅',
        info: 'ℹ️',
        warning: '⚠️',
        error: '❌'
    };
    
    alertDiv.innerHTML = `
        <span>${icons[type] || 'ℹ️'}</span>
        <span>${message}</span>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alertDiv.style.transition = 'opacity 0.3s ease-out';
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
}

/**
 * Format date and time
 */
function formatDateTime(date = new Date()) {
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Validate form input
 */
function validateInput(input, type = 'text') {
    const value = input.value.trim();
    
    switch(type) {
        case 'text':
            return value.length > 0;
        case 'number':
            return !isNaN(value) && value.length > 0;
        case 'email':
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
        default:
            return value.length > 0;
    }
}

/**
 * Sanitize HTML to prevent XSS
 */
function sanitizeHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Deep clone object
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ==================== LOCAL STORAGE HELPERS ====================

/**
 * Save to localStorage with error handling
 */
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

/**
 * Load from localStorage with error handling
 */
function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return defaultValue;
    }
}

/**
 * Clear specific item from localStorage
 */
function clearStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Error clearing localStorage:', error);
        return false;
    }
}

// ==================== API HELPERS ====================

/**
 * Generic API call wrapper
 */
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

/**
 * POST request helper
 */
async function post(endpoint, data) {
    return apiCall(endpoint, 'POST', data);
}

/**
 * GET request helper
 */
async function get(endpoint) {
    return apiCall(endpoint, 'GET');
}

// ==================== ANIMATION HELPERS ====================

/**
 * Fade in element
 */
function fadeIn(element, duration = 300) {
    element.style.opacity = '0';
    element.style.display = 'block';
    
    let opacity = 0;
    const increment = 50 / duration;
    
    const timer = setInterval(() => {
        opacity += increment;
        element.style.opacity = opacity.toString();
        
        if (opacity >= 1) {
            clearInterval(timer);
            element.style.opacity = '1';
        }
    }, 50);
}

/**
 * Fade out element
 */
function fadeOut(element, duration = 300) {
    let opacity = 1;
    const decrement = 50 / duration;
    
    const timer = setInterval(() => {
        opacity -= decrement;
        element.style.opacity = opacity.toString();
        
        if (opacity <= 0) {
            clearInterval(timer);
            element.style.display = 'none';
            element.style.opacity = '0';
        }
    }, 50);
}

/**
 * Smooth scroll to element
 */
function scrollToElement(elementId, offset = 0) {
    const element = document.getElementById(elementId);
    if (element) {
        const top = element.offsetTop - offset;
        window.scrollTo({
            top,
            behavior: 'smooth'
        });
    }
}

// ==================== FORM HELPERS ====================

/**
 * Collect form data as object
 */
function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return null;
    
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

/**
 * Clear form
 */
function clearForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.reset();
    }
}

/**
 * Disable form
 */
function disableForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => input.disabled = true);
    }
}

/**
 * Enable form
 */
function enableForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll('input, select, textarea, button');
        inputs.forEach(input => input.disabled = false);
    }
}

// ==================== CHAT HELPERS ====================

/**
 * Create chat message element
 */
function createChatMessage(role, content, emotion = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : (role === 'assistant' ? '🤖' : '💝');
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = content;
    
    if (emotion) {
        const emotionTag = document.createElement('div');
        emotionTag.className = 'emotion-tag';
        emotionTag.innerHTML = `<strong>Emotion:</strong> ${emotion.primary_emotion} (${Math.round(emotion.confidence * 100)}%)`;
        messageContent.appendChild(emotionTag);
    }
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);
    
    return messageDiv;
}

/**
 * Add message to chat
 */
function addChatMessage(containerId, role, content, emotion = null) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const message = createChatMessage(role, content, emotion);
    container.appendChild(message);
    
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
}

/**
 * Clear chat messages
 */
function clearChat(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '';
    }
}

// ==================== PROGRESS HELPERS ====================

/**
 * Update progress bar
 */
function updateProgress(elementId, percentage) {
    const progressBar = document.querySelector(`#${elementId} .progress-fill`);
    if (progressBar) {
        progressBar.style.width = `${percentage}%`;
    }
}

/**
 * Calculate percentage
 */
function calculatePercentage(value, total) {
    if (total === 0) return 0;
    return Math.round((value / total) * 100);
}

// ==================== ACCESSIBILITY HELPERS ====================

/**
 * Announce to screen readers
 */
function announce(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => announcement.remove(), 1000);
}

/**
 * Set focus on element
 */
function setFocus(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.focus();
    }
}

// ==================== EVENT LISTENERS ====================

/**
 * Wait for DOM to be ready
 */
function ready(callback) {
    if (document.readyState !== 'loading') {
        callback();
    } else {
        document.addEventListener('DOMContentLoaded', callback);
    }
}

// ==================== INITIALIZATION ====================

ready(() => {
    console.log('Integrated Learning Platform initialized');
    
    // Add any global event listeners here
    
    // Handle navigation timing
    if (performance && performance.navigation.type === 1) {
        console.log('Page was refreshed');
    }
});

// ==================== EXPORTS ====================

// Make functions available globally
window.AppUtils = {
    showLoading,
    hideLoading,
    showAlert,
    formatDateTime,
    validateInput,
    sanitizeHTML,
    deepClone,
    debounce,
    saveToStorage,
    loadFromStorage,
    clearStorage,
    apiCall,
    post,
    get,
    fadeIn,
    fadeOut,
    scrollToElement,
    getFormData,
    clearForm,
    disableForm,
    enableForm,
    createChatMessage,
    addChatMessage,
    clearChat,
    updateProgress,
    calculatePercentage,
    announce,
    setFocus,
    ready
};

// ==================== DARK MODE FUNCTIONALITY ====================

/**
 * Initialize dark mode
 */
function initDarkMode() {
    // Check for saved dark mode preference
    const darkMode = localStorage.getItem('darkMode');
    
    if (darkMode === 'enabled') {
        document.body.classList.add('dark-mode');
    }
    
    // Add event listener to dark mode toggle button
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', toggleDarkMode);
    }
}

/**
 * Toggle dark mode
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    
    // Save preference to localStorage
    if (document.body.classList.contains('dark-mode')) {
        localStorage.setItem('darkMode', 'enabled');
    } else {
        localStorage.setItem('darkMode', 'disabled');
    }
}

// Initialize dark mode when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDarkMode);
} else {
    initDarkMode();
}
