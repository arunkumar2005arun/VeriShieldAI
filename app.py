import re
import math
import html
import streamlit as st

st.set_page_config(
    page_title="VeriShield AI | Claim Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- EVIDENCE DATABASE --------------------

EVIDENCE = [
    {
        "topic": "Earth and the Sun",
        "evidence": (
            "Earth revolves around the Sun. One complete revolution "
            "takes approximately 365.25 days."
        ),
        "label": "Supported",
        "source": "NASA Solar System Exploration",
        "url": "https://science.nasa.gov/solar-system/earth/",
    },
    {
        "topic": "Antibiotics and viruses",
        "evidence": (
            "Antibiotics treat certain bacterial infections. They do not "
            "work against viruses such as those that cause colds or flu."
        ),
        "label": "Refuted",
        "source": "CDC: Antibiotic Use",
        "url": "https://www.cdc.gov/antibiotic-use/",
    },
    {
        "topic": "Smoking and health",
        "evidence": (
            "Cigarette smoking harms nearly every organ of the body and "
            "causes many diseases, including cancer and heart disease."
        ),
        "label": "Supported",
        "source": "CDC: Smoking and Health",
        "url": "https://www.cdc.gov/tobacco/",
    },
    {
        "topic": "Water boiling",
        "evidence": (
            "Pure water boils at about 100 degrees Celsius at standard "
            "atmospheric pressure. The boiling point changes with pressure."
        ),
        "label": "Supported",
        "source": "US Geological Survey",
        "url": "https://www.usgs.gov/special-topics/water-science-school",
    },
    {
        "topic": "The Moon",
        "evidence": (
            "The Moon does not produce its own visible light. It reflects "
            "sunlight toward Earth."
        ),
        "label": "Supported",
        "source": "NASA: Moon",
        "url": "https://science.nasa.gov/moon/",
    },
    {
        "topic": "Antibiotic resistance",
        "evidence": (
            "Using antibiotics when they are not needed can contribute "
            "to antibiotic resistance. Antibiotics should be used as "
            "directed by a qualified healthcare professional."
        ),
        "label": "Supported",
        "source": "World Health Organization",
        "url": (
            "https://www.who.int/news-room/fact-sheets/"
            "detail/antimicrobial-resistance"
        ),
    },
]

# -------------------- TEXT PROCESSING --------------------

STOP_WORDS = {
    "the", "is", "a", "an", "and", "or", "to", "of",
    "in", "on", "at", "it", "does", "do", "are",
    "be", "for", "that", "this", "with", "as", "can",
    "around", "about", "from", "by", "its", "their",
    "they", "such", "as", "one", "complete",
}

NEGATION_WORDS = {
    "not", "never", "no", "neither", "cannot", "cant",
    "isnt", "arent", "doesnt", "dont", "wont", "without",
}


def tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def content_words(text):
    return {
        word for word in tokenize(text)
        if word not in STOP_WORDS
        and word not in NEGATION_WORDS
    }


def has_negation(text):
    words = set(tokenize(text))
    return bool(words.intersection(NEGATION_WORDS))


def calculate_similarity(claim, evidence):
    claim_words = content_words(claim)
    evidence_words = content_words(evidence)

    if not claim_words or not evidence_words:
        return 0.0

    overlap = len(claim_words.intersection(evidence_words))

    return overlap / math.sqrt(
        len(claim_words) * len(evidence_words)
    )


def find_evidence(claim):
    results = []

    for item in EVIDENCE:
        score = calculate_similarity(
            claim,
            item["evidence"],
        )
        results.append((score, item))

    results.sort(key=lambda result: result[0], reverse=True)

    return results


def safe_text(value):
    return html.escape(str(value))


# -------------------- PROFESSIONAL DESIGN --------------------

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
    );

    .stApp {
        background: #F4F7FB;
        color: #1E293B;
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stSidebar"] {
        background: #102331;
    }

    [data-testid="stSidebar"] * {
        color: #E8F0F5;
    }

    .brand {
        font-size: 32px;
        font-weight: 800;
        color: #102331;
        letter-spacing: -1px;
    }

    .brand span {
        color: #0D9488;
    }

    .subtitle {
        color: #64748B !important;
        font-size: 15px;
        margin-bottom: 24px;
    }

    .hero {
        background: linear-gradient(135deg, #102331, #17485A);
        padding: 30px;
        border-radius: 18px;
        color: #FFFFFF;
        margin-bottom: 24px;
    }

    .hero h2 {
        color: #FFFFFF !important;
        font-size: 28px;
    }

    .hero p {
        color: #E1EDF3 !important;
        line-height: 1.8;
    }

    .section-title {
        color: #102331 !important;
        font-size: 21px;
        font-weight: 750;
        margin: 14px 0;
    }

    .result-card {
        background: #FFFFFF;
        border: 1px solid #DCE5EF;
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0;
        box-shadow: 0 4px 18px rgba(15, 35, 49, 0.05);
    }

    .result-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 1px;
        color: #64748B !important;
        text-transform: uppercase;
    }

    .evidence-text {
        color: #334155 !important;
        font-size: 15px;
        line-height: 1.8;
    }

    [data-testid="stMain"] label {
        color: #1E293B !important;
        font-weight: 600;
    }

    [data-testid="stMarkdownContainer"] p {
        color: #334155;
    }

    [data-testid="stTextArea"] textarea {
        background: #FFFFFF !important;
        color: #1E293B !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-size: 15px !important;
    }

    [data-testid="stTextArea"] textarea::placeholder {
        color: #64748B !important;
        opacity: 1 !important;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 46px;
        font-weight: 600;
    }

    div.stButton > button[kind="primary"] {
        background: #0D9488;
        color: #FFFFFF;
        border: none;
    }

    div.stButton > button[kind="primary"]:hover {
        background: #0F766E;
        color: #FFFFFF;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        padding: 16px;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    @media (max-width: 768px) {
        .hero {
            padding: 22px;
        }

        .hero h2 {
            font-size: 23px;
        }

        .brand {
            font-size: 26px;
        }
    }
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
    st.markdown("- Improved word matching")
    st.markdown("- Basic negation warning")
    st.markdown("- Reference links")
    st.markdown("---")
    st.caption("Educational prototype")

