
import os
import html
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from ddgs import DDGS
from google import genai


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

load_dotenv(override=True)


def get_gemini_api_key():
    """Read the key from Streamlit Cloud Secrets or local .env."""
    try:
        secret_key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        secret_key = ""

    return (secret_key or os.getenv("GEMINI_API_KEY", "")).strip()


GEMINI_API_KEY = get_gemini_api_key()

st.set_page_config(
    page_title="VeriShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

if "result" not in st.session_state:
    st.session_state.result = None

if "claim_text" not in st.session_state:
    st.session_state.claim_text = ""


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: #080d18;
    color: #e8edf7;
}

[data-testid="stSidebar"] {
    background: #0d1423;
    border-right: 1px solid #1d2a3d;
}

.hero {
    background: linear-gradient(120deg, #101e32, #102c2b);
    border: 1px solid #25483f;
    border-radius: 18px;
    padding: 32px;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 36px;
    font-weight: 800;
    color: #f2f7ff;
    margin-bottom: 8px;
}

.hero p {
    color: #a7b7c9;
    font-size: 15px;
}

.eyebrow {
    color: #45d6a2;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
}

.section-title {
    color: #e9f1fb;
    font-size: 20px;
    font-weight: 700;
    margin: 20px 0 12px;
}

.metric-card {
    background: #111c2e;
    border: 1px solid #24334a;
    padding: 20px;
    border-radius: 14px;
    min-height: 110px;
}

.metric-label {
    color: #93a5bd;
    font-size: 13px;
}

.metric-value {
    color: #f2f7ff;
    font-size: 26px;
    font-weight: 800;
    margin-top: 8px;
}

.result-card {
    background: #111c2e;
    border: 1px solid #2b4059;
    border-radius: 16px;
    padding: 24px;
    margin: 15px 0;
}

.source-card {
    background: #111c2e;
    border: 1px solid #24334a;
    border-radius: 12px;
    padding: 16px;
    margin: 10px 0;
}

.source-card a {
    color: #54d9ad;
    text-decoration: none;
    font-weight: 600;
}

.muted {
    color: #93a5bd;
    font-size: 13px;
}

div.stButton > button {
    background: #16a77b;
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 700;
    min-height: 45px;
}

div.stButton > button:hover {
    background: #118663;
    color: white;
    border: none;
}

textarea {
    background: #111c2e !important;
    color: #ffffff !important;
}

.footer {
    text-align: center;
    color: #70839c;
    padding: 30px 0;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# CALLBACKS
# --------------------------------------------------

def clear_claim():
    """Clear the claim input and the currently displayed result."""
    st.session_state.claim_text = ""
    st.session_state.result = None


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🛡️ VeriShield AI")
    st.caption("AI-Powered Fact Verification")
    st.markdown("---")

    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "Evidence Library", "About"]
    )

    st.markdown("---")
    st.markdown("### System Status")

    if GEMINI_API_KEY:
        st.success("Gemini AI configured")
    else:
        st.warning("Search-only mode")

    st.success("Web search module ready")

    st.markdown("---")
    st.caption("VeriShield AI • Version 1.0")


# --------------------------------------------------
# WEB SEARCH
# --------------------------------------------------

def search_evidence(claim):
    """Search the web and report diagnostic details."""

    results = []
    seen_urls = set()
    errors = []

    search_queries = [
        claim,
        f"{claim} fact check"
    ]

    try:
        with DDGS() as ddgs:
            for query in search_queries:
                try:
                    search_results = ddgs.text(
                        query,
                        max_results=5
                    )

                    if not search_results:
                        continue

                    for item in search_results:
                        if not isinstance(item, dict):
                            continue

                        url = (item.get("href") or "").strip()

                        if (
                            url.startswith(("http://", "https://"))
                            and url not in seen_urls
                        ):
                            seen_urls.add(url)

                            results.append({
                                "title": item.get("title") or "Untitled",
                                "body": item.get("body") or "No description available",
                                "url": url
                            })

                    if len(results) >= 5:
                        break

                except Exception as error:
                    errors.append(f"{query}: {error}")

    except Exception as error:
        errors.append(f"Search connection error: {error}")

    if errors:
        st.warning("Search diagnostic: " + " | ".join(errors))

    st.info(f"Search diagnostic: Found {len(results)} usable sources.")

    return results


