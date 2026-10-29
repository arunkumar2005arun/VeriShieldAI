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
    st.markdown("- Local evidence retrieval\n- Live web search\n- OpenAI claim analysis\n- Source links and limitations")
    st.markdown("---")
    st.caption("Educational prototype")

st.markdown('<div class="brand">VeriShield <span>AI</span></div><div class="subtitle">Evidence-based claim checking made simple.</div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><h2>Check a claim. Explore the evidence.</h2><p>Enter a statement to compare it with our local evidence collection and search for relevant web sources. Review the references and context before deciding what to believe.</p></div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">🔎 Analyse a claim</div>', unsafe_allow_html=True)
st.write("Enter a factual statement below to find related evidence and live web sources.")

claim = st.text_area("Your claim", placeholder="Example: Earth revolves around the Sun.", height=130, max_chars=1000, key="claim_input")
col1, col2 = st.columns(2)
with col1:
    check = st.button("🔍 Check Claim", type="primary", use_container_width=True)
with col2:
    st.button("↻ Clear Input", use_container_width=True, on_click=clear_claim)

if check:
    if not claim.strip():
        st.warning("Please enter a claim before checking.")
        st.session_state.pop("last_claim", None)
        st.session_state.pop("analysis_result", None)
    else:
        st.session_state["last_claim"] = claim.strip()
        st.session_state.pop("analysis_result", None)

if "last_claim" in st.session_state:
    active_claim = st.session_state["last_claim"]
    results = find_evidence(active_claim)
    best_score, best = results[0]

    st.markdown("---")
    st.markdown('<div class="section-title">📊 Analysis Result</div>', unsafe_allow_html=True)
    if best_score < 0.12:
        st.info("🟡 Insufficient local evidence")
        st.write("No sufficiently similar passage was found in the local evidence collection. This does not prove the claim is false.")
    else:
        st.markdown(f'<div class="result-card"><div class="result-label">RELATED TOPIC</div><h3>{safe_text(best["topic"])}</h3><div class="result-label">RETRIEVED LOCAL EVIDENCE</div><p class="evidence-text">{safe_text(best["evidence"])}</p></div>', unsafe_allow_html=True)
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
        sources, web_error, ai_error, ai_result = [], None, None, ""
        with st.spinner("Searching the web and asking the AI to assess the claim..."):
            try:
                sources = search_web(active_claim, max_results=5)
            except Exception as exc:
                web_error = f"{type(exc).__name__}: {exc}"
            try:
                ai_result = analyze_with_ai(active_claim, sources)
            except Exception as exc:
                ai_error = f"{type(exc).__name__}: {exc}"
        st.session_state["analysis_result"] = {
            "sources": sources, "ai": ai_result,
            "web_error": web_error, "ai_error": ai_error,
        }

    analysis = st.session_state["analysis_result"]
    if analysis.get("web_error"):
        st.warning("Live web search failed. The AI analysis may have limited evidence.")
        with st.expander("Web search technical details"):
            st.code(analysis["web_error"])
    if analysis.get("ai_error"):
        st.warning("Live AI analysis could not complete. Your local evidence results above are still available.")
        st.caption("Check OPENAI_API_KEY in Streamlit Secrets, API account billing/access, selected model, and installed packages.")
        with st.expander("AI technical error details"):
            st.code(analysis["ai_error"])
    elif analysis.get("ai"):
        st.markdown(analysis["ai"])

    if analysis.get("sources"):
        st.markdown("#### Web sources returned")
        for i, source in enumerate(analysis["sources"], start=1):
            st.markdown(f'**{i}. [{source["title"]}]({source["url"]})**')
            st.write(source["snippet"] or "No snippet was provided.")
    else:
        st.info("The web search returned no usable sources. Treat any AI assessment as limited.")
    st.caption("AI assessment is based on search snippets, which can be incomplete. Open the original sources and verify context independently.")

st.markdown("---")
with st.expander("📚 Explore the local evidence library"):
    st.write("Evidence currently available in this prototype:")
    for item in EVIDENCE:
        st.markdown(f'**{item["topic"]}**')
        st.write(item["evidence"])
        st.markdown(f'[Source: {item["source"]}]({item["url"]})')
        st.markdown("---")

with st.expander("ℹ️ About VeriShield AI"):
    st.write("VeriShield AI compares a claim with a small local evidence collection, retrieves live web search snippets, and uses an OpenAI model to summarize how those snippets relate to the claim.")
    st.write("Search snippets may be incomplete or misleading. The AI can make mistakes and does not independently guarantee that a claim is true or false.")
    st.write("Always inspect original sources and context. This is an educational prototype, not a substitute for professional advice.")
