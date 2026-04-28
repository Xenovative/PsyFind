/**
 * PsyFind Internationalization Module
 * Handles language switching and translation management
 */

const I18n = (function() {
  'use strict';

  let currentLanguage = 'zh';
  let translations = {};

  // Translation dictionaries
  const translationData = {
    en: {
      // Header
      title: 'PsyFind',
      subtitle: 'AI-Powered Psychiatric Analysis & Specialist Matching',
      
      // Chat
      chat_title: 'PsyFind Clinical Assistant',
      chat_subtitle: 'Your AI-powered mental health screening companion',
      chat_placeholder: 'Type your message here...',
      status_online: 'Online',
      status_typing: 'Typing...',
      
      // Quick responses
      quick_feeling_anxious: "I'm feeling anxious",
      quick_feeling_sad: "I'm feeling sad",
      quick_cant_sleep: "I can't sleep well",
      quick_stressed: "I'm very stressed",
      quick_assessment: 'Take an assessment',
      quick_find_doctor: 'Find a specialist',
      
      // Assessments
      whiteley_title: 'Whiteley 7 Health Anxiety Assessment',
      phq9_title: 'PHQ-9 Depression Assessment',
      gad7_title: 'GAD-7 Anxiety Assessment',
      assessment_instruction: 'Please answer the following questions honestly.',
      question: 'Question',
      of: 'of',
      not_at_all: 'Not at all',
      a_little: 'A little',
      moderately: 'Moderately',
      quite_a_bit: 'Quite a bit',
      extremely: 'Extremely',
      
      // Navigation
      previous: 'Previous',
      next: 'Next',
      submit: 'Submit',
      cancel: 'Cancel',
      close: 'Close',
      
      // Results
      analysis_results: 'Analysis Results',
      your_score: 'Your Score',
      severity: 'Severity',
      minimal: 'Minimal',
      mild: 'Mild',
      moderate: 'Moderate',
      severe: 'Severe',
      interpretation: 'Interpretation',
      possible_matches: 'Possible DSM-5 Matches',
      confidence: 'Confidence',
      recommended_specialists: 'Recommended Specialists',
      clinical_report: 'Clinical Report',
      recommendations: 'Recommendations',
      
      // Loading
      analyzing: 'Analyzing your responses...',
      generating_report: 'Generating clinical report...',
      finding_specialists: 'Finding matching specialists...',
      
      // Errors
      error_network: 'Network error. Please try again.',
      error_generic: 'Something went wrong. Please try again.',
      
      // Admin
      admin_title: 'Admin Dashboard',
      nav_dashboard: 'Dashboard',
      nav_analytics: 'Analytics',
      nav_sessions: 'Active Sessions',
      nav_health: 'System Health',
      nav_management: 'Management',
      nav_assessments: 'Assessments',
      nav_clinical: 'Clinical Records',
      nav_doctors: 'Doctors',
      nav_reports: 'Reports',
      nav_settings: 'Settings',
      nav_system: 'System',
      nav_logs: 'System Logs',
      nav_backup: 'Backup',
      
      // Admin stats
      active_sessions: 'Active Sessions',
      total_assessments: 'Total Assessments',
      memory_usage: 'Memory Usage',
      system_uptime: 'System Uptime',
      
      // Actions
      refresh: 'Refresh',
      logout: 'Logout',
      add_doctor: 'Add Doctor',
      search: 'Search',
      edit: 'Edit',
      delete: 'Delete',
      save: 'Save',
      
      // Form labels
      name: 'Name',
      specialty: 'Specialty',
      subspecialty: 'Subspecialty',
      phone: 'Phone',
      email: 'Email',
      location: 'Location',
      languages: 'Languages',
      experience: 'Experience',
      education: 'Education',
      certifications: 'Certifications',
      availability: 'Availability',
      consultation_fee: 'Consultation Fee',
      notes: 'Notes',
      
      // Placeholders
      search_by_name: 'Search by name, specialty, or location...',
      all_specialties: 'All Specialties',
      all_types: 'All Types',
      
      // Loading states
      loading: 'Loading...',
      loading_sessions: 'Loading sessions...',
      loading_health_data: 'Loading health data...',
      loading_analytics: 'Loading analytics...',
      loading_assessment_data: 'Loading assessment data...',
      loading_recent_assessments: 'Loading recent assessments...',
      loading_clinical_sessions: 'Loading clinical sessions...',
      loading_clinical_reports: 'Loading clinical reports...',
      
      // System status
      status_online: 'Online',
      status_offline: 'Offline',
      status_degraded: 'Degraded',
    },
    
    zh: {
      // Header
      title: 'PsyFind',
      subtitle: 'AI驅動精神科分析與專科醫生配對',
      
      // Chat
      chat_title: 'PsyFind 臨床助理',
      chat_subtitle: '您的AI心理健康篩查夥伴',
      chat_placeholder: '在此輸入您的訊息...',
      status_online: '在線',
      status_typing: '輸入中...',
      
      // Quick responses
      quick_feeling_anxious: '我感到焦慮',
      quick_feeling_sad: '我感到悲傷',
      quick_cant_sleep: '我睡不好',
      quick_stressed: '我壓力很大',
      quick_assessment: '進行評估',
      quick_find_doctor: '尋找專科醫生',
      
      // Assessments
      whiteley_title: 'Whiteley 7 健康焦慮評估',
      phq9_title: 'PHQ-9 抑鬱症評估',
      gad7_title: 'GAD-7 焦慮症評估',
      assessment_instruction: '請誠實回答以下問題。',
      question: '問題',
      of: '/',
      not_at_all: '完全沒有',
      a_little: '有一點',
      moderately: '中等',
      quite_a_bit: '相當多',
      extremely: '非常嚴重',
      
      // Navigation
      previous: '上一題',
      next: '下一題',
      submit: '提交',
      cancel: '取消',
      close: '關閉',
      
      // Results
      analysis_results: '分析結果',
      your_score: '您的分數',
      severity: '嚴重程度',
      minimal: '輕微',
      mild: '輕度',
      moderate: '中度',
      severe: '重度',
      interpretation: '解讀',
      possible_matches: '可能的DSM-5匹配',
      confidence: '置信度',
      recommended_specialists: '推薦專科醫生',
      clinical_report: '臨床報告',
      recommendations: '建議',
      
      // Loading
      analyzing: '正在分析您的回答...',
      generating_report: '正在生成臨床報告...',
      finding_specialists: '正在尋找匹配的專科醫生...',
      
      // Errors
      error_network: '網絡錯誤，請重試。',
      error_generic: '出現問題，請重試。',
      
      // Admin
      admin_title: '管理員儀表板',
      nav_dashboard: '儀表板',
      nav_analytics: '分析',
      nav_sessions: '活動會話',
      nav_health: '系統健康',
      nav_management: '管理',
      nav_assessments: '評估',
      nav_clinical: '臨床記錄',
      nav_doctors: '醫生',
      nav_reports: '報告',
      nav_settings: '設置',
      nav_system: '系統',
      nav_logs: '系統日誌',
      nav_backup: '備份',
      
      // Admin stats
      active_sessions: '活動會話',
      total_assessments: '總評估數',
      memory_usage: '內存使用',
      system_uptime: '系統運行時間',
      
      // Actions
      refresh: '刷新',
      logout: '登出',
      add_doctor: '添加醫生',
      search: '搜索',
      edit: '編輯',
      delete: '刪除',
      save: '保存',
      
      // Form labels
      name: '姓名',
      specialty: '專科',
      subspecialty: '副專科',
      phone: '電話',
      email: '電郵',
      location: '地點',
      languages: '語言',
      experience: '經驗',
      education: '教育背景',
      certifications: '認證',
      availability: '可預約時間',
      consultation_fee: '診症費用',
      notes: '備註',
      
      // Placeholders
      search_by_name: '按姓名、專科或地點搜索...',
      all_specialties: '所有專科',
      all_types: '所有類型',
      
      // Loading states
      loading: '加載中...',
      loading_sessions: '正在加載會話...',
      loading_health_data: '正在加載健康數據...',
      loading_analytics: '正在加載分析數據...',
      loading_assessment_data: '正在加載評估數據...',
      loading_recent_assessments: '正在加載近期評估...',
      loading_clinical_sessions: '正在加載臨床會話...',
      loading_clinical_reports: '正在加載臨床報告...',
      
      // System status
      status_online: '在線',
      status_offline: '離線',
      status_degraded: '性能下降',
    }
  };

  /**
   * Initialize the i18n module
   * @param {string} defaultLang - Default language code
   */
  function init(defaultLang = 'zh') {
    currentLanguage = defaultLang;
    translations = translationData[defaultLang] || translationData['en'];
    applyTranslations();
  }

  /**
   * Switch to a different language
   * @param {string} lang - Language code ('en' or 'zh')
   */
  function switchLanguage(lang) {
    if (!translationData[lang]) {
      console.warn(`Language ${lang} not supported`);
      return;
    }

    currentLanguage = lang;
    translations = translationData[lang];
    
    // Update language toggle buttons
    document.querySelectorAll('.lang-btn, .admin-header__lang-btn').forEach(btn => {
      btn.classList.remove('active', 'admin-header__lang-btn--active');
      if (btn.textContent.toLowerCase().includes(lang === 'zh' ? '中' : 'en')) {
        btn.classList.add('active', 'admin-header__lang-btn--active');
      }
    });

    applyTranslations();

    // Store preference
    localStorage.setItem('psyfind-language', lang);
  }

  /**
   * Apply translations to all elements with data-lang attribute
   */
  function applyTranslations() {
    // Translate text content
    document.querySelectorAll('[data-lang]').forEach(element => {
      const key = element.getAttribute('data-lang');
      if (translations[key]) {
        element.textContent = translations[key];
      }
    });

    // Translate placeholders
    document.querySelectorAll('[data-lang-placeholder]').forEach(element => {
      const key = element.getAttribute('data-lang-placeholder');
      if (translations[key]) {
        element.placeholder = translations[key];
      }
    });
  }

  /**
   * Get a translation by key
   * @param {string} key - Translation key
   * @param {Object} params - Optional parameters for interpolation
   * @returns {string} Translated text
   */
  function t(key, params = {}) {
    let text = translations[key] || translationData['en'][key] || key;
    
    // Simple parameter interpolation
    Object.keys(params).forEach(param => {
      text = text.replace(`{${param}}`, params[param]);
    });
    
    return text;
  }

  /**
   * Get the current language
   * @returns {string} Current language code
   */
  function getCurrentLanguage() {
    return currentLanguage;
  }

  /**
   * Load saved language preference
   */
  function loadSavedLanguage() {
    const saved = localStorage.getItem('psyfind-language');
    if (saved && translationData[saved]) {
      switchLanguage(saved);
    }
  }

  // Public API
  return {
    init,
    switchLanguage,
    t,
    getCurrentLanguage,
    loadSavedLanguage,
    translations: translationData
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = I18n;
}
