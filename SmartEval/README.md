# SmartEval

SmartEval evaluates university answer-sheet content after SmartHTR has extracted handwritten text. The two applications are intentionally separate:

```text
Student answer sheet -> SmartHTR -> UTF-8 page text -> SmartEval
Question paper -------------------------------------> SmartEval
Model answers --------------------------------------> SmartEval
```

SmartHTR owns OCR only. SmartEval does not import OCR models or pipeline internals.

## Current capabilities

Phase 4 loads `.txt`, simple `.json`, text-based `.pdf`, or a directory of page-text files; parses flexible question/answer headings; extracts available marks; validates IDs; and maps `Question`, `ModelAnswer`, and `StudentAnswer` into `EvaluationItem` objects.

Phase 5 evaluates complete mapped answers with the configurable lightweight embedding model `sentence-transformers/all-MiniLM-L6-v2`. It returns independent normalized signals for semantic similarity, concept coverage, relevance, and completeness, followed by a configurable status: `correct`, `mostly_correct`, `partially_correct`, `irrelevant`, `no_answer`, or `model_answer_missing`.

Phase 6 converts those signals into proportional, explainable marks with configurable weights: semantic similarity `40%`, concept coverage `30%`, relevance `15%`, and completeness `15%` by default. Scores are bounded to each question's maximum marks and rounded with a configurable half-up policy. Missing model answers remain unevaluated rather than becoming zero marks.

Phase 7 generates concise, deterministic, teacher-style feedback from the existing Phase 5 metrics and Phase 6 marks. It identifies only metric-supported strengths and general gaps; since Phase 5 currently exposes aggregate concept coverage rather than named concept matches, it does not invent missing concepts. No LLM or external feedback API is used.

Phase 8 assembles the existing results into an API-ready `EvaluationReport`, including question-level results, totals, evaluation statistics, supported report-level strengths and weaknesses, warnings, optional student/exam metadata, JSON export, and a concise text report. A missing model answer stays unavailable and causes a `partially_evaluated` report; it is never converted into zero marks.

SmartHTR remains the source of truth for handwritten OCR. In Google Colab, SmartHTR and SmartEval share one Python runtime: `SharedRuntimeSmartHTRClient` calls SmartHTR's existing complete-document `OCRPipeline` directly and passes its ordered page text plus `full_text` to SmartEval. SmartEval does not duplicate OCR, modify the TrOCR pipeline, or create a network boundary.

## OCR Providers

SmartEval selects one document-level OCR provider through `OCR_PROVIDER`. Both providers return the same OCR result structure and feed the existing text normalization, question/answer extraction, semantic evaluation, marks, feedback, and reporting pipeline. No downstream grading code is duplicated.

### TrOCR

- Local handwritten OCR through the existing SmartHTR pipeline.
- Preserves image preprocessing, DocTR layout detection, line cropping, reading-order reconstruction, and the TrOCR model.
- Requires no external OCR API.

### iLovePDF

- Cloud/API-based PDF OCR using the iLovePDF `pdfocr` tool.
- Requires iLovePDF developer credentials and an internet connection.
- Uses account processing allowance/credits.
- Intended for experimental comparison with TrOCR; this project makes no accuracy claim for either provider.

The default remains TrOCR:

```text
OCR_PROVIDER=trocr
```

To use iLovePDF for PDF student sheets:

```text
OCR_PROVIDER=ilovepdf
ILOVEPDF_PUBLIC_KEY=your-public-key
ILOVEPDF_SECRET_KEY=your-secret-key
ILOVEPDF_REGION=in
ILOVEPDF_TIMEOUT=120
```

Keep these values server-side in `SmartEval/.env`. Never put the secret key in frontend code, commit real credentials, or log JWTs. Copy `SmartEval/.env.example` to `.env` and fill the placeholders only when using iLovePDF.

Phase 10 exposes that application service through a FastAPI interface. The API owns only multipart validation, temporary upload handling, response serialization, and safe error conversion; it delegates OCR and evaluation to the existing Phase 9 service.

