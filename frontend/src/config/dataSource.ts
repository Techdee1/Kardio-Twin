export type DataSourceMode = 'simulator' | 'hardware' | 'manual' | 'hybrid';

const VALID_MODES: DataSourceMode[] = ['simulator', 'hardware', 'manual', 'hybrid'];
export const DATA_SOURCE_MODE_OPTIONS: DataSourceMode[] = [...VALID_MODES];
export const DATA_SOURCE_MODE_STORAGE_KEY = 'cardiotwin-data-source-mode';

function parseMode(value: unknown): DataSourceMode {
    if (typeof value !== 'string') {
        return 'simulator';
    }

    const normalized = value.trim().toLowerCase();
    return (VALID_MODES as string[]).includes(normalized)
        ? (normalized as DataSourceMode)
        : 'simulator';
}

function parseBooleanFlag(value: unknown, defaultValue: boolean): boolean {
    if (typeof value !== 'string') {
        return defaultValue;
    }

    const normalized = value.trim().toLowerCase();
    if (normalized === 'true' || normalized === '1' || normalized === 'yes') {
        return true;
    }
    if (normalized === 'false' || normalized === '0' || normalized === 'no') {
        return false;
    }

    return defaultValue;
}

export function getModeDefaults(mode: DataSourceMode) {
    return {
        enableSimulator: mode === 'simulator',
        enableScorePolling: mode === 'hardware' || mode === 'hybrid',
        enableManualEntry: mode === 'manual' || mode === 'hybrid',
    } as const;
}

export const DATA_SOURCE_MODE: DataSourceMode = parseMode(import.meta.env.VITE_DATA_SOURCE_MODE);

const DEFAULTS = getModeDefaults(DATA_SOURCE_MODE);
const DEFAULT_ENABLE_SIMULATOR = DEFAULTS.enableSimulator;
const DEFAULT_ENABLE_SCORE_POLLING = DEFAULTS.enableScorePolling;
const DEFAULT_ENABLE_MANUAL_ENTRY = DEFAULTS.enableManualEntry;

export const ENABLE_SIMULATOR = parseBooleanFlag(
    import.meta.env.VITE_ENABLE_SIMULATOR,
    DEFAULT_ENABLE_SIMULATOR,
);

export const ENABLE_SCORE_POLLING = parseBooleanFlag(
    import.meta.env.VITE_ENABLE_SCORE_POLLING,
    DEFAULT_ENABLE_SCORE_POLLING,
);

export const ENABLE_MANUAL_ENTRY = parseBooleanFlag(
    import.meta.env.VITE_ENABLE_MANUAL_ENTRY,
    DEFAULT_ENABLE_MANUAL_ENTRY,
);

export const DATA_SOURCE_CONFIG = {
    mode: DATA_SOURCE_MODE,
    enableSimulator: ENABLE_SIMULATOR,
    enableScorePolling: ENABLE_SCORE_POLLING,
    enableManualEntry: ENABLE_MANUAL_ENTRY,
} as const;

export function getStoredDataSourceMode(): DataSourceMode | null {
    try {
        if (typeof window === 'undefined') {
            return null;
        }

        const storedMode = window.localStorage.getItem(DATA_SOURCE_MODE_STORAGE_KEY);
        if (!storedMode) {
            return null;
        }

        return parseMode(storedMode);
    } catch {
        return null;
    }
}

export function setStoredDataSourceMode(mode: DataSourceMode): void {
    try {
        if (typeof window === 'undefined') {
            return;
        }

        window.localStorage.setItem(DATA_SOURCE_MODE_STORAGE_KEY, mode);
    } catch {
        // Ignore storage failures in private mode or restricted contexts.
    }
}
