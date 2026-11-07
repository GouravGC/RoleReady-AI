# RoleReady AI

**Know where you stand before you apply — and what to improve before the interview.**

RoleReady compares a candidate's resume with a specific job description and creates an evidence-based readiness report.

## Features
- Resume upload: PDF, DOCX and TXT.
- Extracts text from regular PDFs and DOCX files.
- Optional vision/OCR fallback for scanned PDF pages using an OpenRouter vision model.
- Requirement-by-requirement matching: Matched, Partial, Missing or Unclear.
- Resume evidence for each requirement.
- Prioritized, truthful improvement actions.
- Role-specific interview practice questions.
- Preparation plan and downloadable Markdown report.
- Demo mode to demonstrate the UI without an API key.

## Setup (Windows CMD)

```cmd
conda create -n roleready python=3.11.10 -y
conda activate roleready
cd path\to\RoleReady-AI
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Add your OpenRouter key to `.env`. The default models are examples of free OpenRouter routes; model availability, free limits and provider capacity can change. You can change model IDs in `.env` or the app sidebar.

```env
OPENROUTER_API_KEY=your_key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra:free
OPENROUTER_VISION_MODEL=nvidia/nemotron-3.5-super-vl:free
```

Run:

```cmd
streamlit run app.py
```

Run tests:

```cmd
pytest -q
```

## How to use
1. Upload your resume.
2. Paste the full job description.
3. Add your OpenRouter key in the sidebar (or configure `.env`).
4. Click **Analyze my job readiness**.
5. Review the evidence, priorities, gaps and interview questions.
6. Download the Markdown report.

## Design principles
- No invented skills, qualifications, experience or achievements.
- A keyword appearing in a resume is not automatically proof of proficiency.
- Required and preferred criteria are treated differently.
- The readiness indicator is guidance, not an ATS score or hiring probability.
- Always verify the report against the original resume and job description.

## Privacy
When AI analysis is enabled, resume and job-description text is sent to the selected model provider through OpenRouter. Scanned PDF pages may also be sent as images to the configured vision model. Do not upload information you do not want processed by an external provider. Keep `.env` private and never commit API keys.

## Current limitations
- Resume formats supported: PDF, DOCX and TXT.
- Job descriptions are pasted as text.
- Scanned PDF vision extraction checks up to the first three pages.
- Free model endpoints may be rate-limited, unavailable or changed by providers.
- The app does not verify employer legitimacy or guarantee job selection.
