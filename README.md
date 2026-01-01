# Smart CV Prioritization System (SCVPS) – Internship MVP by alhaddaddev

This is a **Minimal Viable Product (MVP)** built as part of an internship project. The system is designed to help recruiters **upload, manage, and prioritize CVs** against job descriptions using NLP and semantic matching.

---

## Features

- **Job Management**
  - Create and delete jobs with title and description.
  - View all existing jobs and their attached CVs.

- **CV Management**
  - Upload CVs in multiple formats: PDF, DOCX, PNG, JPG, JPEG.
  - Maintain a central **CV pool** for reusing CVs across multiple jobs.
  - Attach CVs from the pool to specific jobs.

- **Automated CV Scoring**
  - Scores CVs based on:
    - Named entities (organizations, tools, degrees, etc.)
    - Content richness
    - Semantic similarity to job description
  - Provides **flags** for potential issues (e.g., too short, weak match, OCR errors).
  - Displays **NLP insights** to highlight relevant information.

- **UI / Frontend**
  - Responsive and clean interface using HTML/CSS.
  - Flash messages for notifications (success, warning, error).
  - Easy CV upload and attachment workflows.

- **File Management**
  - Safe file uploads with automatic renaming to prevent collisions.
  - Serve uploaded files securely.
  - Delete CVs or jobs without removing other associated data unintentionally.

---

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite (`cv_data.db`)
- **NLP & CV Analysis**:
  - `spaCy` for NLP (noun chunks, named entities)
  - `easyocr` for OCR on scanned images and PDFs
  - `sentence-transformers` for semantic similarity
- **Frontend**: HTML, CSS, Jinja2 templating

---

## Installation

1. Download the repository as a ZIP file and extract it.

2. Install dependencies (Python 3.9+ recommended):
    ```bash
    pip install -r requirements.txt
    ```

3. Download the spaCy English model:
    ```bash
    python -m spacy download en_core_web_sm
    ```

---

## Workflow

- Create a new job with title & description.
- Upload CVs to the job directly or to the CV pool.
- Attach CVs from the pool to jobs.
- CVs are automatically scored and flagged with insights.
- View CVs attached to each job along with their score and status.

---

## Project Structure

- app.py: Main Flask application routes.
- database.py: SQLite schema and CRUD operations.
- utils/scorer.py: Logic for semantic matching and scoring.
- utils/extractor.py: Text extraction logic for PDF, DOCX, and Images.
- uploads/: Directory where uploaded CVs are stored.
- templates/: HTML layouts and views.
- static/: CSS styling.

---

## Notes

- Security: Secret key in app.py should be changed in production.
- Database: cv_data.db is generated automatically. Do not commit it to GitHub.
- MVP Limitations:
    - No authentication.
    - No advanced error handling for malformed CVs.
    - Scoring is experimental and tuned for demonstration.

---

## License

This project is for internship / MVP purposes and not intended for production use.