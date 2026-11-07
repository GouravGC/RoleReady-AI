
import base64
import json
import re
from io import BytesIO

import requests


MODEL_DEFAULT = "nvidia/nemotron-3-ultra:free"
VISION_MODEL_DEFAULT = "nvidia/nemotron-3.5-super-vl:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


# --------------------------------------------------
# OPENROUTER REQUEST
# --------------------------------------------------

def _openrouter_chat(
    api_key,
    model,
    messages,
    max_tokens=6500,
    temperature=0.15,
):
    if not api_key:
        raise ValueError("OpenRouter API key is missing.")

    if not model or not model.strip():
        raise ValueError("Please enter a valid OpenRouter model ID.")

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://roleready-ai.local",
                "X-Title": "RoleReady AI",
            },
            json={
                "model": model.strip(),
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=150,
        )
    except requests.Timeout as exc:
        raise RuntimeError(
            "The request to OpenRouter timed out. Please try again."
        ) from exc
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not connect to OpenRouter: {exc}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(
            f"OpenRouter returned a non-JSON response "
            f"(HTTP {response.status_code})."
        ) from exc

    if response.status_code != 200:
        detail = (
            payload.get("error", {}).get("message")
            if isinstance(payload, dict)
            else None
        )

        raise RuntimeError(
            f"OpenRouter returned HTTP {response.status_code}: "
            f"{detail or response.text[:1000]}"
        )

    try:
        choice = payload["choices"][0]
        message = choice["message"]
        content = message.get("content")
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(
            "OpenRouter returned an unexpected response structure."
        ) from exc

    # Some providers return content as a list of text blocks.
    if isinstance(content, list):
        text_parts = []

        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text_parts.append(part.get("text", ""))

        content = "\n".join(text_parts)

    if not isinstance(content, str) or not content.strip():
        finish_reason = choice.get("finish_reason", "unknown")

        raise RuntimeError(
            "The selected model returned an empty response. "
            f"Finish reason: {finish_reason}. "
            "Try another model."
        )

    return content.strip()


# --------------------------------------------------
# RESUME EXTRACTION
# --------------------------------------------------

def extract_resume_text(
    file_bytes: bytes,
    filename: str,
    vision_model: str = "",
    api_key: str = "",
) -> str:

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    suffix = filename.lower().rsplit(".", 1)[-1]

    if suffix == "txt":
        return file_bytes.decode("utf-8", errors="replace").strip()

    if suffix == "docx":
        from docx import Document

        doc = Document(BytesIO(file_bytes))

        paragraphs = [
            paragraph.text.strip()
            for paragraph in doc.paragraphs
            if paragraph.text.strip()
        ]

        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells
                )

                if row_text.strip():
                    paragraphs.append(row_text)

        return "\n".join(paragraphs).strip()[:50000]

    if suffix == "pdf":
        import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")

        try:
            pages = [
                page.get_text("text")
                for page in doc
            ]

            text = "\n".join(pages).strip()

            # Normal text-based PDF.
            if len(text) >= 100:
                return text[:50000]

            # Scanned PDF: optional vision fallback.
            if not api_key or not vision_model:
                return text

            content = [
                {
                    "type": "text",
                    "text": (
                        "Extract all readable resume text from these "
                        "page images. Preserve headings, dates, skills, "
                        "education and work experience. Do not infer "
                        "missing information."
                    ),
                }
            ]

            for page in list(doc)[:3]:
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(1.5, 1.5),
                    alpha=False,
                )

                encoded = base64.b64encode(
                    pix.tobytes("png")
                ).decode("ascii")

                content.append(
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{encoded}"
                        },
                    }
                )

            result = _openrouter_chat(
                api_key,
                vision_model,
                [{"role": "user", "content": content}],
                max_tokens=5000,
            )

            return result[:50000]

        finally:
            doc.close()

    raise ValueError(
        "Unsupported file type. Upload PDF, DOCX or TXT."
    )


