/**
 * PsyFind Toast Notification Component
 * Non-intrusive user feedback system
 */

const Toast = (function() {
  'use strict';

  let container = null;
  let toasts = [];
  const DEFAULT_DURATION = 5000;
  const MAX_TOASTS = 5;

  /**
   * Initialize the toast container
   */
  function init() {
    if (container) return;

    container = document.createElement('div');
    container.className = 'toast-container';
    container.setAttribute('role', 'status');
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'true');
    document.body.appendChild(container);
  }

  /**
   * Create and show a toast notification
   * @param {Object} options - Toast options
   * @returns {Object} Toast control object
   */
  function show(options = {}) {
    init();

    const {
      type = 'info',
      title = '',
      message = '',
      duration = DEFAULT_DURATION,
      dismissible = true,
      onDismiss = null
    } = options;

    // Limit number of toasts
    if (toasts.length >= MAX_TOASTS) {
      removeToast(toasts[0]);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'status');

    // Icon based on type
    const icons = {
      success: 'fa-check-circle',
      error: 'fa-exclamation-circle',
      warning: 'fa-exclamation-triangle',
      info: 'fa-info-circle'
    };

    const iconClass = icons[type] || icons.info;

    // Build toast HTML
    toast.innerHTML = `
      <i class="fas ${iconClass} toast__icon"></i>
      <div class="toast__content">
        ${title ? `<div class="toast__title">${escapeHtml(title)}</div>` : ''}
        ${message ? `<div class="toast__message">${escapeHtml(message)}</div>` : ''}
      </div>
      ${dismissible ? `
        <button class="toast__close" aria-label="Dismiss notification">
          <i class="fas fa-times"></i>
        </button>
      ` : ''}
    `;

    // Add to container
    container.appendChild(toast);

    // Store toast data
    const toastData = {
      element: toast,
      timeoutId: null,
      onDismiss
    };
    toasts.push(toastData);

    // Setup dismiss handler
    if (dismissible) {
      const closeBtn = toast.querySelector('.toast__close');
      closeBtn.addEventListener('click', () => dismiss(toastData));
      
      // Click toast to dismiss
      toast.addEventListener('click', (e) => {
        if (e.target === toast || e.target.closest('.toast__content')) {
          dismiss(toastData);
        }
      });
    }

    // Auto dismiss
    if (duration > 0) {
      toastData.timeoutId = setTimeout(() => dismiss(toastData), duration);
    }

    // Pause on hover
    toast.addEventListener('mouseenter', () => {
      if (toastData.timeoutId) {
        clearTimeout(toastData.timeoutId);
        toastData.timeoutId = null;
      }
    });

    toast.addEventListener('mouseleave', () => {
      if (duration > 0) {
        toastData.timeoutId = setTimeout(() => dismiss(toastData), duration / 2);
      }
    });

    return {
      dismiss: () => dismiss(toastData)
    };
  }

  /**
   * Dismiss a toast
   * @param {Object} toastData - Toast data object
   */
  function dismiss(toastData) {
    if (!toastData.element) return;

    // Clear timeout
    if (toastData.timeoutId) {
      clearTimeout(toastData.timeoutId);
    }

    // Add exit animation
    toastData.element.classList.add('toast--out');

    // Remove after animation
    setTimeout(() => removeToast(toastData), 300);

    // Call callback
    if (toastData.onDismiss) {
      toastData.onDismiss();
    }
  }

  /**
   * Remove toast from DOM and array
   * @param {Object} toastData - Toast data object
   */
  function removeToast(toastData) {
    const index = toasts.indexOf(toastData);
    if (index > -1) {
      toasts.splice(index, 1);
    }

    if (toastData.element && toastData.element.parentNode) {
      toastData.element.parentNode.removeChild(toastData.element);
    }
  }

  /**
   * Escape HTML to prevent XSS
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Convenience methods
  function success(message, title = '') {
    return show({ type: 'success', title, message });
  }

  function error(message, title = '') {
    return show({ type: 'error', title, message, duration: 8000 });
  }

  function warning(message, title = '') {
    return show({ type: 'warning', title, message });
  }

  function info(message, title = '') {
    return show({ type: 'info', title, message });
  }

  /**
   * Clear all toasts
   */
  function clearAll() {
    [...toasts].forEach(dismiss);
  }

  // Public API
  return {
    init,
    show,
    success,
    error,
    warning,
    info,
    clearAll
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Toast;
}
