
import os

import streamlit as st
from dotenv import load_dotenv

from core import (
    extract_resume_text,
    analyze_candidate,
    build_demo_analysis,
    validate_analysis,
    MODEL_DEFAULT,
    VISION_MODEL_DEFAULT,
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

MODEL_DEFAULT_VALUE = os.getenv(
    "OPENROUTER_MODEL",
    MODEL_DEFAULT,
)

VISION_MODEL_DEFAULT_VALUE = os.getenv(
    "OPENROUTER_VISION_MODEL",
    VISION_MODEL_DEFAULT,
)


st.set_page_config(
    page_title="RoleReady AI",
    page_icon="🎯",
    layout="wide",
)


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 1.4rem 1.6rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 18px;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0 0 .35rem 0;
        font-size: 2.2rem;
    }

    .muted {
        color: #8b929e;
    }

    .metric-card {
        padding: 1rem;
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
    }

    .small-note {
        font-size: .85rem;
        color: #8b929e;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# HERO
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
      <h1>🎯 RoleReady AI</h1>
      <div>
        Know where you stand before you apply —
        and what to improve before the interview.
      </div>
      <p class="small-note">
        Evidence-based resume ↔ job description analysis.
        No invented skills. No meaningless ATS score.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SIDEBAR SETTINGS
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ AI settings")

    if API_KEY:
        st.success("OpenRouter API key configured")
    else:
        st.warning("OpenRouter API key not configured")

    model = st.text_input(
        "Text model",
        value=MODEL_DEFAULT_VALUE,
        help="Use an OpenRouter model ID. Free models often end in :free.",
    )

    vision_model = st.text_input(
        "Vision model (optional)",
        value=VISION_MODEL_DEFAULT_VALUE,
        help=(
            "Used only when the PDF appears scanned "
            "and has little extractable text."
        ),
    )

    st.caption(
        "API credentials are loaded securely from the server "
        "environment. They are not entered or displayed in this interface."
    )

    use_demo = st.toggle(
        "Use demo mode (no API call)",
        value=False,
    )

    st.divider()

    st.caption(
        "Privacy: uploaded resume content is sent to the selected "
        "model provider when you run AI analysis. Avoid uploading "
        "sensitive information you do not need analyzed."
    )


# --------------------------------------------------
# INPUTS
# --------------------------------------------------

st.subheader("1. Upload your resume")

resume_file = st.file_uploader(
    "Upload a resume (PDF, DOCX or TXT)",
    type=["pdf", "docx", "txt"],
    accept_multiple_files=False,
)

st.subheader("2. Paste the job description")

job_description = st.text_area(
    "Job description",
    height=230,
    placeholder=(
        "Paste the complete job description here — responsibilities, "
        "required skills, qualifications and experience..."
    ),
)

with st.expander("What RoleReady checks"):

    st.write(
        "Required vs preferred skills, evidence in your resume, "
        "experience and qualification gaps, missing keywords, "
        "improvement priorities, interview preparation and questions "
        "to ask the recruiter."
    )


# --------------------------------------------------
# ANALYSIS BUTTON
# --------------------------------------------------

analyze_clicked = st.button(
    "Analyze my job readiness",
    type="primary",
    use_container_width=True,
)


# --------------------------------------------------
# ANALYSIS EXECUTION
# --------------------------------------------------

if analyze_clicked:

    # Clear old results immediately.
    # Prevents showing a previous JD's report after a failed analysis.
    st.session_state.pop("analysis", None)
    st.session_state.pop("resume_name", None)

    if not resume_file:

        st.error("Please upload your resume first.")
        st.stop()

    if len(job_description.strip()) < 80:

        st.error(
            "Please paste a more complete job description "
            "(at least 80 characters)."
        )
        st.stop()

    if not use_demo and not API_KEY:

        st.error(
            "OpenRouter API key is not configured. "
            "Add OPENROUTER_API_KEY to your local .env file "
            "or your production environment variables."
        )
        st.stop()

    if not use_demo and not model.strip():

        st.error("Please enter a valid OpenRouter text model ID.")
        st.stop()

    try:

        # ------------------------------------------
        # STEP 1: RESUME EXTRACTION
        # ------------------------------------------

        with st.spinner("Reading your resume..."):

            resume_text = extract_resume_text(
                resume_file.getvalue(),
                resume_file.name,
                vision_model,
                API_KEY,
            )

        if not resume_text or not resume_text.strip():

            st.error(
                "We couldn't extract readable text from this resume. "
                "Try a text-based PDF, DOCX or TXT file."
            )
            st.stop()

        # ------------------------------------------
        # STEP 2: AI ANALYSIS
        # ------------------------------------------

        with st.spinner(
            "Mapping job requirements to resume evidence..."
        ):

            if use_demo:

                result = build_demo_analysis(
                    resume_text,
                    job_description,
                )

            else:

                result = analyze_candidate(
                    resume_text,
                    job_description,
                    API_KEY,
                    model.strip(),
                )

            result = validate_analysis(result)

        # ------------------------------------------
        # STEP 3: SAVE SUCCESSFUL RESULT
        # ------------------------------------------

        st.session_state["analysis"] = result
        st.session_state["resume_name"] = resume_file.name

        st.success("Analysis complete.")

    except Exception as exc:

        st.error(f"Analysis failed: {exc}")

        st.info(
            "Your previous report has been cleared. "
            "Check the error above, then retry or select another "
            "available OpenRouter model."
        )


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "analysis" in st.session_state:

    data = st.session_state["analysis"]

    st.divider()

    st.header("Your job-readiness report")

    st.caption(
        f"Resume: {st.session_state.get('resume_name', 'Uploaded resume')} "
        "· Analysis is based only on the supplied documents."
    )

    # ----------------------------------------------
    # SCORE AND SUMMARY
    # ----------------------------------------------

    score = data.get("readiness_score", 0)

    label = data.get(
        "readiness_label",
        "Needs review",
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Readiness indicator",
        f"{score}/100",
    )

    c2.metric(
        "Assessment",
        label,
    )

    c3.metric(
        "Requirements reviewed",
        len(data.get("requirements", [])),
    )

    st.progress(
        max(0, min(100, int(score))) / 100
    )

    st.caption(
        "This is an explainable guidance indicator, not an employer "
        "ATS score or a prediction of getting hired."
    )

    # ----------------------------------------------
    # PRIORITY ACTIONS
    # ----------------------------------------------

    st.subheader("Your next best actions")

    for i, item in enumerate(
        data.get("priority_actions", []),
        1,
    ):

        with st.container(border=True):

            st.markdown(
                f"**{i}. {item.get('action', '')}**"
            )

            st.write(
                item.get("why", "")
            )

            if item.get("how"):

                st.caption(
                    "How to improve: " + item["how"]
                )

    # ----------------------------------------------
    # REQUIREMENT MATCHING
    # ----------------------------------------------

    st.subheader("Requirement-by-requirement match")

    for item in data.get("requirements", []):

        status = item.get(
            "status",
            "Needs review",
        )

        icon = {
            "Matched": "🟢",
            "Partial": "🟡",
            "Missing": "🔴",
            "Unclear": "⚪",
        }.get(status, "⚪")

        with st.expander(
            f"{icon} {item.get('requirement', 'Requirement')} — {status}"
        ):

            st.write(
                "**Type:**",
                item.get("type", "Not specified"),
            )

            st.write(
                "**Resume evidence:**",
                item.get("resume_evidence")
                or "No clear evidence found.",
            )

            st.write(
                "**Recommendation:**",
                item.get("recommendation")
                or "Review this requirement.",
            )

    # ----------------------------------------------
    # RESUME AND INTERVIEW PREPARATION
    # ----------------------------------------------

    left, right = st.columns(2)

    with left:

        st.subheader("Resume improvements")

        for item in data.get("resume_improvements", []):

            st.markdown(f"- {item}")

    with right:

        st.subheader("Interview preparation")

        for item in data.get("interview_questions", []):

            st.markdown(f"- {item}")

    # ----------------------------------------------
    # CONCERNS
    # ----------------------------------------------

    st.subheader("Potential concerns & missing information")

    concerns = data.get("concerns", [])

    if concerns:

        for item in concerns:

            st.warning(item)

    else:

        st.success(
            "No specific concerns were identified from the supplied text."
        )

    # ----------------------------------------------
    # PREPARATION PLAN
    # ----------------------------------------------

    st.subheader("Suggested preparation plan")

    for item in data.get("preparation_plan", []):

        st.markdown(
            f"- **{item.get('timeframe', 'Next')}** — "
            f"{item.get('task', '')}"
        )

    # ----------------------------------------------
    # OVERALL SUMMARY
    # ----------------------------------------------

    st.info(
        data.get(
            "overall_summary",
            "Review the evidence and priorities above before applying.",
        )
    )

    # ----------------------------------------------
    # MARKDOWN REPORT
    # ----------------------------------------------

    report = "# RoleReady AI — Job Readiness Report\n\n"

    report += (
        f"**Readiness indicator:** {score}/100 — {label}\n\n"
    )

    report += (
        f"**Summary:** {data.get('overall_summary', '')}\n\n"
    )

    report += "## Priority actions\n"

    for item in data.get("priority_actions", []):

        report += (
            f"- **{item.get('action', '')}** — "
            f"{item.get('why', '')} "
            f"How: {item.get('how', '')}\n"
        )

    report += "\n## Requirements\n"

    for item in data.get("requirements", []):

        report += (
            f"- **{item.get('requirement', '')}** "
            f"({item.get('status', '')})\n"
            f"  - Evidence: {item.get('resume_evidence', '')}\n"
            f"  - Recommendation: {item.get('recommendation', '')}\n"
        )

    report += (
        "\n## Resume improvements\n"
        + "\n".join(
            f"- {item}"
            for item in data.get("resume_improvements", [])
        )
    )

    report += (
        "\n\n## Interview questions\n"
        + "\n".join(
            f"- {item}"
            for item in data.get("interview_questions", [])
        )
    )

    report += (
        "\n\n## Concerns\n"
        + "\n".join(
            f"- {item}"
            for item in concerns
        )
    )

    report += (
        "\n\n## Preparation plan\n"
        + "\n".join(
            f"- {item.get('timeframe', '')}: "
            f"{item.get('task', '')}"
            for item in data.get("preparation_plan", [])
        )
    )

    st.download_button(
        "⬇️ Download complete report (Markdown)",
        report,
        file_name="roleready_job_readiness_report.md",
        mime="text/markdown",
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "RoleReady AI is an assistive tool. Verify extracted facts, "
    "salary/qualification requirements and employer policies yourself. "
    "It does not guarantee selection."
)