# --------------------------------------------------
# ROBUST JSON PARSING
# --------------------------------------------------

def _extract_json_object(content: str):
    """
    Extract the first complete JSON object from model output.

    Handles:
    - Markdown code fences
    - Explanatory text before/after JSON
    - Braces inside quoted strings
    - Escaped quotation marks
    """

    if not isinstance(content, str) or not content.strip():
        raise ValueError("The model returned an empty response.")

    cleaned = content.strip()

    # Remove common Markdown code fences.
    cleaned = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```\s*$",
        "",
        cleaned,
    )

    # First try parsing the complete response.
    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    # Find the first balanced JSON object.
    start = cleaned.find("{")

    if start == -1:
        raise ValueError(
            "The model response did not contain a JSON object."
        )

    depth = 0
    inside_string = False
    escaped = False

    for index in range(start, len(cleaned)):
        char = cleaned[index]

        if inside_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                inside_string = False

            continue

        if char == '"':
            inside_string = True

        elif char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:
                candidate = cleaned[start:index + 1]

                try:
                    parsed = json.loads(candidate)

                    if isinstance(parsed, dict):
                        return parsed

                except json.JSONDecodeError as exc:
                    raise ValueError(
                        "The model returned malformed JSON: "
                        f"{exc.msg} at line {exc.lineno}, "
                        f"column {exc.colno}."
                    ) from exc

    raise ValueError(
        "The model response contained incomplete JSON. "
        "The response may have been truncated."
    )


def _parse_json(content: str):
    return _extract_json_object(content)


# --------------------------------------------------
# ANALYSIS PROMPT
# --------------------------------------------------

SYSTEM_PROMPT = """
You are RoleReady AI, a rigorous career-readiness analyst.

Compare a candidate's resume with a job description.

STRICT EVIDENCE RULES:
- Never invent skills, experience, qualifications, employers,
  dates, metrics, projects or achievements.
- Only cite evidence explicitly present in the resume.
- Matched: clear evidence exists.
- Partial: the skill is mentioned, but depth or evidence is weak.
- Missing: no evidence exists in the resume.
- Unclear: the resume is ambiguous.
- Distinguish required and preferred requirements.
- Do not penalize preferred skills as heavily as required skills.
- Do not treat keyword presence alone as proof of proficiency.
- Recommendations must be truthful and actionable.

The readiness score is a guidance indicator based on evidence
coverage. It is NOT an ATS score or a hiring probability.

Return exactly one valid JSON object.
Do not use Markdown code fences.
Do not include explanations outside the JSON object.

Use this schema:

{
  "readiness_score": 0,
  "readiness_label": "Strong alignment | Promising with gaps | Significant gaps | Insufficient evidence",
  "overall_summary": "Short, honest summary",
  "requirements": [
    {
      "requirement": "Requirement name",
      "type": "Required | Preferred | Responsibility | Qualification",
      "status": "Matched | Partial | Missing | Unclear",
      "resume_evidence": "Exact concise evidence or empty string",
      "recommendation": "Truthful next step"
    }
  ],
  "priority_actions": [
    {
      "action": "Action",
      "why": "Reason",
      "how": "How to do it"
    }
  ],
  "resume_improvements": [
    "Specific truthful suggestion"
  ],
  "interview_questions": [
    "Role-specific practice question"
  ],
  "concerns": [
    "Missing or ambiguous information to verify"
  ],
  "preparation_plan": [
    {
      "timeframe": "Today | Before applying | Before interview",
      "task": "Task"
    }
  ]
}

CONTENT REQUIREMENTS:
- 6 to 15 requirements.
- 3 to 5 priority actions.
- 3 to 6 resume improvements.
- 5 to 8 interview questions.
- 2 to 5 preparation plan items.
- Keep the output concise and actionable.
- Never fabricate candidate experience.
- Do not provide legal, immigration or guaranteed hiring advice.
"""


# --------------------------------------------------
# ANALYSIS VALIDATION
# --------------------------------------------------

def validate_analysis(data):

    if not isinstance(data, dict):
        raise ValueError(
            "Analysis output must be a JSON object."
        )

    # Score.
    try:
        score = int(float(data.get("readiness_score", 0)))
    except (TypeError, ValueError):
        score = 0

    data["readiness_score"] = max(0, min(100, score))

    # Text fields.
    text_fields = [
        "readiness_label",
        "overall_summary",
    ]

    for field in text_fields:
        value = data.get(field, "")

        if not isinstance(value, str):
            data[field] = str(value) if value is not None else ""

    # List of strings.
    string_list_fields = [
        "resume_improvements",
        "interview_questions",
        "concerns",
    ]

    for field in string_list_fields:
        value = data.get(field, [])

        if not isinstance(value, list):
            value = []

        data[field] = [
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        ]

    # Requirements.
    requirements = data.get("requirements", [])

    if not isinstance(requirements, list):
        requirements = []

    clean_requirements = []

    for item in requirements:
        if not isinstance(item, dict):
            continue

        clean_requirements.append({
            "requirement": str(item.get("requirement", "")),
            "type": str(item.get("type", "Not specified")),
            "status": str(item.get("status", "Unclear")),
            "resume_evidence": str(
                item.get("resume_evidence", "") or ""
            ),
            "recommendation": str(
                item.get("recommendation", "") or ""
            ),
        })

    data["requirements"] = clean_requirements

    # Priority actions.
    actions = data.get("priority_actions", [])

    if not isinstance(actions, list):
        actions = []

    clean_actions = []

    for item in actions:
        if not isinstance(item, dict):
            continue

        clean_actions.append({
            "action": str(item.get("action", "")),
            "why": str(item.get("why", "")),
            "how": str(item.get("how", "")),
        })

    data["priority_actions"] = clean_actions

    # Preparation plan.
    plan = data.get("preparation_plan", [])

    if not isinstance(plan, list):
        plan = []

    clean_plan = []

    for item in plan:
        if not isinstance(item, dict):
            continue

        clean_plan.append({
            "timeframe": str(item.get("timeframe", "Next")),
            "task": str(item.get("task", "")),
        })

    data["preparation_plan"] = clean_plan

    return data


# --------------------------------------------------
# CANDIDATE ANALYSIS
# --------------------------------------------------

def analyze_candidate(
    resume_text: str,
    job_description: str,
    api_key: str,
    model: str = MODEL_DEFAULT,
):

    if not api_key:
        raise ValueError("OpenRouter API key is required.")

    if not isinstance(resume_text, str) or len(resume_text.strip()) < 40:
        raise ValueError("Resume text is too short to analyze.")

    if (
        not isinstance(job_description, str)
        or len(job_description.strip()) < 80
    ):
        raise ValueError(
            "Please provide a complete job description."
        )

    if not model or not model.strip():
        raise ValueError("Please enter a valid model ID.")

    user_prompt = f"""
RESUME TEXT:
---
{resume_text[:30000]}
---

JOB DESCRIPTION:
---
{job_description[:18000]}
---

Analyze this candidate for this specific role.

Make every requirement traceable to evidence in the resume.
Do not assume that the candidate has a skill just because it is
mentioned in the job description.

Return the requested JSON object only.
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]

    # First attempt.
    content = _openrouter_chat(
        api_key,
        model,
        messages,
        max_tokens=7500,
    )

    try:
        result = _parse_json(content)
        return validate_analysis(result)

    except (ValueError, json.JSONDecodeError) as first_error:

        # One formatting-repair attempt.
        repair_messages = [
            {
                "role": "system",
                "content": (
                    "You are a strict JSON repair assistant. "
                    "Return exactly one valid JSON object matching "
                    "the RoleReady AI analysis schema. Preserve the "
                    "original analysis and all supported facts. "
                    "Do not invent, expand or add candidate experience. "
                    "Do not include Markdown or explanations."
                ),
            },
            {
                "role": "user",
                "content": (
                    "The following model response was expected to be "
                    "valid JSON but could not be parsed.\n\n"
                    "Repair its JSON syntax while preserving its "
                    "original meaning and information.\n\n"
                    "If the response is incomplete or truncated, "
                    "return only the information that is actually "
                    "present. Do not invent missing analysis.\n\n"
                    "MODEL RESPONSE:\n"
                    + content[:30000]
                ),
            },
        ]

        try:
            repaired_content = _openrouter_chat(
                api_key,
                model,
                repair_messages,
                max_tokens=7500,
                temperature=0,
            )

            repaired_result = _parse_json(repaired_content)

            return validate_analysis(repaired_result)

        except Exception as repair_error:
            raise RuntimeError(
                "The model returned invalid or incomplete JSON, "
                "and the automatic repair attempt also failed. "
                f"Initial parsing issue: {first_error}. "
                f"Repair issue: {repair_error}. "
                "Try another available model or retry the analysis."
            ) from repair_error


# --------------------------------------------------
# DEMO MODE
# --------------------------------------------------

def build_demo_analysis(resume_text, job_description):

    resume_lower = resume_text.lower()

    jd_terms = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9+#.-]{2,}\b",
        job_description,
    )

    unique = []

    for term in jd_terms:
        if term.lower() not in [
            existing.lower() for existing in unique
        ]:
            unique.append(term)

    requirements = []

    for term in unique[:10]:

        found = term.lower() in resume_lower

        requirements.append({
            "requirement": term,
            "type": "Needs manual review",
            "status": "Matched" if found else "Unclear",
            "resume_evidence": (
                f"The term '{term}' appears in the resume text."
                if found else ""
            ),
            "recommendation": (
                "Verify that your resume demonstrates this skill "
                "with a project or work example."
                if found
                else
                "Review the job requirement and add evidence only "
                "if you genuinely have this experience."
            ),
        })

    return {
        "readiness_score": 50,
        "readiness_label": "Demo mode — not an AI assessment",
        "overall_summary": (
            "Demo mode demonstrates the report layout. "
            "Connect an OpenRouter model for contextual analysis."
        ),
        "requirements": requirements,
        "priority_actions": [
            {
                "action": "Check every required skill against real evidence",
                "why": "Keyword presence alone does not prove proficiency.",
                "how": (
                    "Add a project, work example or measurable "
                    "outcome where truthful."
                ),
            },
            {
                "action": "Close the most important skill gaps",
                "why": "Required skills usually matter more than preferred skills.",
                "how": (
                    "Prioritize the top two missing requirements "
                    "and build evidence."
                ),
            },
            {
                "action": "Prepare role-specific stories",
                "why": "Interviewers often ask for examples of applied skills.",
                "how": "Use a situation, action and result structure.",
            },
        ],
        "resume_improvements": [
            (
                "Replace generic claims with specific project "
                "evidence and measurable outcomes."
            ),
            (
                "Make relevant skills easy to find, but do not add "
                "skills you cannot demonstrate."
            ),
        ],
        "interview_questions": [
            "Describe a project most relevant to this role.",
            "How have you used the most important required skill?",
            "Tell me about a technical challenge and how you resolved it.",
            "Which requirement in this role would you need to learn further?",
            "Why are you interested in this position?",
        ],
        "concerns": [
            "Demo mode uses simple keyword presence and does not understand context."
        ],
        "preparation_plan": [
            {
                "timeframe": "Today",
                "task": "Map each required job skill to one truthful resume example.",
            },
            {
                "timeframe": "Before applying",
                "task": "Tailor the summary and project ordering to this role.",
            },
            {
                "timeframe": "Before interview",
                "task": "Practice explaining two relevant projects and one learning gap.",
            },
        ],
    }
