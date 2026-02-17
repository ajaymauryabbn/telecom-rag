"""
Telecom RAG - AI-Powered Telecom Operations Platform (Enhanced)
================================================================

A Streamlit-based RAG application for telecom operations support.
Features:
- Hybrid search (BM25 + Dense vectors + RRF fusion)
- RAGAS-style evaluation with faithfulness scoring
- Abstention logic for low-confidence answers
- Glossary-enhanced queries with 81+ telecom terms
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.retriever import TelecomRetriever, RAGResponse
from src.glossary import TelecomGlossary

# Page configuration
st.set_page_config(
    page_title="Telecom RAG Assistant",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .source-card {
        background-color: #f8fafc;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .eval-good { color: #10b981; font-weight: bold; }
    .eval-warn { color: #f59e0b; font-weight: bold; }
    .eval-bad { color: #ef4444; font-weight: bold; }
    .glossary-term {
        background-color: #e0e7ff;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .hybrid-badge {
        background-color: #10b981;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_retriever():
    """Initialize and cache the retriever."""
    return TelecomRetriever(auto_init=True, enable_hybrid=True)


@st.cache_resource
def get_glossary():
    """Initialize and cache the glossary."""
    return TelecomGlossary()


@st.cache_resource
def get_rate_limiter():
    """Initialize and cache the rate limiter."""
    from src.rate_limiter import RateLimiter
    # Limit: 50 requests per minute per user/session
    return RateLimiter(limit=50, window=60)

def display_evaluation(response: RAGResponse):
    """Display evaluation metrics."""
    if not hasattr(response, 'evaluation') or response.evaluation is None:
        return
    
    eval_result = response.evaluation
    
    search_strategy = getattr(response, 'search_type', 'dense')
    st.markdown(f"### 📊 Answer Quality Metrics (Strategy: `{search_strategy}`)")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    def get_color_class(score):
        if score >= 0.8:
            return "eval-good"
        elif score >= 0.6:
            return "eval-warn"
        return "eval-bad"
    
    with col1:
        fc = get_color_class(eval_result.faithfulness_score)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #6b7280;">Faithfulness</div>
            <div class="{fc}" style="font-size: 1.3rem;">{eval_result.faithfulness_score:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rc = get_color_class(eval_result.relevancy_score)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #6b7280;">Relevancy</div>
            <div class="{rc}" style="font-size: 1.3rem;">{eval_result.relevancy_score:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        cc = get_color_class(eval_result.confidence_score)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; background: #f8fafc; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #6b7280;">Confidence</div>
            <div class="{cc}" style="font-size: 1.3rem;">{eval_result.confidence_score:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Context Precision
        cp = get_color_class(eval_result.context_precision)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; background: #f0f9ff; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #6b7280;">Ctx Precision</div>
            <div class="{cp}" style="font-size: 1.3rem;">{eval_result.context_precision:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        # Context Recall
        cr = get_color_class(eval_result.context_recall)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; background: #f0f9ff; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #6b7280;">Ctx Recall</div>
            <div class="{cr}" style="font-size: 1.3rem;">{eval_result.context_recall:.0%}</div>
        </div>
        """, unsafe_allow_html=True)

    with col6:
        # Trust Score (TLM)
        ts = getattr(eval_result, 'trust_score', 0.0)
        tc = get_color_class(ts)
        st.markdown(f"""
        <div style="text-align: center; padding: 0.8rem; background: #f5f3ff; border-radius: 8px;">
            <div style="font-size: 0.7rem; color: #6b7280;">Trust Score</div>
            <div class="{tc}" style="font-size: 1.3rem;">{ts:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    if eval_result.total_claims > 0:
        st.caption(f"📝 Claims verified: {eval_result.supported_claims}/{eval_result.total_claims}")


def display_sources(sources, search_type="dense"):
    """Display source citations."""
    if not sources:
        return
    
    search_badge = ""
    if search_type == "reranked":
        search_badge = '<span class="hybrid-badge" style="background: linear-gradient(90deg, #10b981, #059669);">Reranked (Hybrid + Cross-Encoder)</span>'
    elif search_type == "hybrid":
        search_badge = '<span class="hybrid-badge">Hybrid Search (BM25 + Dense + RRF)</span>'
    
    st.markdown(f"### 📚 Sources {search_badge}", unsafe_allow_html=True)
    
    for idx, source in enumerate(sources[:5], 1):  # Show top 5
        similarity = source.get('similarity', 0)
        rrf_info = ""
        if 'rrf_score' in source:
            rrf_info = f" | RRF: {source['rrf_score']:.4f}"
        
        with st.expander(f"Source {idx}: {source['metadata'].get('source', 'Unknown')} (Score: {similarity:.2f}{rrf_info})"):
            st.markdown(f"**Category:** {source['metadata'].get('category', 'general')}")
            
            if 'dense_score' in source:
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"Dense: {source.get('dense_score', 0):.3f}")
                with col2:
                    st.caption(f"BM25: {source.get('sparse_score', 0):.3f}")
            
            st.markdown(f"**Content:**")
            content = source['content']
            st.text(content[:500] + "..." if len(content) > 500 else content)


def display_glossary_terms(glossary_terms: str):
    """Display identified glossary terms."""
    if not glossary_terms or glossary_terms == "No specific terms identified.":
        return
    
    st.markdown("### 📖 Telecom Terms Identified")
    terms = glossary_terms.strip().split("\n")
    
    cols = st.columns(2)
    for idx, term in enumerate(terms):
        if term.strip():
            with cols[idx % 2]:
                st.markdown(f'<span class="glossary-term">{term.strip()}</span>', unsafe_allow_html=True)


def main():
    # Header
    st.markdown('<p class="main-header">📡 Telecom RAG Assistant</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-powered answers with hybrid search, RAGAS evaluation, and hallucination detection</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Data ingestion status
        try:
            retriever = get_retriever()
            stats = retriever.vector_store.get_stats()
            
            st.markdown("### 📊 Knowledge Base")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documents", stats["total_documents"])
            with col2:
                hybrid_status = "✅" if retriever.enable_hybrid else "❌"
                st.metric("Hybrid", hybrid_status)
            
            if stats["total_documents"] == 0:
                st.warning("⚠️ Knowledge base is empty!")
                if st.button("📥 Ingest Data", type="primary"):
                    with st.spinner("Loading telecom dataset..."):
                        retriever.ingest_data()
                    st.success("✅ Data ingested!")
                    st.cache_resource.clear()
                    st.rerun()
            else:
                if st.button("🔄 Reload Data"):
                    with st.spinner("Reloading data..."):
                        retriever.ingest_data(force_reload=True)
                    st.success("✅ Data reloaded!")
                    st.cache_resource.clear()
                    st.rerun()
                    
        except Exception as e:
            error_msg = str(e)
            st.error(f"Error initializing: {error_msg}")
            if "API_KEY" in error_msg.upper():
                st.warning(
                    "**API Key Issue:** Ensure `OPENAI_API_KEY` is set as a Cloud Run "
                    "environment variable (not just in `.env`). Check with:\n"
                    "```\ngcloud run services describe telecom-rag-service --region=us-central1 --format='value(spec.template.spec.containers[0].env)'\n```"
                )
            else:
                st.info("Please check your configuration and dependencies.")
        
        st.divider()
        
        # Sample queries
        st.markdown("### 💡 Sample Queries")
        sample_queries = [
            "What is the HARQ process in 5G NR?",
            "Explain MIMO technology in telecom",
            "What KPIs measure 5G network quality?",
            "Difference between gNB and eNB?",
            "What is carrier aggregation?",
            "Explain 5G network slicing"
        ]
        
        for query in sample_queries:
            if st.button(f"📝 {query[:35]}...", key=f"sample_{hash(query)}", use_container_width=True):
                st.session_state.query_input = query
        
        st.divider()
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            top_k = st.slider("Number of sources", 5, 20, 12)
            st.session_state.top_k = top_k
            
            use_hybrid = st.checkbox("Enable hybrid search", value=True)
            st.session_state.use_hybrid = use_hybrid
            
            show_eval = st.checkbox("Show evaluation metrics", value=True)
            st.session_state.show_eval = show_eval

            use_llm_eval = st.checkbox("Enable LLM Evaluation (Slower)", value=False, help="Use LLM to evaluate faithfulness and relevancy for higher accuracy")
            st.session_state.use_llm_eval = use_llm_eval
            
            show_enhanced_query = st.checkbox("Show enhanced query", value=True)
            st.session_state.show_enhanced_query = show_enhanced_query
    
    # Main content area
    col_main, col_info = st.columns([2, 1])
    
    with col_main:
        # Query input
        query = st.text_area(
            "Ask a question about telecom operations...",
            value=st.session_state.get("query_input", ""),
            height=100,
            placeholder="e.g., What is the HARQ process in 5G NR?"
        )
        
        col_btn1, col_btn2, _ = st.columns([1, 1, 3])
        with col_btn1:
            search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)
        with col_btn2:
            clear_clicked = st.button("🗑️ Clear", use_container_width=True)
        
        if clear_clicked:
            st.session_state.query_input = ""
            if "last_response" in st.session_state:
                del st.session_state.last_response
            st.rerun()
        
        # Process query
        if search_clicked and query.strip():
            # Rate Limit Check
            if "user_session_id" not in st.session_state:
                import uuid
                st.session_state.user_session_id = str(uuid.uuid4())
            
            rate_limiter = get_rate_limiter()
            if not rate_limiter.is_allowed(st.session_state.user_session_id):
                st.error("⚠️ Rate limit exceeded. Please wait a moment before sending more requests.")
            else:
                try:
                    retriever = get_retriever()
                    
                    with st.spinner("🔍 Searching with hybrid retrieval..."):
                        top_k = st.session_state.get("top_k", 12)
                        use_hybrid = st.session_state.get("use_hybrid", True)
                        use_llm_eval = st.session_state.get("use_llm_eval", False)
                        
                        if use_llm_eval:
                            st.info("ℹ️ LLM Evaluation enabled - this may take a few extra seconds.")
                        
                        response: RAGResponse = retriever.query(
                            query, 
                            top_k=top_k,
                            use_hybrid=use_hybrid,
                            evaluate=True,
                            use_llm_eval=use_llm_eval
                        )
                        st.session_state.last_response = response
                        st.session_state.last_query = query                    
                except Exception as e:
                    st.error(f"Error processing query: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        
        # Display response
        if "last_response" in st.session_state:
            response = st.session_state.last_response
            
            st.markdown("---")
            
            # Show abstention warning if applicable
            if hasattr(response, 'abstained') and response.abstained:
                st.warning("⚠️ Low confidence answer - review carefully")
            
            st.markdown("### 💬 Answer")
            
            # Show search type badge
            if hasattr(response, 'search_type'):
                if response.search_type == "hybrid":
                    st.markdown('<span class="hybrid-badge">🔀 Hybrid Search</span>', unsafe_allow_html=True)
            
            # Show enhanced query if enabled
            if st.session_state.get("show_enhanced_query", True):
                last_query = st.session_state.get("last_query", "")
                if response.enhanced_query != last_query:
                    with st.expander("🔄 Enhanced Query (with glossary expansion)"):
                        st.info(response.enhanced_query)
            
            # Main answer
            st.markdown(response.answer)
            
            # Evaluation metrics
            if st.session_state.get("show_eval", True):
                display_evaluation(response)
            
            # Glossary terms
            if response.glossary_terms:
                display_glossary_terms(response.glossary_terms)
            
            # Sources
            search_type = getattr(response, 'search_type', 'dense')
            display_sources(response.sources, search_type)
            
            # Usage stats
            if response.usage:
                with st.expander("📊 Token Usage"):
                    st.json(response.usage)
    
    with col_info:
        st.markdown("### 🎯 Use Cases")
        
        use_cases = [
            ("🔧", "Network Operations", "Troubleshooting, maintenance, alarms"),
            ("📋", "Compliance", "3GPP standards, regulatory requirements"),
            ("📈", "Performance", "KPIs, capacity planning, optimization"),
            ("🏗️", "Architecture", "Network design, protocols, interfaces"),
        ]
        
        for icon, title, desc in use_cases:
            st.markdown(f"""
            <div style="background-color: #f8fafc; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0;">
                <strong>{icon} {title}</strong><br>
                <small style="color: #6b7280;">{desc}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Feature highlights
        st.markdown("### ✨ Features")
        st.markdown("""
        - **Intelligent Routing**: Query intent classification
        - **Trustworthy AI**: TLM Trust Scoring
        - **Redis Cache**: Persistent semantic caching
        - **Hybrid Search**: BM25 + Dense + RRF
        - **Reliability**: 6-metric evaluation
        """)
        
        st.markdown("---")
        
        # Glossary quick reference
        st.markdown("### 📖 Quick Glossary")
        glossary = get_glossary()
        
        common_terms = ["5G", "NR", "HARQ", "MIMO", "KPI", "gNB"]
        for term in common_terms:
            if term in glossary.glossary:
                with st.expander(f"**{term}**"):
                    st.write(glossary.glossary[term])


if __name__ == "__main__":
    main()
