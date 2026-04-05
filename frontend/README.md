# CardioTwin Frontend

React + TypeScript + Vite dashboard for the CardioTwin platform.

## Core Views

- Overview: live 3D avatar, CardioTwin score, and AI nudge panel
- Projection: what-if and trend projections
- History: score timeline view
- Manual: manual vital sign input when hardware is unavailable
- Settings: language controls (English, Hausa, Igbo, Yoruba)

## Development

```bash
npm install
npm run dev
```

Default local URL is usually http://localhost:5173.

## Build And Lint

```bash
npm run build
npm run lint
npm run preview
```

## Environment Variables

Use `frontend/.env.local` for local overrides.

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `https://cardiotwin-jqrct.ondigitalocean.app` | Backend API base URL |
| `VITE_DATA_SOURCE_MODE` | `simulator` | Data source mode: `simulator`, `hardware`, `manual`, `hybrid` |
| `VITE_ENABLE_SIMULATOR` | mode-derived | Optional override for simulator stream |
| `VITE_ENABLE_SCORE_POLLING` | mode-derived | Optional override for polling `/api/score/:sessionId` |
| `VITE_ENABLE_MANUAL_ENTRY` | mode-derived | Optional override for manual entry panel |

Example:

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_DATA_SOURCE_MODE=hybrid
```

## Runtime Data Source Modes

- `simulator`: sends synthetic readings to `POST /api/reading`
- `hardware`: polls latest data from `GET /api/score/{session_id}`
- `manual`: enables `POST /api/reading/manual`
- `hybrid`: enables both hardware polling and manual entry

The dashboard includes a runtime mode toggle button and persists the selected mode in browser storage.

## Integration Notes

- Start backend first for local integration testing.
- If backend runs on localhost, ensure `VITE_API_BASE_URL=http://localhost:8000`.
- Manual mode remains available while still allowing navigation to overview after score responses.
