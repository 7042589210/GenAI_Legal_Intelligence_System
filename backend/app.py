import os
import sys
import streamlit as st

# --- Page Configuration MUST be the first Streamlit command ---
st.set_page_config(
    page_title="Tata Group AI Legal Intelligence & Operations",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Ensure backend directory and project root are in python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
parent_dir = os.path.dirname(backend_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from backend.database.connection import SessionLocal
from backend.ingestion import extract_text_from_file
from backend.preprocessing import normalize_legal_text
from backend.clause_analysis import parse_clauses_and_metadata
from backend.vectorstore import build_and_save_vector_store
from backend.generation import answer_query
from backend.legal_analysis import analyze_contract_risks, analyze_structured_risks, analyze_document_summary
from backend.legal_operations import (
    create_case_for_document,
    start_review,
    submit_review_decision,
    add_comment,
    assign_case,
    update_case_status,
    update_case_priority,
    complete_case,
    close_case,
    get_dashboard_metrics,
    get_all_cases
)

# Initialize DB tables using a cached resource to prevent blocking re-runs
@st.cache_resource(show_spinner=False)
def initialize_app_database():
    from backend.database.connection import init_db
    init_db()
    return True

initialize_app_database()

# --- Custom Styling & Design Tokens ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%);
        color: #F8FAFC;
    }
    
    /* Header Card */
    .header-container {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 0.3rem;
        margin-bottom: 0;
    }
    
    /* Content Cards */
    .custom-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        color: #F8FAFC;
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #38BDF8;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Risk Badges */
    .risk-card-high {
        background: rgba(239, 68, 68, 0.12);
        border-left: 5px solid #EF4444;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        color: #FCA5A5;
    }
    .risk-card-medium {
        background: rgba(245, 158, 11, 0.12);
        border-left: 5px solid #F59E0B;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        color: #FDE68A;
    }
    .risk-card-low {
        background: rgba(16, 185, 129, 0.12);
        border-left: 5px solid #10B981;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        color: #A7F3D0;
    }

    .approval-banner {
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid #38BDF8;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Footer */
    .footer-text {
        text-align: center;
        color: #64748B;
        font-size: 0.85rem;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid #334155;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State Initialization ---
if "processed" not in st.session_state:
    st.session_state.processed = False
if "filename" not in st.session_state:
    st.session_state.filename = None
if "raw_text" not in st.session_state:
    st.session_state.raw_text = None
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "risk_analysis" not in st.session_state:
    st.session_state.risk_analysis = None
if "structured_risks" not in st.session_state:
    st.session_state.structured_risks = None
if "document_summary" not in st.session_state:
    st.session_state.document_summary = None
if "active_case_id" not in st.session_state:
    st.session_state.active_case_id = None
if "active_query" not in st.session_state:
    st.session_state.active_query = ""
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

# --- Main Page Header ---
st.markdown("""
<div class="header-container">
    <div>
        <h1 class="header-title">⚖️ Tata Group AI Legal Document Intelligence & Operations</h1>
        <p class="header-subtitle">Enterprise RAG Analysis · Human-in-the-Loop Approval · Legal Operations & Audit Trail</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Document Upload & Quick Stats Section ---
col_upload, col_stats = st.columns([3, 2])

with col_upload:
    st.markdown("""
    <div class="card-title">📁 Upload & Ingest Legal Document</div>
    """, unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload Contract or Policy Document (PDF, DOCX, TXT, Images)",
        type=["pdf", "docx", "txt", "jpg", "jpeg", "png"],
        help="Upload legal document for OCR text normalization and vector indexing."
    )
    
    if uploaded_file and (st.session_state.filename != uploaded_file.name):
        with st.spinner("Processing..."):
            temp_path = f"temp_{uploaded_file.name}"
            try:
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 1. OCR / Native Text Extraction
                raw_text = extract_text_from_file(temp_path)
                
                # 2. Clause Extraction & Text Normalization
                pages_data = [{"text": raw_text, "page": 1}]
                chunks = parse_clauses_and_metadata(pages_data, uploaded_file.name)
                
                # 3. Vector DB Ingestion
                build_and_save_vector_store(chunks)
                
                # 4. Create Legal Case in DB for Human Approval Workflow
                db = SessionLocal()
                try:
                    case_obj = create_case_for_document(
                        db=db,
                        filename=uploaded_file.name,
                        title=f"Legal Review: {uploaded_file.name}",
                        ai_risk_level="MEDIUM",
                        ai_summary=f"Extracted {len(chunks)} clause chunks.",
                        ai_analysis_snapshot=f"Document '{uploaded_file.name}' ingested with {len(chunks)} clauses indexed."
                    )
                    st.session_state.active_case_id = case_obj.id
                finally:
                    db.close()

                # Update Session State
                st.session_state.filename = uploaded_file.name
                st.session_state.raw_text = raw_text
                st.session_state.chunks = chunks
                st.session_state.processed = True
                st.session_state.chat_history = []
                st.session_state.risk_analysis = None
                st.session_state.structured_risks = None
                st.session_state.document_summary = None
                st.session_state.active_query = ""
                st.session_state.last_answer = None
                
                st.success(f"Successfully ingested `{uploaded_file.name}` and created Legal Case #{st.session_state.active_case_id}!")
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

with col_stats:
    pass

st.divider()

if not st.session_state.processed:
    st.info(" Please upload a legal contract above to unlock RAG Legal Assistant, Risk Analysis & Human Operations.")
    st.stop()


# --- Main Results & Analysis Tabs ---
tab1, tab_summary, tab2, tab3, tab4, tab5 = st.tabs([
    "🛡️ Executive Risk Assessment",
    "📋 Document Summary",
    "💬 Interactive Q&A Assistant",
    "⚖️ Human Approval & Legal Ops",
    "📑 Extracted Clauses & Chunks",
    "🔍 Document Inspector"
])

# ==========================================
# TAB 1: EXECUTIVE RISK ASSESSMENT
# ==========================================
with tab1:
    st.subheader("🛡️ Executive Legal Risk Assessment")
    st.markdown("Automated RAG evaluation of high-risk liabilities, indemnities, unilateral termination, and payment traps.")
    
    r_btn1, r_btn2 = st.columns([1, 4])
    with r_btn1:
        run_risk_audit = st.button("🚀 Run Comprehensive Risk Audit", type="primary", use_container_width=True)
        run_struct_matrix = st.button("📋 Extract Structured Risk Matrix", use_container_width=True)
    with r_btn2:
        st.caption("Triggers Gemini RAG risk reasoning across liability caps, indemnity, termination penalties, and governing law.")

    if run_risk_audit or (st.session_state.risk_analysis is not None):
        if run_risk_audit or st.session_state.risk_analysis is None:
            with st.spinner("Conducting comprehensive legal risk audit..."):
                answer, sources = analyze_contract_risks()
                st.session_state.risk_analysis = (answer, sources)
        
        answer, sources = st.session_state.risk_analysis
        
        st.markdown("### 📊 Comprehensive Risk Audit Report")
        st.markdown(f'<div class="custom-card">{answer}</div>', unsafe_allow_html=True)
        
        with st.expander("🔍 Retained Legal Context Excerpts"):
            for idx, doc in enumerate(sources):
                st.markdown(f"**Source Excerpt {idx+1} (Page {doc.metadata.get('page', '1')})**:")
                st.caption(doc.page_content)
                st.divider()

    if run_struct_matrix or (st.session_state.structured_risks is not None):
        if run_struct_matrix or st.session_state.structured_risks is None:
            with st.spinner("Extracting structured Pydantic risk flags with verifiable citations..."):
                try:
                    res = analyze_structured_risks(st.session_state.chunks)
                    st.session_state.structured_risks = res
                except Exception as ex:
                    st.warning(f"Structured analysis notice: {str(ex)}")

        res = st.session_state.structured_risks
        if res:
            st.markdown("---")
            st.subheader("📌 Structured Risk Breakdown")
            st.markdown(f"**Document Summary:** {getattr(res, 'document_summary', 'N/A')}")
            
            if hasattr(res, 'risk_flags') and res.risk_flags:
                for rf in res.risk_flags:
                    sev = str(getattr(rf, 'severity', 'MEDIUM')).upper()
                    css_class = "risk-card-high" if "HIGH" in sev else ("risk-card-medium" if "MED" in sev else "risk-card-low")
                    st.markdown(f"""
                    <div class="{css_class}">
                        <h4>CLAUSE {getattr(rf, 'clause_number', '')} — {getattr(rf, 'clause', 'Unknown')}</h4>
                        <strong>Risk Level:</strong> {sev}<br/>
                        <strong>Risk Category:</strong> {getattr(rf, 'clause_type', 'General')}<br/><br/>
                        <b>WHY THIS WAS FLAGGED:</b><br/>{getattr(rf, 'rationale', '')}<br/><br/>
                        <b>POTENTIAL IMPACT:</b><br/>{getattr(rf, 'potential_impact', 'N/A')}<br/><br/>
                        <b>AI RECOMMENDATION:</b><br/>{getattr(rf, 'recommendation', '')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("📄 View Evidence & Citations"):
                        evidence_text = getattr(rf, 'evidence', '')
                        if evidence_text:
                            st.markdown(f"**Original Text Evidence:**\n> {evidence_text}")
                        else:
                            st.warning("No direct evidence snippet extracted.")
                            
                        citations = getattr(rf, 'citations', [])
                        if citations:
                            st.markdown("**SOURCES:**")
                            for c in citations:
                                st.caption(f"- **Document:** {c.document_name} | **Page:** {c.page} | **Clause:** {c.clause}")
                                st.caption(f"  *Matched Text:* {c.evidence_text}")
                        else:
                            st.info("Insufficient source information available to generate formal citations.")

# ==========================================
# TAB SUMMARY: DOCUMENT SUMMARY
# ==========================================
with tab_summary:
    st.subheader("📋 Document Summary")
    
    if st.button("🚀 Generate Document Summary", type="primary", use_container_width=True) or (st.session_state.document_summary is not None):
        if st.session_state.document_summary is None or st.button("🔄 Regenerate Summary"):
            with st.spinner("Analyzing document and generating summary..."):
                try:
                    summary = analyze_document_summary(st.session_state.chunks)
                    st.session_state.document_summary = summary
                except Exception as ex:
                    st.error(f"Error generating summary: {str(ex)}")

        doc_summary = st.session_state.document_summary
        if doc_summary:
            st.markdown("---")
            
            # Document Overview Metrics
            sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
            sum_col1.metric("Document Type", doc_summary.document_type)
            sum_col2.metric("Total Parties", len(doc_summary.parties))
            
            if st.session_state.structured_risks and hasattr(st.session_state.structured_risks, 'risk_flags'):
                high = sum(1 for r in st.session_state.structured_risks.risk_flags if "HIGH" in str(r.severity).upper())
                sum_col3.metric("🔴 High Risks", high)
            else:
                sum_col3.metric("🔴 High Risks", "?")
                
            sum_col4.metric("Extracted Clauses", len(doc_summary.key_clauses))
            
            st.markdown("---")
            
            # Executive Summary
            st.markdown("### 📝 Executive Summary")
            st.info(doc_summary.executive_summary)
            
            st.markdown("---")
            
            # Parties & Dates
            col_p, col_d = st.columns(2)
            with col_p:
                st.markdown("### 👥 Parties")
                if doc_summary.parties:
                    for p in doc_summary.parties:
                        st.markdown(f"- **{p.name}** ({p.role})")
                else:
                    st.caption("No parties clearly identified.")
            
            with col_d:
                st.markdown("### 📅 Important Dates")
                if doc_summary.important_dates:
                    for d in doc_summary.important_dates:
                        st.markdown(f"- **{d.name}:** {d.date}")
                        with st.expander("View Evidence"):
                            if d.citations:
                                for c in d.citations:
                                    st.caption(f"Source: {c.document_name} | Page: {c.page} | Clause: {c.clause}")
                                    st.caption(f"> {c.evidence_text}")
                            else:
                                st.caption(d.evidence_text or "Evidence unavailable.")
                else:
                    st.caption("No important dates extracted.")
                    
            st.markdown("---")
            
            # Takeaways
            st.markdown("### 💡 Key Takeaways")
            if doc_summary.key_takeaways:
                for t in doc_summary.key_takeaways:
                    st.markdown(f"- {t}")
            else:
                st.caption("No takeaways available.")
            
            st.markdown("---")
            
            # Key Clauses
            st.markdown("### 📑 Key Clauses")
            if doc_summary.key_clauses:
                for c in doc_summary.key_clauses:
                    with st.container():
                        st.markdown(f"#### Clause {c.clause_number} - {c.clause_title}")
                        st.markdown(c.summary)
                        with st.expander("View Evidence"):
                            if c.citations:
                                for cit in c.citations:
                                    st.caption(f"Source: {cit.document_name} | Page: {cit.page} | Clause: {cit.clause}")
                                    st.caption(f"> {cit.evidence_text}")
                            else:
                                st.caption(c.evidence_text or "Evidence unavailable.")
            else:
                st.caption("No key clauses extracted.")

            st.markdown("---")
            
            # Obligations
            st.markdown("### 📋 Key Obligations")
            if doc_summary.obligations:
                for o in doc_summary.obligations:
                    with st.container():
                        st.markdown(f"**Party:** {o.party}")
                        st.markdown(f"**Obligation:** {o.obligation}")
                        st.markdown(f"**Deadline:** {o.deadline}")
                        with st.expander("View Evidence"):
                            if o.citations:
                                for cit in o.citations:
                                    st.caption(f"Source: {cit.document_name} | Page: {cit.page} | Clause: {cit.clause}")
                                    st.caption(f"> {cit.evidence_text}")
                            else:
                                st.caption(o.evidence_text or "Evidence unavailable.")
                        st.markdown("---")
            else:
                st.caption("No obligations extracted.")

            st.markdown("### ⚠️ Risk Overview")
            st.markdown("For detailed risk analysis, please view the **Executive Risk Assessment** tab.")
# ==========================================
# TAB 2: INTERACTIVE Q&A ASSISTANT
# ==========================================
with tab2:
    st.subheader("💬 Interactive Legal Q&A Assistant")
    st.markdown("Query specific contract terms with expandable source citations.")

    selected_query = None
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    with q_col1:
        if st.button("🔴 High-Risk Terms", use_container_width=True):
            selected_query = "What are the high-risk clauses, uncapped liabilities, or harsh terms in this contract?"
    with q_col2:
        if st.button("📋 Termination Terms", use_container_width=True):
            selected_query = "What is the termination notice period and conditions for termination?"
    with q_col3:
        if st.button("⚖️ Indemnification", use_container_width=True):
            selected_query = "Summarize the indemnification obligations and liability caps."
    with q_col4:
        if st.button("🔒 Confidentiality", use_container_width=True):
            selected_query = "What confidentiality and data protection obligations are specified?"

    query_val = selected_query if selected_query else st.session_state.active_query
    user_query = st.text_area(
        label="Ask custom question or select quick prompt above:",
        value=query_val,
        height=85,
        placeholder="Ask a question about the contract..."
    )

    if st.button("⚡ Run RAG Analysis", type="primary", use_container_width=True) and user_query:
        with st.spinner("Analyzing document context with RAG engine..."):
            answer, sources = answer_query(user_query)
            st.session_state.last_answer = (user_query, answer, sources)
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": sources})

    if st.session_state.last_answer:
        q_text, a_text, a_sources = st.session_state.last_answer
        st.markdown(f"### 🎯 Latest Query: *\"{q_text}\"*")
        st.markdown(f'<div class="custom-card">{a_text}</div>', unsafe_allow_html=True)

# ==========================================
# TAB 3: HUMAN APPROVAL & LEGAL OPERATIONS
# ==========================================
with tab3:
    st.subheader("⚖️ Human Approval & Legal Operations Lifecycle")
    st.markdown("""
    <div class="approval-banner">
        <strong>⚠️ Human-in-the-Loop Safeguard Notice:</strong> AI findings are advisory recommendations. 
        Final legal approval requires explicit review, human decision-making, and audit trail logging.
    </div>
    """, unsafe_allow_html=True)

    db = SessionLocal()
    try:
        metrics = get_dashboard_metrics(db)
        cases_list = get_all_cases(db)
        
        # Operational Metrics Summary
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Cases", metrics["total_cases"])
        m2.metric("Pending Review", metrics["status"].get("PENDING_REVIEW", 0))
        m3.metric("Under Review", metrics["status"].get("UNDER_REVIEW", 0))
        m4.metric("Approved", metrics["status"].get("APPROVED", 0))
        m5.metric("Changes Req.", metrics["status"].get("CHANGES_REQUESTED", 0))
        m6.metric("Completed", metrics["status"].get("COMPLETED", 0))

        st.divider()

        if cases_list:
            case_options = {f"Case #{c.id}: {c.filename} [{c.status}]": c.id for c in cases_list}
            selected_case_label = st.selectbox("📌 Select Legal Case for Review / Operations:", list(case_options.keys()))
            target_case_id = case_options[selected_case_label]
            
            from backend.database.models import CaseDB
            case_detail = db.query(CaseDB).filter(CaseDB.id == target_case_id).first()
            
            rev_col, ops_col = st.columns([1, 1])

            # Left Column: Human Review Action Console
            with rev_col:
                st.markdown("### 📋 Human Review Console")
                st.info(f"**Current Status:** `{case_detail.status}` | **Assigned To:** `{case_detail.assigned_to}` | **Priority:** `{case_detail.priority}`")
                
                with st.expander("🤖 Structured Risk Analysis & Evidence", expanded=True):
                    if st.session_state.structured_risks:
                        res = st.session_state.structured_risks
                        for rf in res.risk_flags:
                            sev = str(getattr(rf, 'severity', 'MEDIUM')).upper()
                            st.markdown(f"**Clause {getattr(rf, 'clause_number', '')} — {getattr(rf, 'clause', 'Unknown')}**")
                            st.markdown(f"Risk: `{sev}` | Category: `{getattr(rf, 'clause_type', '')}`")
                            st.markdown(f"**Why Flagged:** {getattr(rf, 'rationale', '')}")
                            st.markdown(f"**Impact:** {getattr(rf, 'potential_impact', '')}")
                            st.markdown(f"**Recommendation:** {getattr(rf, 'recommendation', '')}")
                            
                            citations = getattr(rf, 'citations', [])
                            if citations:
                                for c in citations:
                                    st.caption(f"Source: {c.document_name} | Page: {c.page} | Clause: {c.clause}")
                                    st.caption(f"> {c.evidence_text}")
                            else:
                                st.caption("No verifiable citations found.")
                            st.divider()
                    else:
                        st.caption("No structured risk analysis available. Run the analysis in Tab 1 first.")
                        
                with st.expander("🤖 Original AI Analysis Snapshot (Immutable)", expanded=False):
                    latest_rev = case_detail.reviews[-1] if case_detail.reviews else None
                    ai_snap = latest_rev.ai_analysis_snapshot if latest_rev else case_detail.ai_summary
                    st.caption(ai_snap or "No AI snapshot recorded.")

                reviewer_name = st.text_input("Reviewer Name / Title:", value="Senior Counsel")
                reviewer_notes = st.text_area("Reviewer Notes & Feedback:", placeholder="Enter reason for approval, rejection, or required redline revisions...")
                
                btn_rev1, btn_rev2, btn_rev3 = st.columns(3)
                
                with btn_rev1:
                    if st.button("▶️ Start Review", use_container_width=True):
                        try:
                            start_review(db, target_case_id, reviewer=reviewer_name)
                            st.success("Case status moved to UNDER_REVIEW!")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))

                with btn_rev2:
                    if st.button("✅ Approve", type="primary", use_container_width=True):
                        try:
                            submit_review_decision(db, target_case_id, "APPROVED", reviewer=reviewer_name, reviewer_notes=reviewer_notes)
                            st.success("Case APPROVED by human reviewer!")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))

                with btn_rev3:
                    if st.button("❌ Reject", use_container_width=True):
                        try:
                            submit_review_decision(db, target_case_id, "REJECTED", reviewer=reviewer_name, reviewer_notes=reviewer_notes)
                            st.warning("Case REJECTED by human reviewer!")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))

                if st.button("⚠️ Request Changes", use_container_width=True):
                    try:
                        submit_review_decision(db, target_case_id, "CHANGES_REQUESTED", reviewer=reviewer_name, reviewer_notes=reviewer_notes)
                        st.warning("Status updated to CHANGES_REQUESTED!")
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))

            # Right Column: Legal Operations & Lifecycle Management
            with ops_col:
                st.markdown("### ⚙️ Operations Management")
                
                new_assignee = st.text_input("Reassign Case To:", value=case_detail.assigned_to)
                if st.button("👤 Reassign Case", use_container_width=True):
                    assign_case(db, target_case_id, assigned_to=new_assignee)
                    st.success(f"Case assigned to {new_assignee}!")
                    st.rerun()

                new_prio = st.selectbox("Set Case Priority:", ["LOW", "MEDIUM", "HIGH", "CRITICAL"], index=["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(case_detail.priority if case_detail.priority in ["LOW", "MEDIUM", "HIGH", "CRITICAL"] else "MEDIUM"))
                if st.button("⚡ Update Priority", use_container_width=True):
                    update_case_priority(db, target_case_id, priority=new_prio)
                    st.success(f"Priority updated to {new_prio}!")
                    st.rerun()

                comment_text = st.text_area("Add Internal Operations Note:", placeholder="Enter notes or updates for legal team...")
                if st.button("💬 Post Comment", use_container_width=True) and comment_text:
                    add_comment(db, target_case_id, author=reviewer_name, comment_text=comment_text)
                    st.success("Comment posted successfully!")
                    st.rerun()

                ops_b1, ops_b2 = st.columns(2)
                with ops_b1:
                    if st.button("🏁 Complete Case", use_container_width=True):
                        try:
                            complete_case(db, target_case_id)
                            st.success("Case COMPLETED!")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))
                with ops_b2:
                    if st.button("🔒 Close / Archive Case", use_container_width=True):
                        try:
                            close_case(db, target_case_id)
                            st.info("Case CLOSED and archived.")
                            st.rerun()
                        except Exception as ex:
                            st.error(str(ex))

            st.divider()
            
            # Bottom Section: Immutable Audit Trail Log Viewer
            st.markdown("### 📜 Immutable Audit Trail")
            if case_detail.audit_logs:
                audit_data = [
                    {
                        "ID": log.id,
                        "Action": log.action,
                        "Actor": log.actor,
                        "Prev Status": log.previous_status or "-",
                        "New Status": log.new_status or "-",
                        "Details": log.details,
                        "Timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for log in case_detail.audit_logs
                ]
                st.dataframe(audit_data, use_container_width=True)
            else:
                st.info("No audit entries recorded yet.")

    finally:
        db.close()

# ==========================================
# TAB 4: EXTRACTED CLAUSES & CHUNKS
# ==========================================
with tab4:
    st.subheader("📑 Extracted Clauses & Chunk Boundaries")
    if st.session_state.chunks:
        filter_term = st.text_input("🔍 Search clause text or header:", "")
        filtered = [
            c for c in st.session_state.chunks
            if filter_term.lower() in c["text"].lower() or filter_term.lower() in c["metadata"].get("clause", "").lower()
        ]
        st.write(f"Showing **{len(filtered)}** of **{len(st.session_state.chunks)}** chunks")
        for idx, item in enumerate(filtered):
            with st.expander(f"📍 Chunk #{idx+1} | Clause: {item['metadata'].get('clause', 'General Provision')} (Page {item['metadata'].get('page', 1)})"):
                st.markdown(f"**Text:**\n```text\n{item['text']}\n```")

# ==========================================
# TAB 5: DOCUMENT INSPECTOR
# ==========================================
with tab5:
    st.subheader("🔍 Full Extracted Raw Text Inspector")
    if st.session_state.raw_text:
        st.text_area(label="Extracted Normalized Text", value=st.session_state.raw_text, height=500)
        st.download_button(
            label="📥 Download Normalized Text (.txt)",
            data=st.session_state.raw_text,
            file_name=f"normalized_{st.session_state.filename}.txt",
            mime="text/plain"
        )

# Footer
st.markdown("""
<div class="footer-text">
    Tata Group AI Legal Intelligence System · Human-in-the-Loop Operations · ChromaDB · LangChain LangGraph
</div>
""", unsafe_allow_html=True)