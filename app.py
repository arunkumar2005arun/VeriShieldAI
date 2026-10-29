import re
import math
import html
import streamlit as st
from openai import OpenAI
from ddgs import DDGS

st.set_page_config(
    page_title="VeriShield AI | Claim Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- LOCAL EVIDENCE DATABASE --------------------
EVIDENCE = [
    {
        "topic": "Earth and the Sun",
        "evidence": "Earth revolves around the Sun. One complete revolution takes approximately 365.25 days.",
        "label": "Supported",
        "source": "NASA Solar System Exploration",
        "url": "https://science.nasa.gov/solar-system/earth/",
    },
    {
        "topic": "Antibiotics and viruses",
        "evidence": "Antibiotics treat certain bacterial infections. They do not work against viruses such as those that cause colds or flu.",
        "label": "Refuted",
        "source": "CDC: Antibiotic Use",
        "url": "https://www.cdc.gov/antibiotic-use/",
    },
    {
        "topic": "Smoking and health",
        "evidence": "Cigarette smoking harms nearly every organ of the body and causes many diseases, including cancer and heart disease.",
        "label": "Supported",
        "source": "CDC: Smoking and Health",
        "url": "https://www.cdc.gov/tobacco/",
    },
    {
        "topic": "Water boiling",
        "evidence": "Pure water boils at about 100 degrees Celsius at standard atmospheric pressure. The boiling point changes with pressure.",
        "label": "Supported",
        "source": "US Geological Survey",
        "url": "https://www.usgs.gov/special-topics/water-science-school",
    },
    {
        "topic": "The Moon",
        "evidence": "The Moon does not produce its own visible light. It reflects sunlight toward Earth.",
        "label": "Supported",
        "source": "NASA: Moon",
        "url": "https://science.nasa.gov/moon/",
    },
    {
        "topic": "Antibiotic resistance",
        "evidence": "Using antibiotics when they are not needed can contribute to antibiotic resistance. Antibiotics should be used as directed by a qualified healthcare professional.",
        "label": "Supported",
        "source": "World Health Organization",
        "url": "https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance",
    },
]

STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "to", "of", "in", "on", "at",
    "it", "does", "do", "are", "be", "for", "that", "this", "with", "as",
    "can", "around", "about", "from", "by", "its", "their", "they", "such",
    "one", "complete",
}
NEGATION_WORDS = {
    "not", "never", "no", "neither", "cannot", "cant", "isnt", "arent",
    "doesnt", "dont", "wont", "without",
}


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def content_words(text):
    return {w for w in tokenize(text) if w not in STOP_WORDS and w not in NEGATION_WORDS}


def has_negation(text):
    return bool(set(tokenize(text)).intersection(NEGATION_WORDS))


def calculate_similarity(claim, evidence):
    claim_words = content_words(claim)
    evidence_words = content_words(evidence)
    if not claim_words or not evidence_words:
        return 0.0
    overlap = len(claim_words.intersection(evidence_words))
    return overlap / math.sqrt(len(claim_words) * len(evidence_words))


def find_evidence(claim):
    results = [(calculate_similarity(claim, item["evidence"]), item) for item in EVIDENCE]
    results.sort(key=lambda result: result[0], reverse=True)
    return results


def safe_text(value):
    return html.escape(str(value))


def search_web(claim, max_results=5):
    """Fetch live web search snippets. Results may be unavailable in some hosting environments."""
    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(claim, max_results=max_results):
            url = item.get("href") or item.get("url")
            if url:
                results.append({
                    "title": item.get("title", "Untitled source"),
                    "url": url,
                    "snippet": item.get("body", "No snippet available"),
                })
    return results


def analyze_with_ai(claim, sources):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing from Streamlit Secrets.")

    client = OpenAI(api_key=api_key)
    source_text = "\n\n".join(
        f"[{i}] Title: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}"
        for i, s in enumerate(sources, start=1)
    )
    prompt = f"""You are VeriShield AI, a careful claim-checking assistant.
Assess the user's claim using ONLY the provided search-result snippets and the claim itself.
Do not invent facts, citations, sources, or URLs. Search snippets may be incomplete or misleading.
Choose one verdict: Supported, Refuted, Mixed, or Insufficient evidence.
Explain the reasoning briefly, note uncertainty, and distinguish evidence from inference.
Do not treat the number of search results as proof. This is an informational tool, not a substitute for expert advice.

CLAIM:
{claim}

LIVE SEARCH RESULTS:
{source_text if source_text else 'No search results were returned.'}

Return a concise answer with headings: Verdict, Explanation, Limitations."""
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=700,
    )
    return response.output_text

