import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import en from './translations/en';
import yo from './translations/yo';
import ha from './translations/ha';
import ig from './translations/ig';

export type Locale = 'en' | 'yo' | 'ha' | 'ig';

const translations: Record<Locale, Record<string, string>> = { en, yo, ha, ig };

export const LANGUAGE_OPTIONS: { code: Locale; label: string; flag: string }[] = [
    { code: 'en', label: 'English', flag: '🇬🇧' },
    { code: 'yo', label: 'Yorùbá', flag: '🇳🇬' },
    { code: 'ha', label: 'Hausa', flag: '🇳🇬' },
    { code: 'ig', label: 'Igbo', flag: '🇳🇬' },
];

interface LanguageContextValue {
    lang: Locale;
    setLang: (locale: Locale) => void;
    t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextValue>({
    lang: 'en',
    setLang: () => { },
    t: (key: string) => key,
});

const STORAGE_KEY = 'cardiotwin-lang';

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [lang, setLangState] = useState<Locale>(() => {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored && ['en', 'yo', 'ha', 'ig'].includes(stored)) {
                return stored as Locale;
            }
        } catch {
            // SSR or access denied
        }
        return 'en';
    });

    useEffect(() => {
        try {
            localStorage.setItem(STORAGE_KEY, lang);
        } catch {
            // Ignore
        }
    }, [lang]);

    const setLang = (locale: Locale) => {
        setLangState(locale);
    };

    const t = (key: string): string => {
        return translations[lang][key] ?? translations.en[key] ?? key;
    };

    return (
        <LanguageContext.Provider value={{ lang, setLang, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    return useContext(LanguageContext);
}