# --------------------------------------------------
# AI ANALYSIS
# --------------------------------------------------

def analyze_claim(claim, evidence):
    """Analyze a claim using Gemini with retry for temporary errors."""

    if not GEMINI_API_KEY:
        return {
            "success": False,
            "verdict": None,
            "confidence": None,
            "explanation": (
                "Gemini API key is not configured. "
                "No AI verdict has been generated."
            )
        }

    if not evidence:
        return {
            "success": False,
            "verdict": None,
            "confidence": None,
            "explanation": (
                "No usable web evidence was found. "
                "AI analysis was not performed, so no verdict was generated."
            )
        }

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        evidence_text = ""

        for index, item in enumerate(evidence, 1):
            evidence_text += (
                f"\nSource {index}\n"
                f"Title: {item['title']}\n"
                f"Description: {item['body']}\n"
                f"URL: {item['url']}\n"
            )

        prompt = f"""
You are VeriShield AI, a careful fact-checking assistant.

Analyze the claim using ONLY the supplied search evidence.

CLAIM:
{claim}

SEARCH EVIDENCE:
{evidence_text}

Rules:
1. Decide whether the supplied evidence supports or contradicts the claim.
2. Never invent facts, sources, or details.
3. If the evidence is insufficient or mixed, use UNVERIFIED.
4. Absence of evidence is not automatically evidence of falsity.
5. Confidence is an estimate, not a mathematically verified probability.
6. Consider source quality, relevance, date, and independence.
7. Do not give 100 confidence based only on search snippets.
8. Use conservative confidence scores:
   - 90-95: Multiple strong, independent sources agree.
   - 75-89: Good evidence, with some limitations.
   - 50-74: Partial or mixed evidence.
   - 1-49: Weak evidence.
   - 0: No meaningful evidence.

Return exactly these three fields, each on its own line.
The explanation may continue across multiple lines.

VERDICT: SUPPORTED, REFUTED, or UNVERIFIED
CONFIDENCE: integer from 0 to 100
EXPLANATION: concise explanation with relevant limitations
"""

        response = None
        last_error = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )
                break

            except Exception as error:
                last_error = error
                error_text = str(error)

                if (
                    "429" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                ):
                    raise Exception(
                        "Gemini free-tier quota has been reached. "
                        "Please try again after the quota resets."
                    )

                temporary_error = any(
                    code in error_text
                    for code in ("503", "500", "504")
                )

                if not temporary_error or attempt == 2:
                    raise

                time.sleep(2 ** (attempt + 1))

        if response is None:
            raise last_error or Exception(
                "Gemini returned no response."
            )

        answer = (response.text or "").strip()

        if not answer:
            return {
                "success": False,
                "verdict": None,
                "confidence": None,
                "explanation": (
                    "Gemini returned an empty response. "
                    "No verdict was generated."
                )
            }

        verdict = None
        confidence = None
        explanation_lines = []
        reading_explanation = False

        for line in answer.splitlines():
            stripped = line.strip()
            upper = stripped.upper()

            if upper.startswith("VERDICT:"):
                candidate = stripped.split(":", 1)[1].strip().upper()

                if candidate in {"SUPPORTED", "REFUTED", "UNVERIFIED"}:
                    verdict = candidate

                reading_explanation = False

            elif upper.startswith("CONFIDENCE:"):
                raw_confidence = (
                    stripped.split(":", 1)[1]
                    .strip()
                    .replace("%", "")
                )

                try:
                    confidence = int(raw_confidence)
                except ValueError:
                    confidence = None

                reading_explanation = False

            elif upper.startswith("EXPLANATION:"):
                explanation_lines.append(
                    stripped.split(":", 1)[1].strip()
                )
                reading_explanation = True

            elif reading_explanation and stripped:
                explanation_lines.append(stripped)

        # Validate verdict
        if verdict not in {"SUPPORTED", "REFUTED", "UNVERIFIED"}:
            return {
                "success": False,
                "verdict": None,
                "confidence": None,
                "explanation": (
                    "Gemini returned an invalid or incomplete verdict. "
                    "No verdict was generated."
                )
            }

        # Validate confidence
        if (
            not isinstance(confidence, int)
            or not 0 <= confidence <= 100
        ):
            return {
                "success": False,
                "verdict": None,
                "confidence": None,
                "explanation": (
                    "Gemini returned an invalid confidence value. "
                    "No confidence score was generated."
                )
            }

        explanation = "\n".join(explanation_lines).strip()

        if not explanation:
            explanation = (
                "The AI did not provide a detailed explanation."
            )

        return {
            "success": True,
            "verdict": verdict,
            "confidence": confidence,
            "explanation": explanation
        }

    except Exception as error:
        return {
            "success": False,
            "verdict": None,
            "confidence": None,
            "explanation": (
                f"Gemini AI analysis could not be completed: {error}"
            )
        }


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

