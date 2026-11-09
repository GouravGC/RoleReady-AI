# 🎯 RoleReady AI

### Know where you stand before you apply — and what to improve before the interview.

**RoleReady AI** is an AI-powered career readiness copilot that analyzes a candidate's resume against a specific job description. It identifies evidence-backed skill matches and gaps, recommends actionable improvements, and generates role-specific interview preparation guidance.

<p align="center">
  <a href="https://github.com/GouravGC/RoleReady-AI">GitHub Repository</a> •
  <a href="https://devpost.com/software/roleready-ai">Devpost Project</a>
</p>

---

## 📌 Overview

Job seekers frequently struggle to understand how well their resumes align with individual job descriptions. Generic keyword matching tools often provide scores without explaining whether a candidate actually demonstrates the required skills.

RoleReady AI addresses this problem through evidence-based resume analysis.

Upload a resume, paste a job description, and receive a structured report explaining:

- Which requirements are supported by resume evidence.
- Which skills have partial or insufficient evidence.
- Which important requirements are missing.
- What to improve before applying.
- How to prepare for the interview.

**Core principle:** Never invent a candidate's skills, qualifications, experience, or achievements.

---

## ✨ Key Features

### 📄 Multi-format Resume Processing
- Upload PDF, DOCX, and TXT resumes.
- Extract text from standard PDF and DOCX documents.
- Optional vision-model fallback for scanned PDF pages.

### 🎯 Evidence-Based Requirement Matching

Every identified requirement receives one of four classifications:

| Status | Meaning |
|---|---|
| Matched | Clear supporting evidence exists |
| Partial | Some evidence exists, but depth is limited |
| Missing | No supporting evidence was identified |
| Unclear | Available information is ambiguous |

Requirements are also classified by type, such as required skills, preferred skills, responsibilities, and qualifications.

### 📊 Job Readiness Insights
- Readiness guidance indicator.
- Overall candidate-role alignment summary.
- Requirement-by-requirement evidence.
- Prioritized improvement actions.

The readiness indicator is a guidance metric, not an employer ATS score or a hiring probability.

### 🚀 Career Preparation
- Truthful resume improvement suggestions.
- Role-specific interview practice questions.
- Potential concerns and missing information.
- Structured preparation plan.
- Downloadable Markdown analysis report.

### 🤖 Configurable AI Models
- OpenRouter API integration.
- Configurable text model.
- Optional vision model for scanned PDF extraction.
- Structured JSON response parsing and validation.
- Automatic JSON repair attempt for malformed model responses.
- Demo mode without an API call.

---

## 🖥️ Demo

