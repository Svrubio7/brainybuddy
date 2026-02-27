# Phase 8 — Premium Tutor: Review

## What Was Implemented

### Embeddings & RAG (`app/services/tutor/embeddings.py`)
- [x] `chunk_text(text, chunk_size, overlap)` — smart sentence-boundary chunking
- [x] `generate_embeddings(chunks, user_id, course_id, material_id)` — stores in pgvector with dedup via chunk_hash
- [x] `retrieve_context(query, user_id, course_id, top_k)` — cosine similarity search
- [x] Stub embedding function (SHA-512-based deterministic vectors, 1536 dims)

### Flashcards (`app/services/tutor/flashcards.py`)
- [x] `generate_flashcards(material_text, count, course_name, topic)` — Claude-powered generation of {front, back} pairs
- [x] `grade_flashcard(card_id, quality)` — full SM-2 algorithm with easiness, interval, repetition tracking
- [x] Updates next_review date in database

### Practice Exams (`app/services/tutor/practice_exams.py`)
- [x] `generate_practice_exam(course_id, topics, question_types, num_questions, difficulty)`:
  - MCQ (4 options + correct answer)
  - Short answer (model answer + key points)
  - Essay (key points + rubric)
- [x] `grade_exam(exam_id, exam_data, answers)` — AI-powered grading with per-question feedback
- [x] Fallback grading for MCQ when Claude unavailable

### Socratic Tutor (`app/services/tutor/socratic.py`)
- [x] `socratic_response(question, context, hint_level)`:
  - nudge: guiding question only
  - partial: reveal one concept
  - full_explanation: complete walkthrough
- [x] `explain_concept(concept, level, course_name)`:
  - eli5: simple analogies
  - undergrad: proper terminology
  - expert: formal/graduate-level
- [x] Follow-up question extraction

### API Routes (`app/api/tutor.py`)
- [x] POST `/api/tutor/flashcards/generate`
- [x] GET `/api/tutor/flashcards`
- [x] POST `/api/tutor/flashcards/{id}/grade`
- [x] POST `/api/tutor/exams/generate`
- [x] POST `/api/tutor/exams/{id}/grade`
- [x] POST `/api/tutor/socratic`
- [x] POST `/api/tutor/explain`

## What You Must Do Manually

1. **pgvector extension** — Required for embeddings:
   ```sql
   -- Connect to PostgreSQL and run:
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   Also add to docker-compose:
   ```yaml
   db:
     image: pgvector/pgvector:pg18
   ```

2. **Real embedding model** — The current `_compute_embedding()` is a stub using SHA-512 hashes. Replace with:
   - Anthropic embeddings (if/when available)
   - Or OpenAI `text-embedding-3-small` (1536 dims)
   - Or a local model like `sentence-transformers/all-MiniLM-L6-v2` (384 dims)

   Update the embedding dimension in the pgvector column accordingly.

3. **Flashcard database model** — The `grade_flashcard()` function references a `Flashcard` table that doesn't exist yet. Create:
   ```python
   class Flashcard(SQLModel, table=True):
       __tablename__ = "flashcards"
       id: int | None = Field(default=None, primary_key=True)
       user_id: int = Field(foreign_key="users.id")
       course_id: int | None = Field(default=None, foreign_key="courses.id")
       front: str
       back: str
       easiness: float = 2.5
       interval: int = 1
       repetitions: int = 0
       next_review: datetime | None = None
       created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
   ```

4. **Practice exam storage** — Exam generation returns JSON but doesn't persist. Add:
   - `PracticeExam` model (questions JSON, graded_results JSON)
   - Store generated exams so students can review past attempts

5. **Tutor frontend pages** — No frontend pages exist. Build:
   - `/tutor` — mode selector (flashcards, practice exam, Socratic, explain)
   - `/tutor/flashcards` — flip card UI, grade buttons (again/hard/good/easy), deck management
   - `/tutor/exams` — timed exam interface with question navigation, submit + grading view
   - `/tutor/socratic` — specialized chat UI with hint level selector, follow-up prompts
   - `/tutor/explain` — concept input + level switcher (ELI5/undergrad/expert)

6. **Material chunking pipeline** — Wire embeddings to material upload:
   - After text extraction in `upload_material()`, auto-chunk and embed
   - Add to Celery task for background processing
   - Use embeddings in RAG for Socratic tutor and flashcard generation

7. **Block quizzes** — Not implemented. To add:
   - Generate a quick quiz (3-5 questions) for the topic of the current study block
   - Present at the end of a focus session
   - Track quiz scores over time

8. **Auto-glossary** — Not implemented. To add:
   - Extract key terms from course materials using Claude
   - Store as a `GlossaryEntry` model (term, definition, course_id)
   - Display in a searchable panel alongside study materials

9. **Cost management** — Premium tutor features are Claude-heavy. Implement:
   - Request counting per user per day/month
   - Tier-based quotas (Free: 0, Standard: limited, Premium: generous)
   - Rate limiting middleware on `/api/tutor/*` routes
