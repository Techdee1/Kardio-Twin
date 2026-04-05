export type DataSourceMode = 'simulator' | 'hardware' | 'manual' | 'hybrid';

const VALID_MODES: DataSourceMode[] = ['simulator', 'hardware', 'manual', 'hybrid'];

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

export const DATA_SOURCE_MODE: DataSourceMode = parseMode(import.meta.env.VITE_DATA_SOURCE_MODE);

const DEFAULT_ENABLE_SIMULATOR = DATA_SOURCE_MODE === 'simulator';
const DEFAULT_ENABLE_SCORE_POLLING = DATA_SOURCE_MODE === 'hardware' || DATA_SOURCE_MODE === 'hybrid';
const DEFAULT_ENABLE_MANUAL_ENTRY = DATA_SOURCE_MODE === 'manual' || DATA_SOURCE_MODE === 'hybrid';

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