Phase 11 adds PostgreSQL-backed evaluation history. A completed report is saved atomically as both normalized student, exam, evaluation, and question records and an immutable JSON report snapshot. SmartHTR remains unchanged and does not access this database.

Question-paper understanding is available independently at `POST /api/v1/question-papers/analyze`. It discovers sections, common numbering variants, marks, COs, internal `OR` choices, available header metadata, and question types from extracted text without assuming a single paper layout. Send `generate_answers=true` to receive a marks-aware answer-sheet scaffold. It preserves unknown fields as `null` and returns validation warnings rather than modifying a paper.

The evaluation unit is the complete answer for one question, never an individual OCR word.

## SmartHTR connection

Open [../notebooks/smarthtr_smarteval_pipeline.ipynb](../notebooks/smarthtr_smarteval_pipeline.ipynb) with a Google Colab runtime that can access this project checkout. The notebook uses runtime-neutral project paths, creates one shared SmartHTR client, runs the existing full-page OCR pipeline, displays its ordered OCR result, performs quality checks, and sends that result directly into the existing SmartEval workflow.

The normal setting is `SMARTHR_PROVIDER=local`. It means local to the current Python runtime, including a Colab runtime; it does not mean a separate local OCR process. No public URL, ngrok tunnel, health endpoint, or `SMARTHR_BASE_URL` is required.

## Run

Mapping only:

```powershell
python main.py --question-paper inputs/question_paper_fixture.txt --model-answer inputs/model_answer_fixture.txt --student-text inputs/student_text_fixture.txt
```

Semantic signals without marks:

```powershell
python main.py --question-paper inputs/question_paper_fixture.txt --model-answer inputs/model_answer_fixture.txt --student-text inputs/student_text_fixture.txt --evaluate
```

Semantic signals and marks:

```powershell
python main.py --question-paper inputs/question_paper_fixture.txt --model-answer inputs/model_answer_fixture.txt --student-text inputs/student_text_fixture.txt --marks
```

Semantic signals, marks, and feedback:

```powershell
python main.py --question-paper inputs/question_paper_fixture.txt --model-answer inputs/model_answer_fixture.txt --student-text inputs/student_text_fixture.txt --feedback
```

Final report with JSON and text exports under `outputs/reports/`:

```powershell
python main.py --question-paper inputs/question_paper_fixture.txt --model-answer inputs/model_answer_fixture.txt --student-text inputs/student_text_fixture.txt --report
```

End-to-end handwritten-sheet evaluation through the shared SmartHTR runtime:

```powershell
python main.py --question-paper inputs/question_paper.pdf --model-answer inputs/model_answer.pdf --student-sheet inputs/student_answer_sheet.pdf --report-id 001
```

The same command uses iLovePDF when `OCR_PROVIDER=ilovepdf` is set in the environment. iLovePDF downloads a searchable PDF, then SmartEval extracts its page text locally with PyMuPDF before handing the text to the unchanged evaluation pipeline.

Use `--debug` with `--student-sheet` for page counts, text length, and stage counts. It never prints the full OCR text by default.

## API

Start the development server:

```powershell
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

`GET /health` returns service status. Interactive OpenAPI documentation is available at `/docs` and `/redoc`.

Submit an evaluation with multipart form data:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/evaluate" -F "question_paper=@inputs/question_paper.pdf" -F "model_answer=@inputs/model_answer.pdf" -F "student_answer_sheet=@inputs/student_answer_sheet.pdf"
```

Uploads are checked by filename extension and file signature, stored in a unique temporary directory, then deleted after evaluation unless `KEEP_INPUT_FILES=true`. Configure `MAX_UPLOAD_SIZE_MB`, `TEMP_DIRECTORY`, `API_HOST`, `API_PORT`, and `CORS_ALLOWED_ORIGINS` in `.env`. The default CORS allowlist is limited to local frontend origins.

The frontend calls only SmartEval. FastAPI remains an external interface for future clients, but its evaluation service invokes the shared Python SmartHTR provider directly. The frontend never needs OCR runtime details.

