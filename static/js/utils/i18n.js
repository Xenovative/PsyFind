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
      // Page
      page_title: 'PsyFind - AI Mental Health Companion',

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
      gad7_q1: 'Feeling nervous, anxious or on edge',
      gad7_q2: 'Not being able to stop or control worrying',
      gad7_q3: 'Worrying too much about different things',
      gad7_q4: 'Trouble relaxing',
      gad7_q5: 'Being so restless that it is hard to sit still',
      gad7_q6: 'Becoming easily annoyed or irritable',
      gad7_q7: 'Feeling afraid as if something awful might happen',

      // ISI (Insomnia Severity Index) Questions
      isi_q1: 'Difficulty falling asleep',
      isi_q2: 'Difficulty staying asleep',
      isi_q3: 'Problems waking up too early',
      isi_q4: 'How satisfied/dissatisfied are you with your current sleep pattern?',
      isi_q5: 'How noticeable to others do you think your sleep problem is?',
      isi_q6: 'How worried/distressed are you about your current sleep problem?',
      isi_q7: 'To what extent do you consider your sleep problem to interfere with your daily functioning?',

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

      // MindEase New UI Elements
      nav_title: 'PsyFind',
      nav_subtitle: 'Your AI Mental Health Companion',
      nav_chat: 'Chat',
      nav_assessment: 'Self-Check',
      nav_journal: 'Journal',
      nav_resources: 'Resources',

      // Welcome Card
      welcome_greeting: 'Good evening',
      user_name: 'there',
      welcome_text: "No matter how your day went, this is a safe space where you can relax and share. Would you like to talk? I'm here to listen and accompany you.",
      stat_streak: 'Day Streak',
      stat_week: 'This Week',

      // Mood Selector
      mood_question: 'How are you feeling today?',
      mood_hint: 'Select the mood closest to you',
      mood_happy: 'Happy',
      mood_calm: 'Calm',
      mood_neutral: 'Neutral',
      mood_anxious: 'Anxious',
      mood_sad: 'Sad',
      mood_tired: 'Tired',
      mood_recorded: 'Mood recorded!',
      mood_message_happy: "I'm feeling happy today! 😄",
      mood_message_calm: "I'm feeling calm and peaceful. 😌",
      mood_message_neutral: "I'm feeling neutral today. 🤔",
      mood_message_anxious: "I'm feeling anxious and worried. 😟",
      mood_message_sad: "I'm feeling sad and down. 😢",
      mood_message_tired: "I'm feeling tired and exhausted. 😴",

      // Quick Actions
      quick_vent: 'I want to talk',
      quick_relax: 'Relaxation',
      quick_assessment: 'Take Assessment',
      send: 'Send',
      chat_status: 'Online • Always here for you',

      // Mental Status Widget
      widget_status: 'Mental Status',
      badge_ai: 'AI Analysis',
      ai_suggestion_label: 'AI Suggestion:',
      status_emotional: 'Emotional Health',
      status_attention: 'Needs Attention',
      status_stress: 'Stress Level',
      status_high: 'High',
      status_sleep: 'Sleep Quality',
      status_poor: 'Poor',
      status_social: 'Social Activity',
      status_good: 'Good',
      status_low: 'Low',
      status_excellent: 'Excellent',
      suggestion_text: 'Try completing the PHQ-9 assessment and practice breathing exercises before bed.',

      // Recommended Assessments
      widget_recommended: 'Recommended',
      label_priority: 'Priority',
      assessment_phq9: 'PHQ-9 Depression Scale',
      assessment_phq9_desc: 'Standard tool for depression screening',
      assessment_gad7: 'GAD-7 Anxiety Scale',
      assessment_gad7_desc: 'Standard tool for anxiety screening',
      assessment_whiteley: 'Whiteley-7 Health Anxiety',
      assessment_whiteley_desc: 'Health anxiety screening tool',
      assessment_sleep: 'Sleep Quality Scale',
      assessment_sleep_desc: 'Insomnia severity assessment',
      meta_questions: '9 questions • 3 min',
      meta_questions_short: '7 questions • 2 min',
      meta_questions_sleep: '10 questions • 4 min',
      action_start: 'Start →',

      // Emergency Card
      emergency_title: 'Emergency Hotlines',
      emergency_text: "If you're in distress or having thoughts of self-harm, please contact immediately:",
      hotline_1_name: 'Crisis Helpline',
      hotline_1_desc: '24/7 Free Support',
      hotline_2_name: 'Lifeline',
      hotline_2_desc: '24/7 Companionship',

      // Mood Chart
      chart_title: '7-Day Mood Trend',
      chart_subtitle: 'Your emotional fluctuations this week',
      chart_detail: 'View Details',
      day_mon: 'Mon',
      day_tue: 'Tue',
      day_wed: 'Wed',
      day_thu: 'Thu',
      day_fri: 'Fri',
      day_sat: 'Sat',
      day_today: 'Today',
      stat_avg: 'Average Score',
      stat_weekly: 'vs Last Week',
      stat_chats: 'Conversations',

      // Daily Practices
      practices_title: "Today's Recommended Practices",
      practice_breathing: '4-7-8 Breathing',
      practice_breathing_desc: 'Quick relaxation, improves sleep',
      practice_meditation: 'Guided Meditation',
      practice_meditation_desc: 'Relieves anxiety, returns to present',
      practice_journal: 'Gratitude Journal',
      practice_journal_desc: 'Record three things to be thankful for',
      practice_sound: 'Nature Sound Healing',
      practice_sound_desc: 'Rain, ocean waves, forest',
      time_3min: '3 min',
      time_5min: '5 min',
      time_10min: '10 min',
      time_15min: '15 min',

      // Privacy Banner
      privacy_title: 'Your conversations are completely private',
      privacy_text: 'We use end-to-end encryption. Your conversation content will never be shared with third parties.',
      cert_iso: '✓ ISO 27001 Certified',
      cert_hipaa: '✓ HIPAA Compliant',
      cert_encryption: '✓ End-to-end Encryption',
      cert_anonymous: '✓ Anonymous Chat',

      // Footer
      footer_copyright: '© 2025 PsyFind · Protecting your mental health with love and technology 💜',

      // Medical Disclaimer
      medical_disclaimer: 'This cannot replace professional medical diagnosis and treatment.',

      // Quick Intent Messages
      intent_vent: "I want to talk about what's been on my mind...",
      intent_relax: "I'd like to do a relaxation exercise.",
      intent_assessment: "I'd like to take a mental health assessment.",

      // AI Analysis Loading
      analyzing_chat: 'Analyzing conversation...',
      analysis_complete: 'Analysis complete',

      // Accessibility Labels (ARIA)
      aria_chat_interface: 'Chat interface',
      aria_sound: 'Sound',
      aria_more_options: 'More options',
      aria_add_emoji: 'Add emoji',
      aria_attach_file: 'Attach file',
      aria_voice_input: 'Voice input',
      aria_type_message: 'Type your message',
      aria_send_message: 'Send message',
      aria_quick_responses: 'Quick response options',
    },

    zh: {
      // Page
      page_title: 'PsyFind - AI心理健康夥伴',

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

      // ISI (失眠嚴重程度指數) Questions
      isi_q1: '入睡困難',
      isi_q2: '難以維持睡眠',
      isi_q3: '太早醒來的問題',
      isi_q4: '您對目前的睡眠模式有多滿意/不滿意？',
      isi_q5: '您認為您的睡眠問題對他人來說有多明顯？',
      isi_q6: '您對目前的睡眠問題有多擔心/困擾？',
      isi_q7: '您認為睡眠問題在多大程度上影響了您的日常功能？',

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

      // MindEase New UI Elements
      nav_title: 'PsyFind',
      nav_subtitle: '您的AI心理健康夥伴',
      nav_chat: '聊天',
      nav_assessment: '自我檢測',
      nav_journal: '日記',
      nav_resources: '資源',

      // Welcome Card
      welcome_greeting: '晚安',
      user_name: '朋友',
      welcome_text: '無論今天過得怎麼樣，這裡是一個安全的空間，您可以放鬆並分享。想聊聊嗎？我會在這裡傾聽和陪伴您。',
      stat_streak: '連續天數',
      stat_week: '本週心情',

      // Mood Selector
      mood_question: '今天感覺如何？',
      mood_hint: '選擇最接近您的心情',
      mood_happy: '開心',
      mood_calm: '平靜',
      mood_neutral: '一般',
      mood_anxious: '焦慮',
      mood_sad: '難過',
      mood_tired: '疲倦',
      mood_recorded: '心情已記錄！',
      mood_message_happy: '我今天感覺很開心！😄',
      mood_message_calm: '我感覺很平靜祥和。😌',
      mood_message_neutral: '我今天感覺還好。🤔',
      mood_message_anxious: '我感到焦慮和擔心。😟',
      mood_message_sad: '我感到難過和沮喪。😢',
      mood_message_tired: '我感到疲倦和筋疲力盡。😴',

      // Quick Actions
      quick_vent: '我想傾訴',
      quick_relax: '放鬆練習',
      quick_assessment: '進行評估',
      send: '發送',
      chat_status: '在線 • 隨時為您服務',

      // Mental Status Widget
      widget_status: '心理狀態',
      badge_ai: 'AI 分析',
      ai_suggestion_label: 'AI 建議：',
      status_emotional: '情緒健康',
      status_attention: '需要關注',
      status_stress: '壓力水平',
      status_high: '高',
      status_sleep: '睡眠品質',
      status_poor: '不佳',
      status_social: '社交活動',
      status_good: '良好',
      status_low: '低',
      status_excellent: '優秀',
      suggestion_text: '建議完成 PHQ-9 評估並在睡前練習呼吸運動。',

      // Recommended Assessments
      widget_recommended: '推薦評估',
      label_priority: '優先',
      assessment_phq9: 'PHQ-9 抑鬱量表',
      assessment_phq9_desc: '標準抑鬱篩檢工具',
      assessment_gad7: 'GAD-7 焦慮量表',
      assessment_gad7_desc: '標準焦慮篩檢工具',
      assessment_whiteley: 'Whiteley-7 健康焦慮',
      assessment_whiteley_desc: '健康焦慮篩檢工具',
      assessment_sleep: '睡眠品質量表',
      assessment_sleep_desc: '失眠嚴重程度評估',
      meta_questions: '9題 • 3分鐘',
      meta_questions_short: '7題 • 2分鐘',
      meta_questions_sleep: '10題 • 4分鐘',
      action_start: '開始 →',

      // Emergency Card
      emergency_title: '緊急求助熱線',
      emergency_text: '如果您處於危機中或有自我傷害的想法，請立即聯繫：',
      hotline_1_name: '生命線',
      hotline_1_desc: '24/7 免費支援',
      hotline_2_name: '張老師專線',
      hotline_2_desc: '24/7 陪伴傾聽',

      // Mood Chart
      chart_title: '7天心情趨勢',
      chart_subtitle: '您本週的情緒波動',
      chart_detail: '查看詳情',
      day_mon: '一',
      day_tue: '二',
      day_wed: '三',
      day_thu: '四',
      day_fri: '五',
      day_sat: '六',
      day_today: '今天',
      stat_avg: '平均分數',
      stat_weekly: '與上週相比',
      stat_chats: '對話次數',

      // Daily Practices
      practices_title: '今日推薦練習',
      practice_breathing: '4-7-8 呼吸法',
      practice_breathing_desc: '快速放鬆，改善睡眠',
      practice_meditation: '引導冥想',
      practice_meditation_desc: '緩解焦慮，回到當下',
      practice_journal: '感恩日記',
      practice_journal_desc: '記錄三件值得感謝的事',
      practice_sound: '自然聲音療癒',
      practice_sound_desc: '雨聲、海浪、森林',
      time_3min: '3 分鐘',
      time_5min: '5 分鐘',
      time_10min: '10 分鐘',
      time_15min: '15 分鐘',

      // Privacy Banner
      privacy_title: '您的對話完全保密',
      privacy_text: '我們使用端對端加密。您的對話內容絕不會與第三方分享。',
      cert_iso: '✓ ISO 27001 認證',
      cert_hipaa: '✓ HIPAA 合規',
      cert_encryption: '✓ 端對端加密',
      cert_anonymous: '✓ 匿名聊天',

      // Footer
      footer_copyright: '© 2025 PsyFind · 用愛與科技守護您的心理健康 💜',

      // Medical Disclaimer
      medical_disclaimer: '這不能取代專業的醫療診斷和治療。',

      // Quick Intent Messages
      intent_vent: '我想聊聊心裡在想什麼...',
      intent_relax: '我想做個放鬆練習。',
      intent_assessment: '我想做個心理健康評估。',

      // AI Analysis Loading
      analyzing_chat: '正在分析對話內容...',
      analysis_complete: '分析完成',

      // Accessibility Labels (ARIA)
      aria_chat_interface: '聊天介面',
      aria_sound: '聲音',
      aria_more_options: '更多選項',
      aria_add_emoji: '添加表情',
      aria_attach_file: '附加檔案',
      aria_voice_input: '語音輸入',
      aria_type_message: '輸入您的訊息',
      aria_send_message: '發送訊息',
      aria_quick_responses: '快速回覆選項',
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

    // Translate aria-labels
    document.querySelectorAll('[data-lang-aria]').forEach(element => {
      const key = element.getAttribute('data-lang-aria');
      if (translations[key]) {
        element.setAttribute('aria-label', translations[key]);
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
