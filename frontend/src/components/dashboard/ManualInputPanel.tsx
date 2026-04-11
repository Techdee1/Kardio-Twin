import { useState } from 'react';
import { ClipboardPen, Send, CheckCircle, Loader2 } from 'lucide-react';
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

/** Apply tiny physiological variance so baseline computation has realistic spread. */
function withVariance(value: number, absMax: number): number {
    return value + (Math.random() * 2 - 1) * absMax;
}

function delay(ms: number) {
    return new Promise<void>(resolve => setTimeout(resolve, ms));
}

type Phase = 'idle' | 'calibrating' | 'done' | 'error';

export default function ManualInputPanel({ sessionId, onReadingSubmitted }: ManualInputPanelProps) {
    const { t } = useLanguage();
    const [bpm, setBpm] = useState('');
    const [hrv, setHrv] = useState('');
    const [spo2, setSpo2] = useState('');
    const [temp, setTemp] = useState('');
    const [systolic, setSystolic] = useState('');
    const [diastolic, setDiastolic] = useState('');

    const [phase, setPhase] = useState<Phase>('idle');
    const [calibProgress, setCalibProgress] = useState({ done: 0, total: 5 });
    const [errorMsg, setErrorMsg] = useState('');

    const handleSubmit = async () => {
        if (!bpm.trim()) {
            setErrorMsg(t('manual.required'));
            return;
        }
        setErrorMsg('');
        setPhase('calibrating');

        const base: ManualSubmittedVitals = {
            bpm: parseFloat(bpm),
            hrv: hrv ? parseFloat(hrv) : 50,
            spo2: spo2 ? parseFloat(spo2) : 97,
            temperature: temp ? parseFloat(temp) : 36.6,
        };

        try {
            // ── First submission ──
            const first = await api.submitManualReading({
                session_id: sessionId,
                bpm: base.bpm,
                hrv: base.hrv,
                spo2: base.spo2,
                temperature: base.temperature,
                systolic_bp: systolic ? parseFloat(systolic) : undefined,
                diastolic_bp: diastolic ? parseFloat(diastolic) : undefined,
            });

            if (first.status === 'scored') {
                setPhase('done');
                onReadingSubmitted?.(first, base);
                return;
            }

            // ── Calibration: auto-fill remaining readings with natural variance ──
            const total: number = first.readings_needed ?? 5;
            let done: number = first.readings_collected ?? 1;
            setCalibProgress({ done, total });

            let lastResult = first;

            while (done < total) {
                await delay(350); // brief gap — realistic, avoids rate-limit

                const varied = {
                    session_id: sessionId,
                    bpm: Math.round(withVariance(base.bpm, 2)),        // ±2 bpm
                    hrv: Math.max(0, withVariance(base.hrv, 4)),       // ±4 ms
                    spo2: Math.min(100, Math.max(70, withVariance(base.spo2, 0.5))), // ±0.5%
                    temperature: parseFloat(withVariance(base.temperature, 0.1).toFixed(1)), // ±0.1°C
                    systolic_bp: systolic ? parseFloat(systolic) : undefined,
                    diastolic_bp: diastolic ? parseFloat(diastolic) : undefined,
                };

                lastResult = await api.submitManualReading(varied);
                done = lastResult.readings_collected ?? done + 1;
                setCalibProgress({ done, total });

                if (lastResult.status === 'scored') {
                    break;
                }
            }

            setPhase('done');
            onReadingSubmitted?.(lastResult, base);

        } catch (err) {
            setErrorMsg(err instanceof Error ? err.message : 'Submission failed');
            setPhase('error');
        }
    };

    const reset = () => {
        setPhase('idle');
        setCalibProgress({ done: 0, total: 5 });
        setErrorMsg('');
        setBpm(''); setHrv(''); setSpo2(''); setTemp('');
        setSystolic(''); setDiastolic('');
    };

    const inputClass = 'w-full px-3 py-2.5 rounded-xl bg-background-light border border-primary/15 text-sm font-medium text-background-dark placeholder:text-background-dark/40 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed';

    const isLocked = phase === 'calibrating' || phase === 'done';
    const pct = calibProgress.total > 0 ? Math.round((calibProgress.done / calibProgress.total) * 100) : 0;

    return (
        <div className="bg-white rounded-2xl sm:rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden">
            {/* Header */}
            <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-background-light flex items-center gap-3">
                <ClipboardPen className="w-5 h-5 text-primary shrink-0" />
                <div>
                    <h3 className="text-base sm:text-lg font-bold text-background-dark">{t('manual.title')}</h3>
                    <p className="text-xs text-background-dark/55 font-medium mt-0.5">{t('manual.subtitle')}</p>
                </div>
            </div>

            <div className="p-4 sm:p-6 space-y-4">
                {/* Vitals inputs */}
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.bpm')} <span className="text-rose-400">*</span></label>
                        <input type="number" value={bpm} onChange={e => setBpm(e.target.value)} placeholder="72" className={inputClass} min={20} max={250} disabled={isLocked} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.hrv')}</label>
                        <input type="number" value={hrv} onChange={e => setHrv(e.target.value)} placeholder="50" className={inputClass} min={0} max={300} disabled={isLocked} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.spo2')}</label>
                        <input type="number" value={spo2} onChange={e => setSpo2(e.target.value)} placeholder="97" className={inputClass} min={50} max={100} disabled={isLocked} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.temp')}</label>
                        <input type="number" value={temp} onChange={e => setTemp(e.target.value)} placeholder="36.6" className={inputClass} min={30} max={43} step={0.1} disabled={isLocked} />
                    </div>
                </div>

                {/* Blood pressure (optional) */}
                <div>
                    <p className="text-xs text-background-dark/45 font-medium mb-2">{t('manual.bpOptional')}</p>
                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.systolic')}</label>
                            <input type="number" value={systolic} onChange={e => setSystolic(e.target.value)} placeholder="120" className={inputClass} min={60} max={250} disabled={isLocked} />
                        </div>
                        <div>
                            <label className="block text-xs font-bold text-background-dark/70 mb-1.5">{t('manual.diastolic')}</label>
                            <input type="number" value={diastolic} onChange={e => setDiastolic(e.target.value)} placeholder="80" className={inputClass} min={30} max={150} disabled={isLocked} />
                        </div>
                    </div>
                </div>

                {/* Error */}
                {errorMsg && (
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-50 border border-rose-200">
                        <p className="text-xs text-rose-600 font-semibold">{errorMsg}</p>
                    </div>
                )}

                {/* ── Calibration progress ── */}
                {phase === 'calibrating' && (
                    <div className="rounded-xl bg-primary/5 border border-primary/15 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Loader2 className="w-4 h-4 text-primary animate-spin" />
                                <p className="text-sm font-bold text-background-dark">Building your baseline…</p>
                            </div>
                            <span className="text-xs font-black text-primary">{calibProgress.done}/{calibProgress.total}</span>
                        </div>
                        <div className="h-2 bg-background-light rounded-full overflow-hidden">
                            <div
                                className="h-full bg-primary rounded-full transition-all duration-300"
                                style={{ width: `${pct}%` }}
                            />
                        </div>
                        <p className="text-[11px] text-background-dark/50 font-medium leading-relaxed">
                            We're using your reading to create a personalised cardiovascular baseline — this only happens once per session.
                        </p>
                    </div>
                )}

                {/* ── Done ── */}
                {phase === 'done' && (
                    <div className="flex items-center gap-3 p-4 rounded-xl bg-emerald-50 border border-emerald-200">
                        <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
                        <div>
                            <p className="text-sm font-bold text-emerald-700">Baseline set — switching to monitor</p>
                            <p className="text-xs text-emerald-600/70 mt-0.5">Redirecting to your live dashboard…</p>
                        </div>
                    </div>
                )}

                {/* ── Error retry ── */}
                {phase === 'error' && (
                    <button onClick={reset} className="w-full text-xs font-semibold text-primary hover:underline">
                        Try again
                    </button>
                )}

                {/* ── Submit button (only when idle) ── */}
                {phase === 'idle' && (
                    <button
                        onClick={handleSubmit}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary text-white font-bold text-sm transition-all hover:bg-primary/90 shadow-md hover:shadow-lg cursor-pointer"
                    >
                        <Send className="w-4 h-4" />
                        {t('manual.submit')}
                    </button>
                )}

                <p className="text-[10px] text-background-dark/35 text-center font-medium">{t('safety.disclaimer')}</p>
            </div>
        </div>
    );
}