### Database and evaluation history

Copy `.env.example` to `.env`, provide a PostgreSQL `DATABASE_URL`, then apply the schema:

```powershell
alembic upgrade head
```

The API persists complete, partially evaluated, and failed reports before returning the appropriate response. Set `PERSISTENCE_FAILURE_IS_ERROR=false` only when it is acceptable to return a report that was not saved. Set `RETAIN_EVALUATION_CONTENT=false` to omit student and model-answer text from both normalized question records and retrieved report snapshots.

Supply optional `student_id`, `roll_number`, `exam_id`, `exam_name`, `subject`, `semester`, and `exam_date` multipart fields to connect records to history. `student_id` and `exam_id` are the stable identifiers used for filtering.

```text
GET /api/v1/evaluations/{evaluation_id}
GET /api/v1/evaluations?page=1&page_size=20&student_id=...&exam_id=...&status=complete
GET /api/v1/students/{student_id}/evaluations
GET /api/v1/exams/{exam_id}/evaluations
```

Send an `Idempotency-Key` header when clients may retry a submission. Repeated requests with the same key resolve to the same persisted evaluation identifier and cannot create duplicate evaluation rows.

The first semantic run downloads and caches the embedding model. Configure `SEMANTIC_MODEL_NAME`, `SEMANTIC_CORRECT_THRESHOLD`, `MOSTLY_CORRECT_THRESHOLD`, and `PARTIAL_THRESHOLD` in `.env` to change the baseline model or status thresholds.

For marks, configure `SEMANTIC_WEIGHT`, `CONCEPT_WEIGHT`, `RELEVANCE_WEIGHT`, `COMPLETENESS_WEIGHT`, and `MARKS_DECIMAL_PLACES`. The weights must sum to `1.0`; decimal places must be `0`, `1`, or `2`. Feedback uses `FEEDBACK_EXCELLENT_THRESHOLD`, `FEEDBACK_GOOD_THRESHOLD`, `FEEDBACK_PARTIAL_THRESHOLD`, `FEEDBACK_LOW_THRESHOLD`, `FEEDBACK_STRENGTH_THRESHOLD`, and `FEEDBACK_WEAKNESS_THRESHOLD`.

## Architecture

```text
File -> loader/provider -> raw text -> parser -> typed entity
Question + model answer + student answer -> mapping -> EvaluationItem
EvaluationItem -> EvaluationEngine -> EvaluationResult
EvaluationItem + EvaluationResult + MarksResult -> FeedbackService -> FeedbackResult
Phase 4-7 results -> EvaluationReportGenerator -> EvaluationReport -> JSON/text exporters
Student sheet -> shared-runtime SmartHTR pipeline -> StudentTextProvider -> SmartEval Phase 4-8 report
```

`EvaluationEngine` receives its semantic, concept-coverage, relevance, and completeness evaluators through dependency injection. The sentence-transformer provider is replaceable.

## Testing

```powershell
python -m unittest discover -s tests -v
```

Focused provider checks:

```powershell
python -m unittest tests.test_ocr_providers -v
python -m unittest tests.test_end_to_end -v
```

The provider tests mock all iLovePDF HTTP calls, including authentication, task start, upload, processing, and download, so they do not consume API credits. The real iLovePDF path requires valid credentials, internet access, and an available account allowance.

The suite covers parsing, mark extraction, mapping, missing inputs, shared-runtime OCR handoff, semantic signals, OCR-tolerance behavior, status classification, marks, deterministic feedback, report assembly, validation, statistics, JSON/text reports, and FastAPI multipart/API error handling. The optional real SmartHTR test is skipped unless `RUN_COLAB_SMARTHTR_TESTS=true` and `SMARTHR_INTEGRATION_FILE` are configured inside the shared Colab runtime.

## Intentionally not implemented

There is no frontend, authentication, deployment, PDF report generation, OCR training, OCR fine-tuning, or LLM-generated feedback.
