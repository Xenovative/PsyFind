/**
 * PsyFind API Module
 * Handles all backend communication with proper error handling
 */

const API = (function() {
  'use strict';

  const BASE_URL = '';
  const DEFAULT_TIMEOUT = 30000;

  /**
   * Make an API request with proper error handling
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @returns {Promise} API response
   */
  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), options.timeout || DEFAULT_TIMEOUT);

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      signal: controller.signal
    };

    try {
      const response = await fetch(url, {
        ...defaultOptions,
        ...options,
        headers: {
          ...defaultOptions.headers,
          ...options.headers
        }
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new APIError(
          error.message || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          error
        );
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error.name === 'AbortError') {
        throw new APIError('Request timeout', 408);
      }
      
      if (error instanceof APIError) {
        throw error;
      }

      throw new APIError(error.message || 'Network error', 0);
    }
  }

  /**
   * Custom API Error class
   */
  class APIError extends Error {
    constructor(message, status, data = {}) {
      super(message);
      this.name = 'APIError';
      this.status = status;
      this.data = data;
    }
  }

  // Chat API
  const Chat = {
    /**
     * Initialize a new chat session
     * @param {string} language - Preferred language
     * @returns {Promise} Session data
     */
    async init(language = 'zh') {
      return request('/chat/init', {
        method: 'POST',
        body: JSON.stringify({ language })
      });
    },

    /**
     * Send a message
     * @param {string} sessionId - Session ID
     * @param {string} message - User message
     * @returns {Promise} Assistant response
     */
    async sendMessage(sessionId, message) {
      return request('/chat/message', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, message })
      });
    },

    /**
     * Get chat history
     * @param {string} sessionId - Session ID
     * @returns {Promise} Chat history
     */
    async getHistory(sessionId) {
      return request(`/chat/history?session_id=${encodeURIComponent(sessionId)}`);
    }
  };

  // Assessment API
  const Assessment = {
    /**
     * Get available assessments
     * @returns {Promise} List of assessments
     */
    async getTypes() {
      return request('/assessment/types');
    },

    /**
     * Get assessment questions
     * @param {string} type - Assessment type
     * @param {string} language - Language code
     * @returns {Promise} Assessment questions
     */
    async getQuestions(type, language = 'zh') {
      return request(`/assessment/questions?type=${type}&language=${language}`);
    },

    /**
     * Submit assessment responses
     * @param {string} sessionId - Session ID
     * @param {string} type - Assessment type
     * @param {Object} responses - User responses
     * @returns {Promise} Assessment results
     */
    async submit(sessionId, type, responses) {
      return request('/assessment/submit', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          assessment_type: type,
          responses
        })
      });
    },

    /**
     * Get assessment results
     * @param {string} assessmentId - Assessment ID
     * @returns {Promise} Assessment results
     */
    async getResults(assessmentId) {
      return request(`/assessment/results/${assessmentId}`);
    }
  };

  // Doctor API
  const Doctor = {
    /**
     * Search doctors
     * @param {Object} params - Search parameters
     * @returns {Promise} List of doctors
     */
    async search(params = {}) {
      const queryString = new URLSearchParams(params).toString();
      return request(`/doctors/search?${queryString}`);
    },

    /**
     * Get all doctors
     * @returns {Promise} List of doctors
     */
    async getAll() {
      return request('/doctors');
    },

    /**
     * Get doctor by ID
     * @param {number} id - Doctor ID
     * @returns {Promise} Doctor details
     */
    async getById(id) {
      return request(`/doctors/${id}`);
    },

    /**
     * Get doctor specialties
     * @returns {Promise} List of specialties
     */
    async getSpecialties() {
      return request('/doctors/specialties');
    }
  };

  // Admin API
  const Admin = {
    /**
     * Admin login
     * @param {string} username - Username
     * @param {string} password - Password
     * @returns {Promise} Login result
     */
    async login(username, password) {
      return request('/admin/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      });
    },

    /**
     * Admin logout
     * @returns {Promise} Logout result
     */
    async logout() {
      return request('/admin/logout', { method: 'POST' });
    },

    /**
     * Get dashboard stats
     * @returns {Promise} Dashboard statistics
     */
    async getStats() {
      return request('/admin/stats');
    },

    /**
     * Get active sessions
     * @returns {Promise} List of active sessions
     */
    async getSessions() {
      return request('/admin/sessions');
    },

    /**
     * Terminate a session
     * @param {string} sessionId - Session ID to terminate
     * @returns {Promise} Result
     */
    async terminateSession(sessionId) {
      return request('/admin/sessions/terminate', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId })
      });
    },

    /**
     * Get system health
     * @returns {Promise} System health data
     */
    async getHealth() {
      return request('/admin/health');
    },

    /**
     * Get analytics data
     * @returns {Promise} Analytics data
     */
    async getAnalytics() {
      return request('/admin/analytics');
    },

    /**
     * Get system logs
     * @param {Object} filters - Log filters
     * @returns {Promise} System logs
     */
    async getLogs(filters = {}) {
      const queryString = new URLSearchParams(filters).toString();
      return request(`/admin/logs?${queryString}`);
    },

    // Doctor Management
    /**
     * Create a new doctor
     * @param {Object} doctorData - Doctor data
     * @returns {Promise} Created doctor
     */
    async createDoctor(doctorData) {
      return request('/admin/doctors', {
        method: 'POST',
        body: JSON.stringify(doctorData)
      });
    },

    /**
     * Update a doctor
     * @param {number} id - Doctor ID
     * @param {Object} doctorData - Updated doctor data
     * @returns {Promise} Updated doctor
     */
    async updateDoctor(id, doctorData) {
      return request(`/admin/doctors/${id}`, {
        method: 'PUT',
        body: JSON.stringify(doctorData)
      });
    },

    /**
     * Delete a doctor
     * @param {number} id - Doctor ID
     * @returns {Promise} Result
     */
    async deleteDoctor(id) {
      return request(`/admin/doctors/${id}`, {
        method: 'DELETE'
      });
    }
  };

  // Public API
  return {
    request,
    APIError,
    Chat,
    Assessment,
    Doctor,
    Admin
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API;
}