def dashboard():

    st.markdown("""
    <div class="hero">
        <div class="eyebrow">INTELLIGENT FACT VERIFICATION PLATFORM</div>
        <h1>🛡️ VeriShield AI</h1>
        <p>
        Verify information. Explore evidence.
        Make informed decisions with AI-assisted analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Claim Verification</div>',
        unsafe_allow_html=True
    )

    claim = st.text_area(
        "Enter a statement to verify",
        placeholder="Example: The Earth revolves around the Sun.",
        height=120,
        key="claim_text"
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        check = st.button(
            "🔍  Verify Claim",
            use_container_width=True
        )

    with col2:
        st.button(
            "Clear",
            use_container_width=True,
            on_click=clear_claim
        )

    if check:
        if not claim.strip():
            st.warning("Please enter a claim first.")
        else:
            try:
                with st.status(
                    "VeriShield AI is working...",
                    expanded=True
                ) as status:

                    st.write("Step 1: Searching the web...")
                    evidence = search_evidence(claim)

                    st.write(
                        f"Step 2: Found {len(evidence)} evidence sources."
                    )

                    st.write("Step 3: Sending evidence to Gemini AI...")
                    analysis = analyze_claim(claim, evidence)

                    st.write("Step 4: Preparing verification results...")

                    result = {
                        "claim": claim,
                        "evidence": evidence,
                        "analysis": analysis,
                        "time": datetime.now().strftime(
                            "%d %b %Y, %I:%M %p"
                        )
                    }

                    st.session_state.result = result

                    if analysis["success"]:
                        st.session_state.history.insert(
                            0,
                            {
                                "claim": claim,
                                "verdict": analysis["verdict"],
                                "time": result["time"]
                            }
                        )

                        st.session_state.history = (
                            st.session_state.history[:20]
                        )

                        status.update(
                            label="Verification completed!",
                            state="complete"
                        )
                    else:
                        status.update(
                            label="Evidence collected; AI analysis not completed",
                            state="error"
                        )

            except Exception as error:
                st.error(f"Verification failed: {error}")

    result = st.session_state.result

    if result:
        analysis = result["analysis"]
        verdict = analysis["verdict"]

        st.markdown("---")
        st.markdown(
            '<div class="section-title">Verification Results</div>',
            unsafe_allow_html=True
        )

        if analysis.get("success"):
            if verdict == "SUPPORTED":
                st.success("VERDICT: SUPPORTED")
            elif verdict == "REFUTED":
                st.error("VERDICT: REFUTED")
            else:
                st.warning("VERDICT: UNVERIFIED")

            col1, col2 = st.columns(2)

            with col1:
                confidence_value = analysis.get("confidence")

                confidence_display = (
                    f"{confidence_value}%"
                    if confidence_value is not None
                    else "Not available"
                )

                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">AI Assessment Confidence</div>
                        <div class="metric-value">{confidence_display}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">Evidence Sources Found</div>
                        <div class="metric-value">{len(result['evidence'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        else:
            st.error("AI ANALYSIS NOT COMPLETED")

            st.caption(
                "No verdict or confidence score was generated. "
                "The sources below are provided for manual review."
            )

            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Evidence Sources Found</div>
                    <div class="metric-value">{len(result['evidence'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            '<div class="section-title">Claim Details</div>',
            unsafe_allow_html=True
        )

        st.info(result["claim"])

        st.markdown(
            '<div class="section-title">AI Explanation</div>',
            unsafe_allow_html=True
        )

        safe_explanation = html.escape(
            analysis["explanation"]
        ).replace("\n", "<br>")

        st.markdown(
            f'<div class="result-card">{safe_explanation}</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="section-title">Evidence & Sources</div>',
            unsafe_allow_html=True
        )

        if result["evidence"]:
            for index, item in enumerate(result["evidence"], 1):
                safe_title = html.escape(item["title"])
                safe_body = html.escape(item["body"])
                safe_url = html.escape(item["url"], quote=True)

                st.markdown(
                    f"""
                    <div class="source-card">
                        <div class="muted">SOURCE {index}</div>
                        <h4>{safe_title}</h4>
                        <p>{safe_body}</p>
                        <a href="{safe_url}" target="_blank" rel="noopener noreferrer">
                            Open original source ↗
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("No evidence sources were found.")

        st.caption(f"Checked on: {result['time']}")

        st.caption(
            "AI-generated assessments may contain errors. "
            "Always review original sources before relying on a verdict."
        )

    else:
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Verification Engine</div>
                <div class="metric-value">Ready</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-label">Evidence Search</div>
                <div class="metric-value">Online</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Previous Checks</div>
                <div class="metric-value">{len(st.session_state.history)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.info(
            "Enter a claim above and select Verify Claim to begin your fact-check."
        )


# --------------------------------------------------
# EVIDENCE LIBRARY
# --------------------------------------------------

def evidence_library():

    st.title("📚 Evidence Library")

    st.write(
        "Review the claims you have previously submitted for verification."
    )

    if not st.session_state.history:
        st.info(
            "Your verification history is empty. "
            "Verify your first claim from the Dashboard."
        )
        return

    for index, item in enumerate(st.session_state.history, 1):
        with st.expander(f"{index}. {item['claim'][:100]}"):
            st.write("**Verdict:**", item["verdict"])
            st.write("**Checked:**", item["time"])
            st.write("**Claim:**", item["claim"])

    if st.button("Clear Search History"):
        st.session_state.history = []
        st.session_state.result = None
        st.rerun()


# --------------------------------------------------
# ABOUT PAGE
# --------------------------------------------------

def about_page():

    st.title("About VeriShield AI")

    st.markdown("""
    ### 🛡️ What is VeriShield AI?

    VeriShield AI is an AI-assisted fact-checking
    application designed to help users examine online
    claims using available web evidence.

    ### Main Features

    - Claim verification
    - Web evidence retrieval
    - AI-assisted evidence analysis
    - Source links and references
    - Verification history
    - Confidence assessment

    ### How it works

    1. User enters a claim.
    2. The application searches for relevant web evidence.
    3. Available evidence is analyzed by the AI model
       when an API key is configured.
    4. A verdict and explanation are displayed.
    5. Users can inspect the original sources.

    ### Important Notice

    VeriShield AI is an assistance tool, not an absolute
    authority on truth. Search results can be incomplete,
    outdated, or unreliable. Always inspect the original
    sources and consider multiple independent references.
    """)


# --------------------------------------------------
# PAGE ROUTING
# --------------------------------------------------

if page == "Dashboard":
    dashboard()
elif page == "Evidence Library":
    evidence_library()
elif page == "About":
    about_page()


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("""
<div class="footer">
    🛡️ VeriShield AI | AI-Assisted Fact Verification
    <br>
    Built with Python, Streamlit and Gemini AI
    <br><br>
    © 2026 VeriShield AI. All rights reserved.
</div>
""", unsafe_allow_html=True)
