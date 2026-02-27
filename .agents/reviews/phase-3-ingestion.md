# Phase 3 — Document Ingestion: Review

## What Was Implemented

### Document Parsing
- [x] `app/services/ingestion/parser.py`:
  - `extract_text_from_pdf()` — PyPDF2-based text extraction
  - `extract_text_from_image()` — pytesseract OCR
  - `extract_text()` — content-type router (PDF, image, text fallback)

### Claude-Powered Extraction
- [x] `app/services/ingestion/extractor.py`:
  - `extract_from_text()` — general document → tasks + events + confidence score
  - `extract_syllabus()` — specialized syllabus parser (exams, assignments, weekly schedule, milestones)
  - Both use Claude Sonnet 4 with structured JSON output
  - Text truncation at 15K chars for context window

### API Routes
- [x] `app/api/materials.py`:
  - POST `/api/materials/upload` — file upload + text extraction
  - POST `/api/materials/extract/{id}` — Claude extraction on uploaded material
  - POST `/api/materials/extract-syllabus/{id}` — specialized syllabus extraction
  - POST `/api/materials/confirm-extraction` — create tasks from confirmed results
  - GET `/api/materials` — list uploaded materials

### Frontend
- [x] `/materials` page with:
  - Drag-and-drop upload zone (also click-to-upload)
  - Extraction preview with task list, event list, confidence score
  - Confirm button to create tasks from extraction
  - Materials list with extraction status badges

## What You Must Do Manually

1. **Install PDF parsing dependencies**:
   ```bash
   uv add PyPDF2 Pillow
   # For OCR (optional):
   # uv add pytesseract
   # Also install Tesseract OCR system binary
   ```

2. **S3 storage** — Files are currently only processed in-memory (not persisted to S3). To add:
   - Install MinIO or use AWS S3
   - In `upload_material()`, save `contents` to S3 using `boto3`
   - Store `s3_key` on the Material record
   - Add a download endpoint

3. **Background extraction** — Currently extraction is synchronous in the API handler. For production:
   - Move extraction to a Celery task
   - Return `202 Accepted` immediately
   - Poll for extraction status via GET `/api/materials/{id}`

4. **Confidence slider** — The extraction preview shows confidence but doesn't let users edit individual items. Add:
   - Editable fields for each extracted task (title, due date, hours)
   - Delete button per item
   - Confidence threshold slider ("only import items above X% confidence")

5. **Voice input** — Not yet implemented. To add:
   - Use Web Speech API (`window.SpeechRecognition`) in the frontend
   - Transcribe to text, send to chat endpoint
   - Chat handles it via `create_task` tool call

6. **Timetable PDF parsing** — The syllabus extractor handles this via Claude, but results may vary. For structured timetable PDFs, consider adding a rule-based parser that detects tabular layouts.
