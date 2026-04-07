import { useState } from 'react';
import { ClipboardPen, Send, CheckCircle } from 'lucide-react';
import { api } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

export interface ManualSubmittedVitals {
    bpm: number;
    hrv: number;
    spo2: number;
    temperature: number;
}

interface ManualInputPanelProps {
    sessionId: string;
    onReadingSubmitted?: (result: any, submittedVitals: ManualSubmittedVitals) => void;
}

export default function ManualInputPanel({ sessionId, onReadingSubmitted }: ManualInputPanelProps) {
    const { t } = useLanguage();
    const [bpm, setBpm] = useState('');
    const [hrv, setHrv] = useState('');
    const [spo2, setSpo2] = useState('');
    const [temp, setTemp] = useState('');
    const [systolic, setSystolic] = useState('');
    const [diastolic, setDiastolic] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async () => {
        if (!bpm.trim()) {
            setError(t('manual.required'));
            return;
        }
        setError('');
        setSubmitting(true);
        setSuccess(false);

        try {
            const submittedVitals: ManualSubmittedVitals = {
                bpm: parseFloat(bpm),
                hrv: hrv ? parseFloat(hrv) : 50,
                spo2: spo2 ? parseFloat(spo2) : 97,
                temperature: temp ? parseFloat(temp) : 36.6,
            };

            const result = await api.submitManualReading({
                session_id: sessionId,
                bpm: submittedVitals.bpm,
                hrv: submittedVitals.hrv,
                spo2: submittedVitals.spo2,
                temperature: submittedVitals.temperature,
                systolic_bp: systolic ? parseFloat(systolic) : undefined,
                diastolic_bp: diastolic ? parseFloat(diastolic) : undefined,
            });
            setSuccess(true);
            onReadingSubmitted?.(result, submittedVitals);
            // Reset after a moment
            setTimeout(() => setSuccess(false), 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Submission failed');
        } finally {
            setSubmitting(false);
        }
    };

    const inputClass = 'w-full px-3 py-2.5 rounded-xl bg-background-light border border-primary/15 text-sm font-medium text-background-dark placeholder:text-background-dark/40 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/30 transition-all';

    return (
        <div className="bg-white rounded-2xl sm:rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
            <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-background-light">
                <div className="flex items-center gap-3 mb-1">
                    <ClipboardPen className="w-5 h-5 text-primary" />
                    <h3 className="text-base sm:text-lg font-bold text-background-dark">{t('manual.title')}</h3>
                </div>
                <p className="text-xs sm:text-sm text-background-dark/60 font-medium ml-8">{t('manual.subtitle')}</p>
            </div>

            <div className="p-4 sm:p-6 space-y-4">
                {/* Core vitals */}
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.bpm')} *</label>
                        <input type="number" value={bpm} onChange={e => setBpm(e.target.value)} placeholder="72" className={inputClass} min={20} max={250} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.hrv')}</label>
                        <input type="number" value={hrv} onChange={e => setHrv(e.target.value)} placeholder="50" className={inputClass} min={0} max={300} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.spo2')}</label>
                        <input type="number" value={spo2} onChange={e => setSpo2(e.target.value)} placeholder="97" className={inputClass} min={50} max={100} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.temp')}</label>
                        <input type="number" value={temp} onChange={e => setTemp(e.target.value)} placeholder="36.6" className={inputClass} min={30} max={43} step={0.1} />
                    </div>
                </div>

                {/* Blood pressure (optional) */}
                <div>
                    <p className="text-xs text-background-dark/50 font-medium mb-2">{t('manual.bpOptional')}</p>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.systolic')}</label>
                            <input type="number" value={systolic} onChange={e => setSystolic(e.target.value)} placeholder="120" className={inputClass} min={60} max={250} />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.diastolic')}</label>
                            <input type="number" value={diastolic} onChange={e => setDiastolic(e.target.value)} placeholder="80" className={inputClass} min={30} max={150} />
                        </div>
                    </div>
                </div>

                {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}

                {success ? (
                    <div className="flex items-center gap-2 text-emerald-600 text-sm font-bold">
                        <CheckCircle className="w-4 h-4" />
                        {t('manual.success')}
                    </div>
                ) : (
                    <button
                        onClick={handleSubmit}
                        disabled={submitting}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary text-white font-bold text-sm transition-all hover:bg-primary/90 disabled:opacity-50 shadow-md hover:shadow-lg cursor-pointer"
                    >
                        <Send className="w-4 h-4" />
                        {submitting ? t('manual.submitting') : t('manual.submit')}
                    </button>
                )}

                <p className="text-[10px] text-background-dark/40 text-center font-medium">{t('safety.disclaimer')}</p>
            </div>
        </div>
    );
}
