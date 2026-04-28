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
      welcome_message: 'Welcome to PsyFind. I am your clinical assistant. How can I help you today?',
      
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
      whiteley_tab: 'Health Anxiety',
      phq9_tab: 'PHQ-9 (Depression)',
      gad7_tab: 'GAD-7 (Anxiety)',
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
      clinical_report: 'Clinical Report',
      possible_matches: 'Possible DSM-5 Matches',
      confidence: 'Confidence',
      recommended_specialists: 'Recommended Specialists',
      recommendations: 'Recommendations',
      
      // Loading
      analyzing: 'Analyzing your responses...',
      generating_report: 'Generating clinical report...',
      finding_specialists: 'Finding matching specialists...',
      
      // Errors
      error_network: 'Network error. Please try again.',
      error_generic: 'Something went wrong. Please try again.',
      
      // Disclaimer
      disclaimer_title: 'Important Disclaimer',
      disclaimer_text: 'This tool is for informational purposes only and does not provide medical diagnosis or treatment recommendations. Always consult with qualified mental health professionals for proper evaluation and care.',
      disclaimer_note_title: 'Please Note:',
      disclaimer_note_1: 'This assessment is a screening tool, not a diagnostic instrument',
      disclaimer_note_2: 'Results should be discussed with a qualified healthcare provider',
      disclaimer_note_3: 'If you\'re experiencing a mental health emergency, contact emergency services immediately',
      disclaimer_note_4: 'Your privacy is protected - no personal data is stored permanently',
      disclaimer_understand: 'I Understand',
      disclaimer_close: 'Close',
      
      // User Info Modal
      user_info_title: 'About You',
      user_info_description: 'Please provide some basic information to help us provide better assistance:',
      age_label: 'Age',
      age_placeholder: 'Enter your age',
      gender_label: 'Gender',
      select_gender: 'Select gender (optional)',
      male: 'Male',
      female: 'Female',
      non_binary: 'Non-binary',
      prefer_not_to_say: 'Prefer not to say',
      duration_label: 'How long have you been experiencing symptoms?',
      select_duration: 'Select duration',
      less_than_week: 'Less than a week',
      '1-2_weeks': '1-2 weeks',
      '2-4_weeks': '2-4 weeks',
      '1-3_months': '1-3 months',
      '3-6_months': '3-6 months',
      '6-12_months': '6-12 months',
      more_than_year: 'More than a year',
      privacy_note: 'Your information is kept private and secure. It\'s only used to provide personalized assistance.',
      continue: 'Continue',
      submit_assessment: 'Submit Assessment',
      assessment: 'Assessment',
      
      // Assessment Scale Labels
      several_days: 'Several days',
      more_than_half_days: 'More than half the days',
      nearly_every_day: 'Nearly every day',
      rarely: 'Rarely',
      sometimes: 'Sometimes',
      often: 'Often',
      very_often: 'Very Often',
      
      // Whiteley Questions
      whiteley_q1: 'Do you often worry about having a serious illness?',
      whiteley_q2: 'Do you frequently check your body for signs of illness?',
      whiteley_q3: 'Do health concerns cause you significant distress?',
      whiteley_q4: 'Do you seek reassurance from doctors or family about your health?',
      whiteley_q5: 'Do you avoid medical information because it triggers anxiety?',
      whiteley_q6: 'Do minor symptoms make you worry about serious diseases?',
      whiteley_q7: 'Do you believe you have a serious illness that doctors haven\'t found?',
      
      // PHQ-9 Questions
      phq9_q1: 'Little interest or pleasure in doing things',
      phq9_q2: 'Feeling down, depressed, or hopeless',
      phq9_q3: 'Trouble falling or staying asleep, or sleeping too much',
      phq9_q4: 'Feeling tired or having little energy',
      phq9_q5: 'Poor appetite or overeating',
      phq9_q6: 'Feeling bad about yourself or that you are a failure',
      phq9_q7: 'Trouble concentrating on things',
      phq9_q8: 'Moving or speaking slowly, or being fidgety/restless',
      phq9_q9: 'Thoughts that you would be better off dead or hurting yourself',
      
      // GAD-7 Questions
      gad7_q1: 'Feeling nervous, anxious, or on edge',
      gad7_q2: 'Not being able to stop or control worrying',
      gad7_q3: 'Worrying too much about different things',
      gad7_q4: 'Trouble relaxing',
      gad7_q5: 'Being so restless that it is hard to sit still',
      gad7_q6: 'Becoming easily annoyed or irritable',
      gad7_q7: 'Feeling afraid as if something awful might happen',
      
      // Validation Messages
      please_fill_required: 'Please fill in all required fields',
      thank_you_info: 'Thank you for providing your information',
      assessment_completed: 'Assessment completed successfully',
      failed_submit_assessment: 'Failed to submit assessment',
      
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
      welcome_message: '歡迎使用 PsyFind。我是您的臨床助理。請問今天有什麼我可以幫您的嗎？',
      
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
      whiteley_tab: '健康焦慮',
      phq9_tab: 'PHQ-9 (抑鬱)',
      gad7_tab: 'GAD-7 (焦慮)',
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
      clinical_report: '臨床報告',
      possible_matches: '可能的DSM-5匹配',
      confidence: '置信度',
      recommended_specialists: '推薦專科醫生',
      recommendations: '建議',
      
      // Loading
      analyzing: '正在分析您的回答...',
      generating_report: '正在生成臨床報告...',
      finding_specialists: '正在尋找匹配的專科醫生...',
      
      // Errors
      error_network: '網絡錯誤，請重試。',
      error_generic: '出現問題，請重試。',
      
      // Disclaimer
      disclaimer_title: '重要聲明',
      disclaimer_text: '此工具僅供參考，不提供醫療診斷或治療建議。請務必諮詢合格的心理健康專業人員進行適當的評估和護理。',
      disclaimer_note_title: '請注意：',
      disclaimer_note_1: '此評估是篩檢工具，而非診斷儀器',
      disclaimer_note_2: '結果應與合格的醫療保健提供者討論',
      disclaimer_note_3: '如果您正在經歷心理健康緊急情況，請立即聯繫緊急服務',
      disclaimer_note_4: '您的隱私受到保護 - 不會永久存儲個人數據',
      disclaimer_understand: '我明白',
      disclaimer_close: '關閉',
      
      // User Info Modal
      user_info_title: '關於您',
      user_info_description: '請提供一些基本信息，以便我們提供更好的協助：',
      age_label: '年齡',
      age_placeholder: '輸入您的年齡',
      gender_label: '性別',
      select_gender: '選擇性別（可選）',
      male: '男性',
      female: '女性',
      non_binary: '非二元性別',
      prefer_not_to_say: '不願透露',
      duration_label: '您出現這些症狀有多久了？',
      select_duration: '選擇持續時間',
      less_than_week: '少於一週',
      '1-2_weeks': '1-2 週',
      '2-4_weeks': '2-4 週',
      '1-3_months': '1-3 個月',
      '3-6_months': '3-6 個月',
      '6-12_months': '6-12 個月',
      more_than_year: '超過一年',
      privacy_note: '您的信息將被保密且安全。它僅用於提供個性化協助。',
      continue: '繼續',
      submit_assessment: '提交評估',
      assessment: '評估',
      
      // Assessment Scale Labels
      several_days: '幾天',
      more_than_half_days: '超過一半天數',
      nearly_every_day: '幾乎每天',
      rarely: '很少',
      sometimes: '有時',
      often: '經常',
      very_often: '非常經常',
      
      // Whiteley Questions
      whiteley_q1: '您是否經常擔心患有嚴重疾病？',
      whiteley_q2: '您是否經常檢查身體是否有疾病跡象？',
      whiteley_q3: '健康問題是否給您帶來重大困擾？',
      whiteley_q4: '您是否會向醫生或家人尋求健康保證？',
      whiteley_q5: '您是否因為會引發焦慮而迴避醫療資訊？',
      whiteley_q6: '輕微症狀是否會讓您擔心嚴重疾病？',
      whiteley_q7: '您是否認為自己患有醫生尚未發現的嚴重疾病？',
      
      // PHQ-9 Questions
      phq9_q1: '做事情的興趣或樂趣減少',
      phq9_q2: '感到沮喪、抑鬱或絕望',
      phq9_q3: '入睡困難、睡眠不安或睡眠過多',
      phq9_q4: '感到疲勞或沒有精力',
      phq9_q5: '食慾不振或暴飲暴食',
      phq9_q6: '對自己感覺不好，或認為自己是失敗者',
      phq9_q7: '難以集中注意力',
      phq9_q8: '動作或說話緩慢，或煩躁不安',
      phq9_q9: '認為死了會更好，或想傷害自己的念頭',
      
      // GAD-7 Questions
      gad7_q1: '感到緊張、焦慮或煩躁',
      gad7_q2: '無法停止或控制擔憂',
      gad7_q3: '對不同事情過度擔憂',
      gad7_q4: '難以放鬆',
      gad7_q5: '煩躁不安，難以靜坐',
      gad7_q6: '容易生氣或煩躁',
      gad7_q7: '感到害怕，好像會發生不好的事情',
      
      // Validation Messages
      please_fill_required: '請填寫所有必填欄位',
      thank_you_info: '感謝您提供您的信息',
      assessment_completed: '評估成功完成',
      failed_submit_assessment: '提交評估失敗',
      
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