**Project:** [RoleReady AI on Devpost](https://devpost.com/software/roleready-ai)

**Demo video:** Add the published YouTube demo URL here.

**Repository:** [GouravGC/RoleReady-AI](https://github.com/GouravGC/RoleReady-AI)

---

## 🏗️ Architecture

```text
                 USER
                  |
                  v
        Streamlit Application
                  |
          Resume + Job Description
                  |
                  v
          Document Processing
          /       |        \
        PDF      DOCX      TXT
          \       |        /
                  |
                  v
          OpenRouter API
          /            \
      Text Model     Vision Model
          |          (Optional)
          |
          v
    Structured AI Analysis
          |
          v
    JSON Parsing & Validation
          |
          v
       Analysis Report
          |
     +----+-----+-------+
     |          |       |
  Evidence   Actions  Interview
  Matching   & Gaps   Preparation
     |          |       |
     +----------+-------+
                |
                v
       Downloadable Report
```

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Language | Python 3.11 |
| User Interface | Streamlit |
| AI Integration | OpenRouter |
| Language Models | Configurable OpenRouter models |
| PDF Processing | PyMuPDF |
| DOCX Processing | python-docx |
| API Requests | Requests |
| Configuration | python-dotenv |
| Testing | Pytest |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Container Registry | GitHub Container Registry |

---

## ⚙️ Local Installation

### Prerequisites

- Python 3.11
- Conda or Python virtual environment
- OpenRouter API key for AI-powered analysis

### 1. Clone the repository

```cmd
git clone https://github.com/GouravGC/RoleReady-AI.git
cd RoleReady-AI
```

### 2. Create the environment

```cmd
conda create -n roleready python=3.11.10 -y
conda activate roleready
```

### 3. Install dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

```cmd
copy .env.example .env
notepad .env
```

Configure your own OpenRouter credentials:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=nvidia/nemotron-3-ultra:free
OPENROUTER_VISION_MODEL=nvidia/nemotron-3.5-super-vl:free
```

Model availability and free-tier limits may change. Model IDs can also be changed in the application sidebar.

**Never commit your `.env` file or expose your API key.**

### 5. Run the application

```cmd
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

---

## 🧪 Testing

Run the automated test suite:

```cmd
python -m pytest -q
```

The tests cover core application behavior, including:

- JSON response parsing.
- Analysis output validation.
- Readiness score boundaries.
- Demo analysis structure.

---

## 🐳 Docker

RoleReady AI is packaged as a single Streamlit application container.

### Build the image

```cmd
docker build -t roleready-ai:latest .
```

### Run the container

```cmd
docker run --rm -p 8501:8501 ^
  -e OPENROUTER_API_KEY=your_openrouter_api_key ^
  -e OPENROUTER_MODEL=nvidia/nemotron-3-ultra:free ^
  roleready-ai:latest
```

Open:

```text
http://localhost:8501
```

Environment variables are passed at runtime rather than baked into the image.

---

## 🔄 CI/CD Pipeline

The repository includes a GitHub Actions workflow for automated testing and Docker image publishing.

### Pipeline

```text
        GitHub Push to main
                 |
                 v
          GitHub Actions
                 |
                 v
          Install Dependencies
                 |
                 v
            Run Pytest
                 |
           Tests Successful?
                 |
                 v
           Build Docker Image
                 |
                 v
          Publish to GHCR
                 |
                 v
          Render Deploy Hook
                 |
                 v
         Updated Application
```

### Container Image

```text
ghcr.io/gouravgc/roleready-ai:latest
```

The pipeline is designed to publish a latest image and commit-specific image tags after successful main-branch builds.

Render deployment is triggered through a repository secret containing the Render deploy hook URL, once the image-backed service is configured.

See [GitHub Actions](https://github.com/GouravGC/RoleReady-AI/actions) for workflow execution history.

---

## 🔐 Privacy and Responsible AI

- Resume information is processed only when the user initiates analysis.
- AI-enabled analysis sends resume text and job-description content to the selected model provider through OpenRouter.
- Scanned PDF pages may also be sent to the configured vision model.
- API keys should be stored in local environment variables or deployment secrets.
- The system does not intentionally fabricate candidate skills or achievements.
- Generated assessments should always be verified against the original documents.

RoleReady AI is an assistive career preparation tool. It does not guarantee interviews, employment, or selection.

---

## ⚠️ Current Limitations

- Supports PDF, DOCX, and TXT resume uploads.
- Job descriptions are supplied as pasted text.
- Scanned PDF extraction checks up to the first three pages.
- Model output quality and availability depend on the selected provider.
- Free model routes may have rate limits or temporary availability issues.
- The application does not independently verify employer information or job legitimacy.

---

## 🚀 Future Improvements

- Persistent candidate profiles and analysis history.
- Advanced semantic skill matching.
- Multiple resume versions for different job roles.
- More robust scanned-document extraction.
- Interactive mock interview simulation.
- Detailed feedback on interview responses.
- Additional model providers.
- Enhanced cloud monitoring and deployment observability.

---

## 🏆 Hackathon

Built for **Next Byte Hacks V5**.

[View RoleReady AI on Devpost](https://devpost.com/software/roleready-ai)

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

---

## 👨‍💻 Author

**Gourav Chhatwani**

- GitHub: [@GouravGC](https://github.com/GouravGC)
- Project: [RoleReady AI](https://github.com/GouravGC/RoleReady-AI)