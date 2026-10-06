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

While the submission runs, the dashboard polls `GET /api/v1/evaluation-progress/{idempotency_key}` once per second using the submission's `Idempotency-Key`. Stages and recent activity come from actual backend processing, including OCR attempts and character counts. Polling stops on completion, failure, or leaving the page, and reconnects after temporary network errors.

Progress snapshots are kept in memory for up to one hour (at most 1,000 evaluations). Run the API with one Uvicorn worker, as in `uvicorn api.app:app`; multiple workers or replicas require a shared progress store. Completed reports remain in the existing persistence system.

## Tests and build

```powershell
npm test
npm run build
```
