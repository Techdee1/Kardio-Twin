import { Shield, Lock, Verified, ArrowRight, Heart, AlertTriangle, TrendingUp, Zap, Smartphone, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { api } from '../services/api';
import { useLanguage } from '../i18n/LanguageContext';

export default function LandingPage() {
    const navigate = useNavigate();
    const [phone, setPhone] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showContacts, setShowContacts] = useState(false);
    const [caregiverName, setCaregiverName] = useState('');
    const [caregiverPhone, setCaregiverPhone] = useState('');
    const [medName, setMedName] = useState('');
    const [medPhone, setMedPhone] = useState('');
    const { t } = useLanguage();

    const handleStart = async () => {
        if (!phone.trim()) {
            alert(t('hero.enterPhone'));
            return;
        }
        setIsLoading(true);
        try {
            const sessionId = `session-${Date.now()}`;
            const userPhone = `+234${phone.trim()}`;
            await api.startSession({
                session_id: sessionId,
                user_phone: userPhone,
                caregiver_phone: caregiverPhone ? `+234${caregiverPhone.trim()}` : undefined,
                caregiver_name: caregiverName || undefined,
                medical_professional_phone: medPhone ? `+234${medPhone.trim()}` : undefined,
                medical_professional_name: medName || undefined,
            });
            navigate(`/dashboard?session_id=${sessionId}`);
        } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            console.error(`[CardioTwin] Session creation failed: ${message}. Falling back to demo session.`);
            navigate(`/dashboard?session_id=session-${Date.now()}`);
        } finally {
            setIsLoading(false);
        }
    };

    const renderEmergencyContacts = () => (
        <div className="mt-3 space-y-3 bg-white/60 border border-primary/15 rounded-xl p-4">
            <p className="text-[11px] text-background-dark/60 font-medium">{t('caregiver.subtitle')}</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <input type="text" placeholder={t('caregiver.name')} value={caregiverName} onChange={e => setCaregiverName(e.target.value)} className="px-3 py-2 rounded-lg bg-white border border-primary/15 text-sm font-medium text-background-dark placeholder:text-background-dark/40 focus:outline-none focus:ring-2 focus:ring-primary/20" />
                <input type="tel" placeholder={t('caregiver.phone')} value={caregiverPhone} onChange={e => setCaregiverPhone(e.target.value)} className="px-3 py-2 rounded-lg bg-white border border-primary/15 text-sm font-medium text-background-dark placeholder:text-background-dark/40 focus:outline-none focus:ring-2 focus:ring-primary/20" />
                <input type="text" placeholder={t('caregiver.medName')} value={medName} onChange={e => setMedName(e.target.value)} className="px-3 py-2 rounded-lg bg-white border border-primary/15 text-sm font-medium text-background-dark placeholder:text-background-dark/40 focus:outline-none focus:ring-2 focus:ring-primary/20" />
                <input type="tel" placeholder={t('caregiver.medPhone')} value={medPhone} onChange={e => setMedPhone(e.target.value)} className="px-3 py-2 rounded-lg bg-white border border-primary/15 text-sm font-medium text-background-dark placeholder:text-background-dark/40 focus:outline-none focus:ring-2 focus:ring-primary/20" />
            </div>
        </div>
    );

    return (
        <>
            {/* ── HERO ── */}
            <main className="relative overflow-hidden bg-white">
                {/* Background gradients */}
                <div className="absolute inset-0 -z-10 pointer-events-none">
                    <div className="absolute top-0 right-0 w-[60%] h-[70%] bg-[radial-gradient(ellipse_at_top_right,rgba(33,196,93,0.08),transparent_70%)]" />
                    <div className="absolute bottom-0 left-0 w-[40%] h-[50%] bg-[radial-gradient(ellipse_at_bottom_left,rgba(33,196,93,0.05),transparent_70%)]" />
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20 sm:pt-24 sm:pb-28 lg:pt-28 lg:pb-32">
                    <div className="grid lg:grid-cols-2 gap-14 lg:gap-20 items-center">

                        {/* Left: Copy */}
                        <div className="flex flex-col gap-7">
                            <div className="inline-flex items-center gap-2 bg-primary/10 border border-primary/20 text-primary text-xs font-bold px-3.5 py-1.5 rounded-full w-fit">
                                <span className="relative flex h-1.5 w-1.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-primary" />
                                </span>
                                AI-Powered Cardiac Monitoring
                            </div>

                            <div className="space-y-4">
                                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.08] tracking-tight text-background-dark">
                                    Your Heart,<br />
                                    <span className="text-primary italic font-serif font-normal">Understood</span><br />
                                    in Real Time
                                </h1>
                                <p className="text-base sm:text-lg text-background-dark/65 max-w-lg leading-relaxed">
                                    CardioTwin creates a personalised digital twin of your cardiovascular system — detecting risk before symptoms appear, and guiding you to act at the right moment.
                                </p>
                            </div>

                            {/* Phone input */}
                            <div id="start" className="bg-white border border-primary/20 p-2 rounded-2xl max-w-lg shadow-[0_8px_40px_-8px_rgba(33,196,93,0.15)] ring-1 ring-background-dark/5">
                                <div className="flex flex-col sm:flex-row gap-2">
                                    <div className="flex items-center bg-background-light rounded-xl flex-1 px-4">
                                        <div className="flex items-center gap-2 text-sm font-semibold pr-3 border-r border-primary/20 text-background-dark shrink-0">
                                            <span className="text-xl">🇳🇬</span>
                                            <span>+234</span>
                                        </div>
                                        <input
                                            type="tel"
                                            className="bg-transparent border-none focus:outline-none w-full text-background-dark placeholder:text-background-dark/40 ml-3 py-3.5 font-medium text-sm"
                                            placeholder={t('hero.placeholder')}
                                            value={phone}
                                            onChange={(e) => setPhone(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                                        />
                                    </div>
                                    <button
                                        onClick={handleStart}
                                        disabled={isLoading}
                                        className="bg-primary hover:bg-primary/90 active:scale-95 text-white px-7 py-3.5 rounded-xl font-bold transition-all flex items-center justify-center gap-2 whitespace-nowrap cursor-pointer shadow-lg shadow-primary/25 disabled:opacity-50 text-sm"
                                    >
                                        {isLoading ? (
                                            <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Starting…</span>
                                        ) : (
                                            <>{t('hero.startScreening')} <ArrowRight className="w-4 h-4" /></>
                                        )}
                                    </button>
                                </div>
                            </div>

                            {/* Emergency contacts */}
                            <div className="max-w-lg -mt-3">
                                <button
                                    onClick={() => setShowContacts(!showContacts)}
                                    className="text-xs font-semibold text-primary/70 hover:text-primary transition-colors cursor-pointer flex items-center gap-1"
                                >
                                    {showContacts ? '▾' : '▸'} {t('caregiver.title')}
                                </button>
                                {showContacts && renderEmergencyContacts()}
                            </div>

                            {/* Trust badges */}
                            <div className="flex flex-wrap items-center gap-4 text-xs text-background-dark/55 font-semibold -mt-2">
                                <div className="flex items-center gap-1.5"><Verified className="w-3.5 h-3.5 text-primary" /> HIPAA-aligned</div>
                                <div className="flex items-center gap-1.5"><Lock className="w-3.5 h-3.5 text-primary" /> End-to-end encrypted</div>
                                <div className="flex items-center gap-1.5"><Shield className="w-3.5 h-3.5 text-primary" /> No data sold</div>
                            </div>
                        </div>

                        {/* Right: Hero image with overlaid metric cards */}
                        <div className="relative hidden lg:block">
                            {/* Glow behind image */}
                            <div className="absolute -inset-6 bg-primary/8 blur-3xl rounded-full" />

                            {/* Main image — 800×450 source (16:9), display as 4:3 cropped from top */}
                            <div className="relative rounded-3xl overflow-hidden aspect-[4/3] shadow-[0_32px_64px_-16px_rgba(0,0,0,0.15)]">
                                <img
                                    src="/images/hero.jpg"
                                    alt="Healthcare professional monitoring cardiac data"
                                    className="w-full h-full object-cover object-top"
                                    onError={(e) => {
                                        e.currentTarget.style.display = 'none';
                                        e.currentTarget.parentElement!.style.background = 'linear-gradient(135deg, #e8f5ee 0%, #d1f0e0 50%, #c5ecda 100%)';
                                    }}
                                />
                                {/* Subtle overlay for card legibility */}
                                <div className="absolute inset-0 bg-gradient-to-t from-background-dark/40 via-transparent to-transparent" />
                            </div>

                            {/* Floating metric: CardioTwin Score */}
                            <div className="absolute top-6 -left-6 bg-white rounded-2xl shadow-xl border border-primary/10 p-4 min-w-[160px]">
                                <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40 mb-1">CardioTwin Score</p>
                                <div className="flex items-end gap-1.5">
                                    <span className="text-3xl font-black text-emerald-600">94</span>
                                    <span className="text-xs font-bold text-emerald-500 mb-1 flex items-center gap-0.5">
                                        <TrendingUp className="w-3 h-3" /> +3
                                    </span>
                                </div>
                                <div className="mt-2 h-1.5 bg-background-light rounded-full overflow-hidden">
                                    <div className="h-full bg-primary rounded-full" style={{ width: '94%' }} />
                                </div>
                                <span className="text-[9px] font-bold text-emerald-600 uppercase tracking-wider mt-1 block">● Thriving</span>
                            </div>

                            {/* Floating metric: Alert */}
                            <div className="absolute bottom-12 -right-5 bg-white rounded-2xl shadow-xl border border-primary/10 p-4 min-w-[180px]">
                                <div className="flex items-center gap-2 mb-2">
                                    <div className="w-7 h-7 rounded-full bg-emerald-50 flex items-center justify-center">
                                        <Heart className="w-3.5 h-3.5 text-primary" />
                                    </div>
                                    <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40">Live Vitals</p>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
                                    <div><p className="text-[9px] text-background-dark/40 font-bold">HR</p><p className="text-sm font-black text-background-dark">72 <span className="text-[9px] font-semibold text-background-dark/40">bpm</span></p></div>
                                    <div><p className="text-[9px] text-background-dark/40 font-bold">HRV</p><p className="text-sm font-black text-background-dark">52 <span className="text-[9px] font-semibold text-background-dark/40">ms</span></p></div>
                                    <div><p className="text-[9px] text-background-dark/40 font-bold">SpO₂</p><p className="text-sm font-black text-background-dark">98 <span className="text-[9px] font-semibold text-background-dark/40">%</span></p></div>
                                    <div><p className="text-[9px] text-background-dark/40 font-bold">Temp</p><p className="text-sm font-black text-background-dark">36.6 <span className="text-[9px] font-semibold text-background-dark/40">°C</span></p></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>

            {/* ── THE PROBLEM ── */}
            <section id="problem" className="relative bg-background-dark py-20 sm:py-28 overflow-hidden">
                {/* Decorative ECG line */}
                <div className="absolute inset-0 pointer-events-none opacity-5">
                    <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1200 200">
                        <path d="M0,100 L200,100 L250,30 L280,160 L310,10 L340,180 L370,100 L600,100 L650,30 L680,160 L710,10 L740,180 L770,100 L1200,100"
                            fill="none" stroke="#21c45d" strokeWidth="3" />
                    </svg>
                </div>

                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="text-center mb-14">
                        <span className="inline-block text-primary font-bold text-xs uppercase tracking-[0.2em] mb-4 bg-primary/10 px-3 py-1.5 rounded-full">The Crisis</span>
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
                            Cardiac Disease is Silently<br className="hidden sm:block" />
                            <span className="text-primary italic font-serif font-normal"> Killing Africans</span>
                        </h2>
                        <p className="mt-4 text-white/55 max-w-2xl mx-auto text-base sm:text-lg font-light leading-relaxed">
                            Cardiovascular disease is now the leading cause of death in sub-Saharan Africa — yet most people have no way to detect warning signs before a crisis strikes.
                        </p>
                    </div>

                    {/* Stat cards */}
                    <div className="grid sm:grid-cols-3 gap-5 mb-16">
                        {[
                            {
                                stat: '1 in 3',
                                label: 'Nigerians live with hypertension',
                                sub: 'Most are undiagnosed and untreated',
                                icon: AlertTriangle,
                                color: 'text-rose-400',
                                bg: 'bg-rose-500/10',
                            },
                            {
                                stat: '80%',
                                label: 'of cardiac deaths are preventable',
                                sub: 'With early detection and timely action',
                                icon: Heart,
                                color: 'text-primary',
                                bg: 'bg-primary/10',
                            },
                            {
                                stat: '1 doctor',
                                label: 'per 2,500+ patients',
                                sub: 'Leaving most without access to cardiac care',
                                icon: Users,
                                color: 'text-amber-400',
                                bg: 'bg-amber-500/10',
                            },
                        ].map(({ stat, label, sub, icon: Icon, color, bg }) => (
                            <div key={stat} className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-sm hover:bg-white/8 transition-colors">
                                <div className={`w-10 h-10 rounded-xl ${bg} flex items-center justify-center mb-4`}>
                                    <Icon className={`w-5 h-5 ${color}`} />
                                </div>
                                <p className={`text-3xl sm:text-4xl font-black mb-1 ${color}`}>{stat}</p>
                                <p className="text-white font-bold text-sm mb-1">{label}</p>
                                <p className="text-white/45 text-xs font-medium leading-relaxed">{sub}</p>
                            </div>
                        ))}
                    </div>

                    {/* Problem image strip — ecg.png is 760×552 (4:3), contain so it stays sharp */}
                    <div className="relative rounded-2xl overflow-hidden bg-background-dark" style={{ aspectRatio: '760/552', maxHeight: '360px' }}>
                        <img
                            src="/images/ecg.png"
                            alt="ECG heartbeat monitor readout"
                            className="w-full h-full object-contain"
                            onError={(e) => { e.currentTarget.style.display = 'none'; }}
                        />
                        {/* Fallback ECG graphic if image missing */}
                        <div className="absolute inset-0 flex items-center justify-center bg-white/5 border border-white/10 rounded-2xl">
                            <svg className="w-full h-24 text-primary/40" preserveAspectRatio="xMidYMid meet" viewBox="0 0 800 100">
                                <path d="M0,50 L150,50 L180,20 L200,80 L220,10 L240,90 L260,50 L400,50 L430,20 L450,80 L470,10 L490,90 L510,50 L700,50 L730,20 L750,80 L770,10 L790,90 L800,50"
                                    fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" />
                            </svg>
                            <div className="absolute inset-0 bg-gradient-to-r from-background-dark via-transparent to-background-dark" />
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-r from-background-dark/80 via-background-dark/20 to-background-dark/80" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <p className="text-white/80 text-lg sm:text-2xl font-bold italic font-serif text-center px-4">
                                "Most cardiac events give warnings.<br className="hidden sm:block" /> CardioTwin is trained to hear them."
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── HOW IT WORKS ── */}
            <section id="how-it-works" className="py-20 sm:py-28 bg-background-light relative">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-14">
                        <span className="inline-block text-primary font-bold text-xs uppercase tracking-[0.2em] mb-4 bg-primary/10 px-3 py-1.5 rounded-full">{t('howItWorks.tag')}</span>
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-background-dark tracking-tight">{t('howItWorks.title')}</h2>
                        <p className="mt-3 text-background-dark/60 max-w-2xl mx-auto text-base sm:text-lg font-light leading-relaxed">
                            {t('howItWorks.subtitle')}
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
                        {[
                            {
                                num: '01',
                                icon: Smartphone,
                                title: t('howItWorks.b1Title'),
                                desc: t('howItWorks.b1Desc'),
                                accent: 'from-emerald-50 to-white border-emerald-100',
                            },
                            {
                                num: '02',
                                icon: TrendingUp,
                                title: t('howItWorks.b2Title'),
                                desc: t('howItWorks.b2Desc'),
                                accent: 'from-sky-50 to-white border-sky-100',
                            },
                            {
                                num: '03',
                                icon: Zap,
                                title: t('howItWorks.b3Title'),
                                desc: t('howItWorks.b3Desc'),
                                accent: 'from-violet-50 to-white border-violet-100',
                            },
                        ].map(({ num, icon: Icon, title, desc, accent }) => (
                            <div key={num} className={`group relative p-7 rounded-3xl bg-gradient-to-br ${accent} border hover:shadow-xl hover:-translate-y-1 transition-all duration-300`}>
                                <span className="text-5xl font-black text-background-dark/6 absolute top-5 right-6 select-none">{num}</span>
                                <div className="w-12 h-12 rounded-2xl bg-white shadow-sm border border-background-dark/8 flex items-center justify-center text-primary mb-5 group-hover:scale-110 transition-transform">
                                    <Icon className="w-6 h-6" />
                                </div>
                                <h4 className="text-lg font-bold text-background-dark mb-2">{title}</h4>
                                <p className="text-background-dark/60 leading-relaxed text-sm font-light">{desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── FEATURES ── */}
            <section id="features" className="py-20 sm:py-28 bg-white relative overflow-hidden">
                <div className="absolute inset-0 pointer-events-none opacity-50">
                    <div className="absolute top-0 right-0 w-[40%] h-[60%] bg-[radial-gradient(ellipse_at_top_right,rgba(33,196,93,0.06),transparent_70%)]" />
                </div>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                    <div className="grid lg:grid-cols-2 gap-14 lg:gap-20 items-center">

                        {/* Left: Feature image */}
                        <div className="relative order-2 lg:order-1">
                            <div className="absolute -inset-4 bg-primary/5 blur-2xl rounded-full" />
                            {/*
                              community.jpg is 275×183 (3:2, very small).
                              We cap the container at 275px wide and use object-contain so it
                              renders at native resolution without upscaling blur.
                              A soft green bg fills the surrounding space.
                            */}
                            <div className="relative rounded-3xl overflow-hidden bg-emerald-50 shadow-[0_24px_60px_-12px_rgba(0,0,0,0.12)] flex items-center justify-center"
                                style={{ aspectRatio: '3/2', maxWidth: '100%' }}>
                                <img
                                    src="/images/community.jpg"
                                    alt="Community health worker with patient in Nigeria"
                                    className="w-full h-full object-contain"
                                    style={{ imageRendering: 'auto' }}
                                    onError={(e) => {
                                        e.currentTarget.style.display = 'none';
                                        e.currentTarget.parentElement!.style.background = 'linear-gradient(135deg, #e8f5ee 0%, #d1f0e0 100%)';
                                    }}
                                />
                            </div>

                            {/* Floating language badge */}
                            <div className="absolute -bottom-4 -right-4 bg-white rounded-2xl shadow-xl border border-primary/10 p-4">
                                <p className="text-[10px] uppercase tracking-widest font-bold text-background-dark/40 mb-2">Available in</p>
                                <div className="flex gap-1.5 flex-wrap max-w-[160px]">
                                    {['🇬🇧 EN', '🇳🇬 PID', 'YO', 'IG', 'HA'].map(lang => (
                                        <span key={lang} className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-0.5 rounded-full">{lang}</span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Right: Features list */}
                        <div className="order-1 lg:order-2 space-y-6">
                            <div>
                                <span className="inline-block text-primary font-bold text-xs uppercase tracking-[0.2em] mb-3 bg-primary/10 px-3 py-1.5 rounded-full">Built for Africa</span>
                                <h2 className="text-3xl sm:text-4xl font-extrabold text-background-dark tracking-tight leading-tight">
                                    Clinical-grade insight.<br />
                                    <span className="text-primary italic font-serif font-normal">No clinic required.</span>
                                </h2>
                                <p className="mt-3 text-background-dark/60 text-base leading-relaxed">
                                    CardioTwin combines AI, real-time biometrics, and cultural context to bring hospital-level cardiac screening to anyone with a smartphone.
                                </p>
                            </div>

                            <div className="space-y-4">
                                {[
                                    {
                                        icon: Heart,
                                        title: 'Personalised Baseline Calibration',
                                        desc: 'Learns your unique cardiovascular signature in minutes — so every alert is calibrated to you, not a population average.',
                                        color: 'bg-rose-50 text-rose-500',
                                    },
                                    {
                                        icon: TrendingUp,
                                        title: 'Risk Trajectory Projection',
                                        desc: '24-hour predictive curves show where your heart health is heading, giving you time to act before a crisis.',
                                        color: 'bg-sky-50 text-sky-500',
                                    },
                                    {
                                        icon: Zap,
                                        title: 'Instant Caregiver Alerts',
                                        desc: 'When risk escalates, your doctor or family member gets a WhatsApp alert immediately — in your local language.',
                                        color: 'bg-violet-50 text-violet-500',
                                    },
                                    {
                                        icon: Shield,
                                        title: 'Privacy-First Architecture',
                                        desc: 'Your biometric data never trains our models without consent. You own it, you control it.',
                                        color: 'bg-emerald-50 text-emerald-500',
                                    },
                                ].map(({ icon: Icon, title, desc, color }) => (
                                    <div key={title} className="flex gap-4 p-4 rounded-2xl bg-background-light/60 hover:bg-background-light transition-colors border border-transparent hover:border-primary/10">
                                        <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center shrink-0 mt-0.5`}>
                                            <Icon className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <h5 className="font-bold text-background-dark text-sm mb-0.5">{title}</h5>
                                            <p className="text-background-dark/55 text-xs leading-relaxed">{desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── SECURITY ── */}
            <section id="security" className="py-20 sm:py-24 bg-background-light relative overflow-hidden">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="bg-white rounded-3xl border border-background-dark/8 shadow-[0_8px_40px_-8px_rgba(0,0,0,0.06)] p-8 sm:p-12">
                        <div className="grid sm:grid-cols-3 gap-8">
                            <div className="sm:col-span-2 space-y-4">
                                <span className="inline-block text-primary font-bold text-xs uppercase tracking-[0.2em] bg-primary/10 px-3 py-1.5 rounded-full">Privacy & Trust</span>
                                <h2 className="text-2xl sm:text-3xl font-extrabold text-background-dark">
                                    {t('security.title1')} <span className="text-primary italic font-serif">{t('security.title2')}</span>
                                </h2>
                                <p className="text-background-dark/60 leading-relaxed font-light">
                                    {t('security.subtitle')}
                                </p>
                                <div className="grid sm:grid-cols-2 gap-4 pt-2">
                                    {[
                                        { icon: Shield, title: t('security.bankLevel'), desc: t('security.bankLevelDesc') },
                                        { icon: Lock, title: t('security.zeroThirdParty'), desc: t('security.zeroThirdPartyDesc') },
                                        { icon: Verified, title: t('security.hipaaCompliant'), desc: 'Aligned with global health data protection standards.' },
                                        { icon: Heart, title: 'Your data, your choice', desc: 'Opt out anytime. No biometric data is retained after session ends.' },
                                    ].map(({ icon: Icon, title, desc }) => (
                                        <div key={title} className="flex items-start gap-3 p-3 rounded-xl bg-background-light">
                                            <Icon className="w-5 h-5 text-primary shrink-0 mt-0.5" />
                                            <div>
                                                <p className="font-bold text-background-dark text-sm">{title}</p>
                                                <p className="text-xs text-background-dark/55 mt-0.5 leading-relaxed">{desc}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Security badge visual */}
                            <div className="flex items-center justify-center">
                                <div className="w-full max-w-[200px] aspect-square rounded-full bg-gradient-to-br from-primary/10 to-primary/5 border-2 border-primary/15 flex flex-col items-center justify-center text-center p-6 shadow-inner">
                                    <Shield className="w-10 h-10 text-primary mb-3" />
                                    <p className="text-xs font-black text-background-dark uppercase tracking-wide leading-snug">Bank-Level<br />Encryption</p>
                                    <div className="mt-3 flex items-center gap-1">
                                        <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                                        <span className="text-[9px] font-bold text-primary uppercase tracking-widest">Active</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── FINAL CTA ── */}
            <section className="py-20 sm:py-28 bg-background-dark relative overflow-hidden">
                {/* ECG decoration */}
                <div className="absolute inset-0 pointer-events-none opacity-[0.04]">
                    <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 1200 300">
                        <path d="M0,150 L300,150 L340,80 L370,210 L400,40 L430,250 L460,150 L700,150 L740,80 L770,210 L800,40 L830,250 L860,150 L1200,150"
                            fill="none" stroke="#21c45d" strokeWidth="4" />
                    </svg>
                </div>
                {/* Green glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary/10 blur-[100px] rounded-full pointer-events-none" />

                <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
                    <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white mb-5 tracking-tight leading-tight">
                        {t('cta.title1')}<br />
                        <span className="text-primary italic font-serif font-normal">{t('cta.title2')}</span> {t('cta.title3')}
                    </h2>
                    <p className="text-white/55 mb-10 text-base sm:text-lg max-w-xl mx-auto font-light leading-relaxed">
                        {t('cta.subtitle')}
                    </p>

                    <div className="flex flex-col items-center gap-5">
                        <div className="flex flex-col sm:flex-row gap-2 w-full max-w-md bg-white/10 border border-white/15 backdrop-blur-sm p-2 rounded-2xl">
                            <div className="flex items-center bg-white/10 rounded-xl flex-1 px-4">
                                <div className="flex items-center gap-2 text-sm font-semibold pr-3 border-r border-white/20 text-white shrink-0">
                                    <span className="text-xl">🇳🇬</span>
                                    <span>+234</span>
                                </div>
                                <input
                                    type="tel"
                                    className="bg-transparent border-none focus:outline-none w-full text-white placeholder:text-white/40 ml-3 py-3.5 font-medium text-sm"
                                    placeholder={t('hero.placeholder')}
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleStart()}
                                />
                            </div>
                            <button
                                onClick={handleStart}
                                disabled={isLoading}
                                className="bg-primary hover:bg-primary/90 active:scale-95 text-white px-7 py-3.5 rounded-xl font-bold transition-all flex items-center justify-center gap-2 whitespace-nowrap cursor-pointer shadow-lg shadow-primary/30 disabled:opacity-50 text-sm"
                            >
                                {isLoading ? (
                                    <span className="flex items-center gap-2"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Starting…</span>
                                ) : (
                                    <>{t('hero.startScreening')} <ArrowRight className="w-4 h-4" /></>
                                )}
                            </button>
                        </div>

                        {/* Emergency contacts toggle in CTA */}
                        <div className="w-full max-w-md text-left">
                            <button
                                onClick={() => setShowContacts(!showContacts)}
                                className="text-xs font-semibold text-primary/70 hover:text-primary transition-colors cursor-pointer"
                            >
                                {showContacts ? '▾' : '▸'} {t('caregiver.title')}
                            </button>
                            {showContacts && renderEmergencyContacts()}
                        </div>

                        <p className="text-xs text-white/35 font-medium">
                            {t('cta.terms')} <a href="#" className="underline hover:text-white/60 transition-colors">{t('cta.termsLink')}</a> {t('cta.and')} <a href="#" className="underline hover:text-white/60 transition-colors">{t('cta.privacyLink')}</a>.
                        </p>
                    </div>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className="bg-background-dark border-t border-white/5 py-8">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-lg bg-primary/20 flex items-center justify-center">
                            <Heart className="w-3 h-3 text-primary" />
                        </div>
                        <span className="text-sm font-bold text-white/60">Cardio<span className="text-primary italic font-serif">Twin</span></span>
                    </div>
                    <p className="text-xs text-white/30 font-medium text-center">
                        Wellness screening tool only — not a medical diagnosis. Always consult a qualified health professional.
                    </p>
                    <p className="text-xs text-white/30">© 2026 CardioTwin</p>
                </div>
            </footer>
        </>
    );
}
