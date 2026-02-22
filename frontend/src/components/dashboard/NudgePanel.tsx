import { useState } from 'react';
import { Sparkles, X, RefreshCw } from 'lucide-react';
import type { NudgeResponse } from '../../services/api';
import { useLanguage } from '../../i18n/LanguageContext';

interface NudgePanelProps {
    nudge: NudgeResponse;
    isLoading: boolean;
    onRefresh: () => void;
    onClose: () => void;
}

const zoneStyles: Record<string, { bg: string; border: string; text: string; badge: string; icon: string; accent: string }> = {
    GREEN: {
        bg: 'bg-emerald-50',
        border: 'border-emerald-200',
        text: 'text-emerald-800',
        badge: 'bg-emerald-100 text-emerald-700 border-emerald-300',
        icon: 'text-emerald-500',
        accent: 'bg-emerald-400',
    },
    YELLOW: {
        bg: 'bg-amber-50',
        border: 'border-amber-200',
        text: 'text-amber-800',
        badge: 'bg-amber-100 text-amber-700 border-amber-300',
        icon: 'text-amber-500',
        accent: 'bg-amber-400',
    },
    ORANGE: {
        bg: 'bg-orange-50',
        border: 'border-orange-200',
        text: 'text-orange-800',
        badge: 'bg-orange-100 text-orange-700 border-orange-300',
        icon: 'text-orange-500',
        accent: 'bg-orange-400',
    },
    RED: {
        bg: 'bg-rose-50',
        border: 'border-rose-200',
        text: 'text-rose-800',
        badge: 'bg-rose-100 text-rose-700 border-rose-300',
        icon: 'text-rose-500',
        accent: 'bg-rose-400',
    },
};

export default function NudgePanel({ nudge, isLoading, onRefresh, onClose }: NudgePanelProps) {
    const style = zoneStyles[nudge.zone] || zoneStyles.GREEN;
    const [hoveredRefresh, setHoveredRefresh] = useState(false);
    const { t } = useLanguage();

    return (
        <div
            className="h-full flex flex-col bg-white/80 backdrop-blur-md rounded-3xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.04)] overflow-hidden"
            style={{ animation: 'nudgePanelIn 0.5s ease-out' }}
        >
            {/* Accent bar */}
            <div className={`h-1.5 w-full ${style.accent}`} />

            {/* Header */}
            <div className="flex items-center justify-between px-5 pt-4 pb-3">
                <div className="flex items-center gap-2.5">
                    <div className={`p-2 rounded-xl ${style.bg} border ${style.border}`}>
                        <Sparkles className={`w-4 h-4 ${style.icon}`} />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-background-dark">{t('nudge.aiInsight')}</h3>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${style.badge}`}>
                            {nudge.zone_label}
                        </span>
                    </div>
                </div>
                <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg hover:bg-black/5 transition-colors text-background-dark/30 hover:text-background-dark/60 cursor-pointer"
                    title="Close panel"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            {/* Divider */}
            <div className="mx-5 h-[1px] bg-background-dark/5" />

            {/* Message */}
            <div className="flex-1 px-5 py-5 overflow-y-auto">
                <div className={`${style.bg} ${style.border} border rounded-2xl p-5`}>
                    <p className={`text-sm font-medium leading-relaxed ${style.text}`}>
                        {nudge.message}
                    </p>
                </div>

                {/* Decorative tips section */}
                <div className="mt-5 space-y-3">
                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-background-dark/40">
                        {t('nudge.quickActions')}
                    </h4>
                    <div className="grid grid-cols-2 gap-2">
                        {[
                            { emoji: '🫁', label: t('nudge.deepBreathing') },
                            { emoji: '🚶', label: t('nudge.takeWalk') },
                            { emoji: '💧', label: t('nudge.stayHydrated') },
                            { emoji: '😌', label: t('nudge.mindfulBreak') },
                        ].map((tip) => (
                            <div
                                key={tip.label}
                                className="flex items-center gap-2 p-2.5 rounded-xl bg-background-light/80 border border-background-dark/5 text-xs font-medium text-background-dark/70"
                            >
                                <span className="text-base">{tip.emoji}</span>
                                {tip.label}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Refresh button */}
            <div className="px-5 pb-5">
                <button
                    onClick={onRefresh}
                    disabled={isLoading}
                    onMouseEnter={() => setHoveredRefresh(true)}
                    onMouseLeave={() => setHoveredRefresh(false)}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary text-sm font-bold transition-all border border-primary/20 hover:border-primary/30 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <RefreshCw
                        className={`w-4 h-4 transition-transform ${isLoading ? 'animate-spin' : hoveredRefresh ? 'rotate-180' : ''}`}
                    />
                    {isLoading ? t('nudge.gettingAdvice') : t('nudge.refreshAdvice')}
                </button>
            </div>
        </div>
    );
}
