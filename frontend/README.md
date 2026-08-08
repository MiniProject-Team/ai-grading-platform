# SmartEval Dashboard

Teacher-facing React dashboard for the SmartEval API. It displays backend-provided evaluation history and reports; it does not perform OCR, marks calculation, or semantic evaluation in the browser.

## Requirements

- Node.js 20 or later
- Running SmartEval backend with PostgreSQL persistence configured

## Setup

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_BASE_URL` in `.env` to the SmartEval API, for example `http://localhost:8000`. The frontend is served by Vite at `http://localhost:5173` by default.

## Routes

- `/` dashboard and recent evaluations
- `/evaluate` new evaluation submission
- `/evaluations` paginated history and filters
- `/evaluations/:evaluationId` stored evaluation details

The dashboard uses `POST /api/v1/evaluate` and the evaluation-history endpoints exposed by SmartEval. Uploaded files remain local until the teacher starts evaluation.

## Tests and build

```powershell
npm test
npm run build
```
