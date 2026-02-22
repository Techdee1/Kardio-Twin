const en: Record<string, string> = {
    // Navbar
    'nav.howItWorks': 'How It Works',
    'nav.security': 'Security',
    'nav.impact': 'Our Impact',
    'nav.getStarted': 'Get Started',

    // Landing hero
    'hero.title1': "Your Heart's",
    'hero.title2': 'Early Warning',
    'hero.title3': 'System',
    'hero.subtitle': 'Real-time cardiometabolic risk scoring designed to prevent heart disease before it starts. Get instant AI-driven assessments directly on WhatsApp.',
    'hero.placeholder': 'WhatsApp Number',
    'hero.starting': 'Starting...',
    'hero.startScreening': 'Start Screening',
    'hero.hipaa': 'HIPAA Compliant',
    'hero.encrypted': 'End-to-End Encrypted',
    'hero.enterPhone': 'Please enter your WhatsApp number.',

    // Hero card
    'hero.activeMonitoring': 'Active Monitoring',
    'hero.cardioAnalysis': 'CardioTwin Analysis',
    'hero.optimized': 'Optimized',
    'hero.healthScore': 'Health Score',

    // How it works
    'howItWorks.tag': 'Patient-Centric Care',
    'howItWorks.title': 'Your Health, Simplified',
    'howItWorks.subtitle': 'We transform complex clinical data into simple, actionable steps delivered right to your phone.',
    'howItWorks.b1Title': 'Holistic Monitoring',
    'howItWorks.b1Desc': 'Seamlessly connect your wearables and lab results for a complete picture of your heart health without the medical jargon.',
    'howItWorks.b2Title': 'Personalized Insights',
    'howItWorks.b2Desc': 'Receive a clear, easy-to-understand health score that tells you exactly where you stand and what it means for your future.',
    'howItWorks.b3Title': 'WhatsApp Guidance',
    'howItWorks.b3Desc': 'Get gentle nudges, diet tips, and activity reminders directly on WhatsApp. Like having a personal cardiologist in your pocket.',

    // Security section
    'security.title1': 'Your Health Data is',
    'security.title2': 'Sovereign',
    'security.subtitle': 'We believe health data privacy is a fundamental right. CardioTwin AI utilizes enterprise-grade encryption to ensure only you and your chosen providers can access your heart twin profile.',
    'security.bankLevel': 'Bank-Level Security',
    'security.bankLevelDesc': 'AES-256 bit encryption for all your health data.',
    'security.zeroThirdParty': 'Zero Third-Party',
    'security.zeroThirdPartyDesc': 'Your data is never sold to insurance companies.',
    'security.privacyProtocol': 'Privacy Protocol',
    'security.hipaaCompliant': 'HIPAA Compliant',
    'security.e2e': 'End-to-End Encryption',
    'security.active': 'ACTIVE',
    'security.testimonial': '"CardioTwin AI has transformed how we handle preventive patient data in our clinic securely and transparently."',
    'security.testimonialAuthor': '— Dr. Amara Okafor, Cardiologist',

    // CTA section
    'cta.title1': 'Start Your Journey to a',
    'cta.title2': 'Stronger Heart',
    'cta.title3': 'Today',
    'cta.subtitle': 'Join thousands of people who are taking proactive control of their cardiovascular health with simple, personalized guidance.',
    'cta.terms': 'By starting, you agree to our',
    'cta.termsLink': 'Terms of Service',
    'cta.and': 'and',
    'cta.privacyLink': 'Privacy Policy',

    // Footer
    'footer.privacy': 'Privacy Policy',
    'footer.terms': 'Terms of Service',
    'footer.contact': 'Contact Support',
    'footer.api': 'API Docs',
    'footer.copyright': '© {year} CardioTwin AI Healthcare Solutions. All rights reserved.',

    // Dashboard header
    'dash.liveStatus': 'Live Status',
    'dash.digitalTwin': 'Digital Twin',
    'dash.calibrating': 'Calibrating',
    'dash.liveMonitoring': 'Live Monitoring',
    'dash.session': 'Session',
    'dash.realtimeSync': 'Real-time Hardware Sync',
    'dash.getAiAdvice': 'Get AI Advice',
    'dash.loading': 'Loading...',
    'dash.healthScore': 'Health Score',

    // Dashboard calibration
    'dash.analyzingBaseline': 'Analyzing Baseline Metrics',
    'dash.gatheringSensor': 'Gathering sensor data to establish a personalized cardiovascular baseline.',
    'dash.initializing': 'Initializing',

    // Dashboard analysis
    'dash.analysisStatus': 'Real-time Analysis Status',
    'dash.statusOptimal': 'Biometric patterns indicate optimal recovery. No arrhythmias or stress triggers detected in current session.',
    'dash.statusMild': 'Mild strain detected in current biomarkers. Monitor hydration and rest recommended.',
    'dash.statusWarning': 'Warning levels reached. Immediate attention to cardiovascular state is advised.',
    'dash.activeZone': 'Active Zone',

    // Settings
    'settings.title': 'Settings',
    'settings.language': 'Language',
    'settings.languageDesc': 'Choose your preferred language for the application.',
    'settings.configTitle': 'Settings Configuration',
    'settings.configDesc': 'System configuration view coming soon.',

    // Sidebar
    'sidebar.overview': 'Overview',
    'sidebar.projection': 'What-If',
    'sidebar.history': 'History',
    'sidebar.settings': 'Settings',
    'sidebar.exit': 'Exit Dashboard',

    // Nudge panel
    'nudge.aiInsight': 'AI Insight',
    'nudge.quickActions': 'Quick Actions',
    'nudge.deepBreathing': 'Deep Breathing',
    'nudge.takeWalk': 'Take a Walk',
    'nudge.stayHydrated': 'Stay Hydrated',
    'nudge.mindfulBreak': 'Mindful Break',
    'nudge.gettingAdvice': 'Getting Advice...',
    'nudge.refreshAdvice': 'Refresh Advice',

    // Projection panel
    'projection.title': 'What-If Projection',
    'projection.subtitle': 'See your future health trajectory',
    'projection.days': 'days',
    'projection.today': 'Today',
    'projection.projected': 'Projected',
    'projection.loading': 'Calculating projection...',
    'projection.retry': 'Try Again',
    'projection.improving': 'Trending Positive',
    'projection.declining': 'Needs Attention',
    'projection.scoreChange': 'Score change',
    'projection.hrChange': 'Resting HR change',
    'projection.riskChange': 'Risk category',
    'projection.scenarioLabel': 'Scenario (Optional)',
    'projection.scenarioPlaceholder': 'e.g., "What if I stop taking sugar"',
    'projection.analyze': 'Analyze',
    'projection.scenarioHint': 'AI will analyze this lifestyle change',

    // History chart
    'history.title': 'Session History',
    'history.subtitle': 'Live updates every 10s',
    'history.score': 'Score',
    'history.heartRate': 'Heart Rate',
    'history.hrv': 'HRV',
    'history.spo2': 'SpO₂',
    'history.loading': 'Loading history...',
    'history.retry': 'Try Again',
    'history.noData': 'No history data yet',
    'history.noDataHint': 'Data will appear as readings are collected',
    'history.zoneGreen': 'Thriving',
    'history.zoneYellow': 'Mild Strain',
    'history.zoneOrange': 'Elevated',
    'history.zoneRed': 'Critical',

    // Demo page
    'demo.subtitle': "Your Heart's Early Warning System",
    'demo.alert': '⚠️ ALERT — Risk Detected! Check WhatsApp.',
    'demo.scoreLabel': 'CardioTwin Score',
    'demo.disclaimer': 'Wellness screening tool only — not a medical diagnosis',
    'demo.thriving': 'Thriving',
    'demo.mildStrain': 'Mild Strain',
    'demo.elevatedRisk': 'Elevated Risk',
    'demo.criticalStrain': 'Critical Strain',

    // Language names
    'lang.en': 'English',
    'lang.yo': 'Yoruba',
    'lang.ha': 'Hausa',
    'lang.ig': 'Igbo',
};

export default en;