# -------------------- HEADER --------------------

st.markdown(
    """
    <div class="brand">VeriShield <span>AI</span></div>
    <div class="subtitle">
        Evidence-based claim checking made simple.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h2>Check a claim. Explore the evidence.</h2>
        <p>
            Enter a statement to find related information from our
            local evidence collection. Review the references and
            context before deciding what to believe.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------- CLAIM INPUT --------------------

st.markdown(
    '<div class="section-title">🔎 Analyse a claim</div>',
    unsafe_allow_html=True,
)

st.write("Enter a factual statement below to find related evidence.")

claim = st.text_area(
    "Your claim",
    placeholder="Example: Earth revolves around the Sun.",
    height=130,
    max_chars=1000,
    key="claim_input",
)

col1, col2 = st.columns(2)

with col1:
    check = st.button(
        "🔍 Check Claim",
        type="primary",
        use_container_width=True,
    )

with col2:
    clear = st.button(
        "↻ Clear Input",
        use_container_width=True,
    )

if clear:
    st.session_state["claim_input"] = ""
    st.session_state.pop("last_claim", None)
    st.rerun()

# -------------------- CLAIM ANALYSIS --------------------

if check:
    if not claim.strip():
        st.warning("Please enter a claim before checking.")
        st.session_state.pop("last_claim", None)
    else:
        st.session_state["last_claim"] = claim.strip()

if "last_claim" in st.session_state:
    active_claim = st.session_state["last_claim"]
    results = find_evidence(active_claim)
    best_score, best = results[0]

    st.markdown("---")
    st.markdown(
        '<div class="section-title">📊 Analysis Result</div>',
        unsafe_allow_html=True,
    )

    if best_score < 0.12:
        st.info("🟡 Insufficient Evidence")
        st.write(
            "No sufficiently similar passage was found in the local "
            "evidence collection. This does not prove the claim is false."
        )
    else:
        claim_negated = has_negation(active_claim)
        evidence_negated = has_negation(best["evidence"])

        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-label">RELATED TOPIC</div>
                <h3>{safe_text(best["topic"])}</h3>
                <div class="result-label">RETRIEVED EVIDENCE</div>
                <p class="evidence-text">
                    {safe_text(best["evidence"])}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if claim_negated != evidence_negated:
            st.warning(
                "⚠️ Your claim and the retrieved evidence may differ "
                "in negation. Please review the original source carefully. "
                "This basic check cannot reliably determine contradiction."
            )
        elif best["label"] == "Refuted":
            st.error("🔴 Potentially Refuted by Retrieved Evidence")
        else:
            st.success("🟢 Potentially Supported by Retrieved Evidence")

        st.markdown(
            f"**Reference:** [{best['source']}]({best['url']})"
        )

    metric_col1, metric_col2 = st.columns(2)

    with metric_col1:
        st.metric(
            "Text overlap score",
            f"{best_score * 100:.1f}%",
        )

    with metric_col2:
        st.metric(
            "Evidence entries searched",
            len(EVIDENCE),
        )

    st.caption(
        "The score measures word overlap, not the probability that "
        "a claim is true. Negation detection is basic and can be wrong."
    )

   
    with st.expander("📚 View other matching evidence"):
        other_matches = [
            (score, item)
            for score, item in results[1:]
            if score > 0
        ]

        if other_matches:
            for score, item in other_matches:
                st.markdown(f"**{item['topic']}**")
                st.write(item["evidence"])
                st.caption(f"Word overlap score: {score * 100:.1f}%")
                st.markdown(f"[Open reference]({item['url']})")
                st.markdown("---")
        else:
            st.info("No other evidence with matching words was found.")

        

# -------------------- EVIDENCE LIBRARY --------------------

st.markdown("---")

with st.expander("📚 Explore the local evidence library"):
    st.write("Evidence currently available in this prototype:")

    for item in EVIDENCE:
        st.markdown(f"**{item['topic']}**")
        st.write(item["evidence"])
        st.markdown(f"[Source: {item['source']}]({item['url']})")
        st.markdown("---")

# -------------------- ABOUT --------------------

with st.expander("ℹ️ About VeriShield AI"):
    st.write(
        "VeriShield AI compares words in a claim with a small local "
        "evidence collection and retrieves related passages."
    )
    st.write(
        "It does not search the entire internet or use a trained AI model. "
        "Its matching and negation checks are limited."
    )
    st.write(
        "The similarity score is not a truth probability. Always inspect "
        "the original source and context."
    )

# -------------------- FOOTER --------------------

st.markdown("---")
st.markdown(
    """
    <p style="text-align:center;color:#64748B;font-size:12px;">
        🛡️ VeriShield AI · Educational Prototype
        <br>
        Always check the original source and context.
    </p>
    """,
    unsafe_allow_html=True,
)
