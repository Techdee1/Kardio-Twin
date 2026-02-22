import { Heart, Globe, ChevronDown } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useLanguage, LANGUAGE_OPTIONS } from '../../i18n/LanguageContext';

export default function Navbar() {
    const { lang, setLang, t } = useLanguage();
    const [langOpen, setLangOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setLangOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

    const currentLang = LANGUAGE_OPTIONS.find(l => l.code === lang)!;

    return (
        <nav className="sticky top-0 z-50 w-full border-b border-primary/10 bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-20 items-center">
                    <div className="flex items-center gap-2 text-primary">
                        <Heart className="w-8 h-8 fill-primary stroke-primary" />
                        <span className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
                            CardioTwin<span className="text-primary">AI</span>
                        </span>
                    </div>
                    <div className="hidden md:flex items-center gap-8">
                        <a href="#how-it-works" className="text-sm font-medium hover:text-primary transition-colors">{t('nav.howItWorks')}</a>
                        <a href="#security" className="text-sm font-medium hover:text-primary transition-colors">{t('nav.security')}</a>
                        <a href="#impact" className="text-sm font-medium hover:text-primary transition-colors">{t('nav.impact')}</a>

                        {/* Language Switcher */}
                        <div className="relative" ref={dropdownRef}>
                            <button
                                onClick={() => setLangOpen(!langOpen)}
                                className="flex items-center gap-2 px-3 py-2 rounded-xl border border-primary/20 hover:border-primary/40 bg-white hover:bg-white/85 transition-all text-sm font-medium text-background-dark cursor-pointer"
                            >
                                <Globe className="w-4 h-4 text-primary" />
                                <span>{currentLang.flag} {currentLang.label}</span>
                                <ChevronDown className={`w-3.5 h-3.5 text-background-dark/50 transition-transform ${langOpen ? 'rotate-180' : ''}`} />
                            </button>

                            {langOpen && (
                                <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl border border-primary/10 shadow-[0_8px_30px_rgb(0,0,0,0.08)] py-2 z-50 animate-in fade-in slide-in-from-top-2">
                                    {LANGUAGE_OPTIONS.map((option) => (
                                        <button
                                            key={option.code}
                                            onClick={() => { setLang(option.code); setLangOpen(false); }}
                                            className={`w-full text-left px-4 py-2.5 text-sm font-medium flex items-center gap-3 transition-colors cursor-pointer ${lang === option.code
                                                    ? 'bg-primary/10 text-primary'
                                                    : 'text-background-dark/70 hover:bg-background-light hover:text-background-dark'
                                                }`}
                                        >
                                            <span className="text-base">{option.flag}</span>
                                            <span>{option.label}</span>
                                            {lang === option.code && (
                                                <span className="ml-auto text-primary text-xs">✓</span>
                                            )}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        <button className="bg-primary hover:bg-primary/90 text-background-dark px-6 py-2.5 rounded-lg font-bold text-sm transition-all shadow-lg shadow-primary/20">
                            {t('nav.getStarted')}
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
}