# -------------------- PROFESSIONAL DESIGN --------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp { background: #F4F7FB; color: #1E293B; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background: #102331; }
    [data-testid="stSidebar"] * { color: #E8F0F5; }
    .brand { font-size: 32px; font-weight: 800; color: #102331; letter-spacing: -1px; }
    .brand span { color: #0D9488; }
    .subtitle { color: #64748B !important; font-size: 15px; margin-bottom: 24px; }
    .hero { background: linear-gradient(135deg, #102331, #17485A); padding: 30px; border-radius: 18px; color: #FFFFFF; margin-bottom: 24px; }
    .hero h2 { color: #FFFFFF !important; font-size: 28px; }
    .hero p { color: #E1EDF3 !important; line-height: 1.8; }
    .section-title { color: #102331 !important; font-size: 21px; font-weight: 750; margin: 14px 0; }
    .result-card { background: #FFFFFF; border: 1px solid #DCE5EF; border-radius: 16px; padding: 24px; margin: 12px 0; box-shadow: 0 4px 18px rgba(15, 35, 49, 0.05); }
    .result-label { font-size: 12px; font-weight: 700; letter-spacing: 1px; color: #64748B !important; text-transform: uppercase; }
    .evidence-text { color: #334155 !important; font-size: 15px; line-height: 1.8; }
    [data-testid="stMain"] label { color: #1E293B !important; font-weight: 600; }
    [data-testid="stMarkdownContainer"] p { color: #334155; }
    [data-testid="stTextArea"] textarea { background: #FFFFFF !important; color: #1E293B !important; border: 1px solid #CBD5E1 !important; border-radius: 10px !important; font-size: 15px !important; }
    [data-testid="stTextArea"] textarea::placeholder { color: #64748B !important; opacity: 1 !important; }
    div.stButton > button { border-radius: 10px; min-height: 46px; font-weight: 600; }
    div.stButton > button[kind="primary"] { background: #0D9488; color: #FFFFFF; border: none; }
    div.stButton > button[kind="primary"]:hover { background: #0F766E; color: #FFFFFF; }
    div[data-testid="stMetric"] { background: #FFFFFF; padding: 16px; border: 1px solid #E2E8F0; border-radius: 12px; }
    #MainMenu, footer { visibility: hidden; }
    @media (max-width: 768px) { .hero { padding: 22px; } .hero h2 { font-size: 23px; } .brand { font-size: 26px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("## 🛡️ VeriShield AI")
    st.caption("EVIDENCE-BASED CLAIM CHECKER")
    st.markdown("---")
    st.markdown("### Navigation")
    st.markdown("🔎 Claim Checker")
    st.markdown("📚 Evidence Library")
    st.markdown("ℹ️ About the Project")
    st.markdown("---")
    st.markdown("### Current capabilities")
    st.markdown("- Local evidence retrieval")
    st.markdown("- Live web search")
    st.markdown("- OpenAI claim analysis")
    st.markdown("- Source links and limitations")
    st.markdown("---")
    st.caption("Educational prototype")

# -------------------- HEADER --------------------
st.markdown('<div class="brand">VeriShield <span>AI</span></div><div class="subtitle">Evidence-based claim checking made simple.</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero"><h2>Check a claim. Explore the evidence.</h2><p>Enter a statement to compare it with our local evidence collection and search for relevant web sources. Review the references and context before deciding what to believe.</p></div>',
    unsafe_allow_html=True,
)

# -------------------- CLAIM INPUT --------------------
st.markdown('<div class="section-title">🔎 Analyse a claim</div>', unsafe_allow_html=True)
st.write("Enter a factual statement below to find related evidence and live web sources.")
claim = st.text_area(
    "Your claim",
    placeholder="Example: Earth revolves around the Sun.",
    height=130,
    max_chars=1000,
    key="claim_input",
)
col1, col2 = st.columns(2)
with col1:
    check = st.button("🔍 Check Claim", type="primary", use_container_width=True)
with col2:
    clear = st.button("↻ Clear Input", use_container_width=True)

if clear:
    st.session_state["claim_input"] = ""
    st.session_state.pop("last_claim", None)
    st.session_state.pop("analysis_result", None)
    st.rerun()

if check:
    if not claim.strip():
        st.warning("Please enter a claim before checking.")
        st.session_state.pop("last_claim", None)
    else:
        st.session_state["last_claim"] = claim.strip()
        st.session_state.pop("analysis_result", None)

if "last_claim" in st.session_state:
    active_claim = st.session_state["last_claim"]
    results = find_evidence(active_claim)
    best_score, best = results[0]

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Analysis Result</div>', unsafe_allow_html=True)

    # Keep the local evidence retrieval visible even if live services fail.
    if best_score < 0.12:
        st.info("🟡 Insufficient local evidence")
        st.write("No sufficiently similar passage was found in the local evidence collection. This does not prove the claim is false.")
    else:
        st.markdown(
            f'<div class="result-card"><div class="result-label">RELATED TOPIC</div><h3>{safe_text(best["topic"])}</h3><div class="result-label">RETRIEVED LOCAL EVIDENCE</div><p class="evidence-text">{safe_text(best["evidence"])}</p></div>',
            unsafe_allow_html=True,
        )
        if has_negation(active_claim) != has_negation(best["evidence"]):
            st.warning("The claim and local evidence may differ in negation. This basic check cannot reliably determine contradiction.")
        elif best["label"] == "Refuted":
            st.error("Potentially refuted by local evidence")
        else:
            st.success("Potentially supported by local evidence")
        st.markdown(f'**Local reference:** [{best["source"]}]({best["url"]})')

    metric_col1, metric_col2 = st.columns(2)
    with metric_col1:
        st.metric("Text overlap score", f"{best_score * 100:.1f}%")
    with metric_col2:
        st.metric("Local evidence entries searched", len(EVIDENCE))
    st.caption("The overlap score measures shared words, not the probability that a claim is true.")

    with st.expander("📚 View other matching local evidence"):
        other_matches = [(score, item) for score, item in results[1:] if score > 0]
        if other_matches:
            for score, item in other_matches:
                st.markdown(f'**{item["topic"]}**')
                st.write(item["evidence"])
                st.caption(f"Word overlap score: {score * 100:.1f}%")
                st.markdown(f'[Open reference]({item["url"]})')
                st.markdown("---")
        else:
            st.info("No other local evidence with matching words was found.")

    st.markdown("---")
    st.markdown('<div class="section-title">🌐 Live Web Search + AI Analysis</div>', unsafe_allow_html=True)
    if "analysis_result" not in st.session_state:
        with st.spinner("Searching the web and asking the AI to assess the available snippets..."):
            try:
                web_sources = search_web(active_claim, max_results=5)
                ai_result = analyze_with_ai(active_claim, web_sources)
                st.session_state["analysis_result"] = {"sources": web_sources, "ai": ai_result, "error": None}
            except Exception as exc:
                # Do not expose credentials or detailed server errors to end users.
                st.session_state["analysis_result"] = {"sources": [], "ai": "", "error": str(exc)}

    analysis = st.session_state["analysis_result"]
    if analysis["error"]:
        st.warning("Live AI analysis could not complete. Your local evidence results above are still available.")
        st.caption("Check that OPENAI_API_KEY is set in Streamlit Secrets, the API account can use the selected model, and the required packages are installed. Live web search can also fail if the host blocks it.")
        with st.expander("Technical error details"):
            st.code(analysis["error"])
    else:
        st.markdown(analysis["ai"])
        if analysis["sources"]:
            st.markdown("#### Web sources returned")
            for i, source in enumerate(analysis["sources"], start=1):
                st.markdown(f'**{i}. [{source["title"]}]({source["url"]})**')
                st.write(source["snippet"] or "No snippet was provided.")
        else:
            st.info("The web search returned no usable sources. Treat the AI assessment as limited.")
        st.caption("AI assessment is based on search snippets, which can be incomplete. Open the original sources and verify context independently.")

# -------------------- EVIDENCE LIBRARY --------------------
st.markdown("---")
with st.expander("📚 Explore the local evidence library"):
    st.write("Evidence currently available in this prototype:")
    for item in EVIDENCE:
        st.markdown(f'**{item["topic"]}**')
        st.write(item["evidence"])
        st.markdown(f'[Source: {item["source"]}]({item["url"]})')
        st.markdown("---")

# -------------------- ABOUT --------------------
with st.expander("ℹ️ About VeriShield AI"):
    st.write("VeriShield AI compares a claim with a small local evidence collection, retrieves live web search snippets, and uses an OpenAI model to summarize how those snippets relate to the claim.")
    st.write("Search snippets may be incomplete or misleading. The AI can make mistakes and does not independently guarantee that a claim is true or false.")
    st.write("Always inspect original sources and context. This is an educational prototype, not a substitute for professional advice.")

# -------------------- FOOTER --------------------
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#64748B;font-size:12px;">🛡️ VeriShield AI · Educational Prototype<br>Always check the original source and context.</p>',
    unsafe_allow_html=True,
)
