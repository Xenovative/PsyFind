/**
 * PsyFind Modal Component
 * Accessible modal dialog system
 */

const Modal = (function() {
  'use strict';

  let activeModal = null;
  let previousActiveElement = null;
  let focusableElements = [];

  // Focusable element selectors
  const FOCUSABLE_SELECTORS = [
    'button:not([disabled])',
    'a[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])'
  ].join(', ');

  /**
   * Create a modal
   * @param {Object} options - Modal options
   * @returns {Object} Modal control object
   */
  function create(options = {}) {
    const {
      id = 'modal-' + Date.now(),
      title = '',
      content = '',
      size = 'md', // sm, md, lg, xl, full
      closable = true,
      onClose = null,
      onConfirm = null,
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      showFooter = true,
      danger = false
    } = options;

    // Store previously focused element
    previousActiveElement = document.activeElement;

    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = id;
    overlay.className = 'modal-overlay';
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-labelledby', `${id}-title`);

    // Size class
    const sizeClass = size !== 'md' ? `modal--${size}` : '';

    // Build modal HTML
    overlay.innerHTML = `
      <div class="modal ${sizeClass}">
        <div class="modal__header">
          <h3 class="modal__title" id="${id}-title">
            ${title ? `<i class="fas fa-info-circle"></i> ${escapeHtml(title)}` : ''}
          </h3>
          ${closable ? `
            <button class="modal__close" aria-label="Close dialog">
              <i class="fas fa-times"></i>
            </button>
          ` : ''}
        </div>
        <div class="modal__body">
          ${typeof content === 'string' ? content : ''}
        </div>
        ${showFooter ? `
          <div class="modal__footer">
            <button class="btn btn--secondary modal-cancel">${escapeHtml(cancelText)}</button>
            <button class="btn ${danger ? 'btn--danger' : 'btn--primary'} modal-confirm">${escapeHtml(confirmText)}</button>
          </div>
        ` : ''}
      </div>
    `;

    document.body.appendChild(overlay);

    // Get focusable elements
    const modal = overlay.querySelector('.modal');
    focusableElements = Array.from(modal.querySelectorAll(FOCUSABLE_SELECTORS));

    // Event handlers
    const modalData = {
      id,
      overlay,
      onClose,
      onConfirm,
      closed: false
    };

    // Close handlers
    if (closable) {
      overlay.querySelector('.modal__close').addEventListener('click', () => close(modalData));
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close(modalData);
      });
    }

    // Footer buttons
    if (showFooter) {
      overlay.querySelector('.modal-cancel').addEventListener('click', () => close(modalData));
      overlay.querySelector('.modal-confirm').addEventListener('click', () => {
        if (onConfirm) onConfirm();
        close(modalData);
      });
    }

    // Keyboard handlers
    overlay.addEventListener('keydown', (e) => handleKeydown(e, modalData));

    // Store as active
    activeModal = modalData;

    // Prevent body scroll
    document.body.style.overflow = 'hidden';

    // Show modal (trigger animation)
    requestAnimationFrame(() => {
      overlay.classList.add('modal-overlay--open');
      
      // Focus first element
      const firstFocusable = focusableElements[0];
      if (firstFocusable) {
        firstFocusable.focus();
      }
    });

    return modalData;
  }

  /**
   * Handle keyboard events for accessibility
   * @param {KeyboardEvent} e - Keyboard event
   * @param {Object} modalData - Modal data
   */
  function handleKeydown(e, modalData) {
    if (e.key === 'Escape' && modalData.overlay.querySelector('.modal__close')) {
      e.preventDefault();
      close(modalData);
    }

    if (e.key === 'Tab') {
      handleTabNavigation(e, modalData);
    }
  }

  /**
   * Handle tab navigation to trap focus
   * @param {KeyboardEvent} e - Keyboard event
   * @param {Object} modalData - Modal data
   */
  function handleTabNavigation(e, modalData) {
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (e.shiftKey && document.activeElement === firstElement) {
      e.preventDefault();
      lastElement.focus();
    } else if (!e.shiftKey && document.activeElement === lastElement) {
      e.preventDefault();
      firstElement.focus();
    }
  }

  /**
   * Close a modal
   * @param {Object} modalData - Modal data
   */
  function close(modalData) {
    if (modalData.closed) return;
    modalData.closed = true;

    // Trigger exit animation
    modalData.overlay.classList.remove('modal-overlay--open');

    // Wait for animation then remove
    setTimeout(() => {
      if (modalData.overlay.parentNode) {
        modalData.overlay.parentNode.removeChild(modalData.overlay);
      }

      // Restore body scroll
      if (activeModal === modalData) {
        document.body.style.overflow = '';
        activeModal = null;
      }

      // Restore focus
      if (previousActiveElement) {
        previousActiveElement.focus();
      }

      // Call callback
      if (modalData.onClose) {
        modalData.onClose();
      }
    }, 300);
  }

  /**
   * Close the active modal
   */
  function closeActive() {
    if (activeModal) {
      close(activeModal);
    }
  }

  /**
   * Show an alert modal
   * @param {Object} options - Alert options
   * @returns {Object} Modal control
   */
  function alert(options = {}) {
    return create({
      ...options,
      showFooter: true,
      confirmText: options.confirmText || 'OK',
      cancelText: null
    });
  }

  /**
   * Show a confirmation modal
   * @param {Object} options - Confirmation options
   * @returns {Object} Modal control
   */
  function confirm(options = {}) {
    return create({
      ...options,
      showFooter: true,
      danger: options.danger || false
    });
  }

  /**
   * Show a custom content modal
   * @param {Object} options - Modal options
   * @returns {Object} Modal control
   */
  function custom(options = {}) {
    return create(options);
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

  // Public API
  return {
    create,
    alert,
    confirm,
    custom,
    close: closeActive
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Modal;
}
