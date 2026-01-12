import streamlit as st

# --- 1. CONFIGURATION MUST BE FIRST ---
st.set_page_config(page_title="CareerCraft AI", page_icon="🚀", layout="wide")

import os
from datetime import datetime

# --- 2. IMPORT CUSTOM MODULES ---
from resume_parse import extract_text_from_pdf
from skill_extract import get_resume_details, compare_resume_with_jd, get_final_score_and_suggestions
from llm import analyze_with_llm
from database.connection import engine, Base, SessionLocal
from database import crud
from job_search import find_jobs_realtime

# --- 3. DATABASE SETUP ---
Base.metadata.create_all(bind=engine)
SAVE_DIR = "resumes"
os.makedirs(SAVE_DIR, exist_ok=True)
FAKE_USER_ID = 1

# --- 4. SESSION STATE INITIALIZATION ---
if 'resume_text' not in st.session_state:
    st.session_state['resume_text'] = ""
if 'jd_text' not in st.session_state:
    st.session_state['jd_text'] = ""
if 'target_role' not in st.session_state:
    st.session_state['target_role'] = ""
if 'edit_session_id' not in st.session_state:
    st.session_state['edit_session_id'] = None
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "📊 Dashboard & Analyzer"

# --- 5. HELPER FUNCTIONS ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Alerts
@st.dialog("Confirm Deletion")
def confirm_delete_dialog(session_id):
    st.warning("⚠️ Are you sure you want to delete this analysis history permanently?")
    if st.button("Yes, Delete Permanently", type="primary"):
        db = SessionLocal()
        try:
            if crud.delete_analysis_session(db, session_id):
                st.success("Deleted!")
                st.rerun()
        finally:
            db.close()

# --- 6. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
    st.title("CareerCraft")
    
    # NAVIGATION LOGIC: Sync radio button index with session state
    nav_list = ["📊 Dashboard & Analyzer", "📜 History"]
    if st.session_state.get('current_page') == "📊 Dashboard & Analyzer":
        default_index = 0
    else:
        default_index = 1
    
    selected_page = st.radio(
        "Navigate", 
        nav_list, 
        index=default_index,
        key="main_navigation"
    )
    
    # Update state based on selection
    if selected_page != st.session_state['current_page']:
        st.session_state['current_page'] = selected_page
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ⚙️ User Profile")
    st.info(f"Logged in as: User #{FAKE_USER_ID}")
    if st.button("Logout"):
        st.write("Logged out (Demo)")

# =========================================================
# PAGE ROUTER
# =========================================================
page = st.session_state.get('current_page', "📊 Dashboard & Analyzer")

# =========================================================
# PAGE: DASHBOARD & ANALYZER
# =========================================================
if page == "📊 Dashboard & Analyzer":
    db_session = next(get_db())
    last_session = crud.get_latest_session(db_session, FAKE_USER_ID)
    
    # NEW: Check if we are in Edit Mode
    is_editing = st.session_state.get('edit_session_id') is not None

    # --- ONLY SHOW WELCOME/NOTIFICATIONS IF NOT EDITING ---
    if not is_editing:
        # --- 1. NOTIFICATION SYSTEM ---
        if 'notification_jobs' not in st.session_state:
            st.session_state['notification_jobs'] = []
            st.session_state['has_checked_notifications'] = False

        if last_session and not st.session_state['has_checked_notifications']:
            previous_role = last_session.output.best_suited_job if last_session.output else None
            if previous_role and previous_role != "Unknown Role":
                with st.spinner(f"🔔 Checking for new '{previous_role}' jobs..."):
                    new_jobs = find_jobs_realtime(previous_role, limit=3)
                    if new_jobs:
                        st.session_state['notification_jobs'] = new_jobs
                        st.toast(f"Found {len(new_jobs)} new jobs for you!", icon="🔔")
            st.session_state['has_checked_notifications'] = True

        if st.session_state['notification_jobs']:
            jobs = st.session_state['notification_jobs']
            with st.container():
                st.info(f"🔔 **Notification:** We found {len(jobs)} new openings.")
                with st.expander("📂 Click to view Job Listings"):
                    for job in jobs:
                        st.markdown(f"**[{job['title']}]({job['link']})**")
                    if st.button("Clear Notifications"):
                        st.session_state['notification_jobs'] = []
                        st.rerun()

        # --- 3. WELCOME SECTION ---
        st.markdown("## 👋 Welcome Back!")
        if last_session:
            match_score = last_session.output.fit_score if last_session.output else 0
            job_role = last_session.output.best_suited_job if last_session.output else "Unknown Role"
            st.markdown(f"""
            <div style="background-color: #001F3F; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                <h4>🚀 Last Session Recap</h4>
                <p>You analyzed a resume for a <strong>{job_role}</strong> position.</p>
                <p><strong>Score:</strong> {match_score}% | <strong>Date:</strong> {last_session.timestamp.strftime('%d %b, %Y')}</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("---")
    
    # --- 4. ANALYZER INTERFACE ---
    if is_editing:
        st.info(f"✨ **Currently Editing Analysis #{st.session_state['edit_session_id']}**")
        if st.button("❌ Cancel Edit & Back to New Analysis"):
            st.session_state['edit_session_id'] = None
            st.session_state['resume_text'] = ""
            st.session_state['jd_text'] = ""
            st.session_state['target_role'] = ""
            # Clear widget keys too
            if 'resume_text_area' in st.session_state: del st.session_state['resume_text_area']
            if 'jd_text_area' in st.session_state: del st.session_state['jd_text_area']
            if 'target_role_input' in st.session_state: del st.session_state['target_role_input']
            st.rerun()

    header_text = f"✏️ Edit Analysis #{st.session_state['edit_session_id']}" if st.session_state['edit_session_id'] else "🧠 New Analysis"
    st.subheader(header_text)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 1. Upload Resume")
        upload_type = st.radio("Input Type", ["PDF Upload", "Paste Text"], horizontal=True)
        if upload_type == "PDF Upload":
            resume_file = st.file_uploader("Drop PDF here", type=["pdf"], key="resume_uploader")
            if resume_file:
                st.session_state['resume_text'] = extract_text_from_pdf(resume_file)
        else:
            # FIX: Use key to sync with state
            st.session_state['resume_text'] = st.text_area(
                "Paste Resume", 
                value=st.session_state['resume_text'], 
                height=300,
                key="resume_text_area"
            )

    with col2:
        st.markdown("### 2. Job Details")
        # FIX: Use key to sync with state
        st.session_state['target_role'] = st.text_input(
            "Target Job Title", 
            value=st.session_state['target_role'],
            key="target_role_input"
        )
        
        # FIX: Use key to sync with state
        st.session_state['jd_text'] = st.text_area(
            "Paste Job Description (JD)", 
            value=st.session_state['jd_text'], 
            height=300,
            key="jd_text_area"
        )

    # --- 5. ACTION BUTTON ---
    button_label = "🔄 Update Analysis" if st.session_state['edit_session_id'] else "🚀 Analyze Alignment"
    analyze_btn = st.button(button_label, type="primary", use_container_width=True)

    if analyze_btn:
        # Read directly from session state which is synced with widgets
        if not st.session_state['resume_text'] or not st.session_state['jd_text'] or not st.session_state['target_role']:
            st.error("Please provide Resume, Job Description, and Target Job Title.")
        else:
            with st.spinner("🤖 Your data is being processed. It might take a few moments..."):
                # Analysis Logic
                resume_details = get_resume_details(st.session_state['resume_text'])
                analysis = compare_resume_with_jd(resume_details, st.session_state['jd_text'])
                score, keyword_match, skill_score = get_final_score_and_suggestions(analysis)
                llm_insight_text = analyze_with_llm(st.session_state['resume_text'], st.session_state['jd_text'])
                
                target_role = st.session_state['target_role'] # grab from state

                res_data = {
                    "fit_score": score, "keyword_match": keyword_match, "skill_match": skill_score,
                    "full_suggestion_text": llm_insight_text, "best_suited_job": target_role,
                    "suggested_location": "Kuala Lumpur, Malaysia",
                    "skill_matches": [{"skill_name": s, "status": "MISSING"} for s in analysis["missing_skills"]] + 
                                    [{"skill_name": s, "status": "MATCHED"} for s in analysis["matched_skills"]],
                    "job_listings": []
                }

                if st.session_state['edit_session_id']:
                    # --- UPDATE LOGIC ---
                    sess_id = st.session_state['edit_session_id']
                    crud.update_existing_analysis(db_session, sess_id, st.session_state['resume_text'], st.session_state['jd_text'])
                    crud.refresh_analysis_results(db_session, sess_id, res_data)
                    db_session.commit()
                    st.success(f"✅ Analysis #{sess_id} updated successfully!")
                    
                    # IMPORTANT: Do NOT clear the session state or ID here. 
                    # We want the user to see the result of their update.
                    # st.session_state['edit_session_id'] = None (REMOVED THIS)
                else:
                    # --- SAVE NEW LOGIC ---
                    crud.save_full_analysis(db_session, FAKE_USER_ID, st.session_state['resume_text'], st.session_state['jd_text'], res_data)
                    st.success(f"✅ New Analysis saved!")

                # --- 6. DISPLAY RESULTS ---
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Fit Score", f"{score}%")
                m2.metric("Keyword Match", f"{keyword_match}%")
                m3.metric("Skill Match", f"{skill_score}%")
                m4.metric("Missing Skills", len(analysis['missing_skills']), delta_color="inverse")

                tab1, tab2, tab3 = st.tabs(["💡 AI Feedback", "🛠 Skill Gap", "🌐 Real-time Jobs"])
                with tab1:
                    st.markdown(llm_insight_text)
                with tab2:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.error("Missing Skills")
                        for s in analysis['missing_skills']: st.write(f"- {s}")
                    with c2:
                        st.success("Matched Skills")
                        for s in analysis['matched_skills']: st.write(f"- {s}")
                with tab3:
                    st.markdown(f"### 🇲🇾 Jobs for '{target_role}' in Malaysia")
                    live_jobs = find_jobs_realtime(target_role, location="Malaysia")
                    if live_jobs:
                        for job in live_jobs:
                            with st.container():
                                st.markdown(f"**[{job['title']}]({job['link']})**")
                                st.caption(job['snippet'][:200] + "...")
                                st.divider()
                    else:
                        st.warning(f"No direct job listings found.")
    
    db_session.close()

# =========================================================
# PAGE: HISTORY
# =========================================================
elif page == "📜 History":
    st.title("📜 Analysis History")
    db_session = next(get_db())
    history = crud.get_user_history(db_session, FAKE_USER_ID)
    
    if not history:
        st.warning("No analysis history found.")
    else:
        for session in history:
            fit_score = session.output.fit_score if session.output else 0
            kw_match = session.output.keyword_match if session.output and hasattr(session.output, 'keyword_match') else 0
            matched_objs = [s for s in session.skills if s.status == 'MATCHED']
            missing_objs = [s for s in session.skills if s.status == 'MISSING']
            total_skills = len(matched_objs) + len(missing_objs)
            skill_match_score = round((len(matched_objs) / total_skills) * 100) if total_skills > 0 else 0
            date_str = session.timestamp.strftime("%d %b %Y, %H:%M")
            job_title = session.output.best_suited_job if session.output else "Analysis"

            with st.expander(f"**{date_str}** | {job_title} | Fit: **{fit_score}%**"):
                c_btn1, c_btn2 = st.columns([1, 5])
                
                # --- EDIT BUTTON (FIXED LOGIC) ---
                if c_btn1.button("✏️ Edit", key=f"edit_btn_{session.id}"):
                    # 1. Update the variables we use
                    st.session_state['resume_text'] = session.resume_text
                    st.session_state['jd_text'] = session.jd_text
                    st.session_state['target_role'] = job_title
                    
                    # 2. ALSO Update the specific widget Keys to ensure UI update
                    st.session_state['resume_text_area'] = session.resume_text
                    st.session_state['jd_text_area'] = session.jd_text
                    st.session_state['target_role_input'] = job_title
                    
                    # 3. Set flags
                    st.session_state['edit_session_id'] = session.id
                    st.session_state['current_page'] = "📊 Dashboard & Analyzer"
                    st.rerun()

                if c_btn2.button("🗑️ Delete", key=f"del_btn_{session.id}"):
                    confirm_delete_dialog(session.id)

                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Fit Score", f"{fit_score}%")
                m2.metric("Keyword Match", f"{kw_match}%")
                m3.metric("Skill Match", f"{skill_match_score}%")
                m4.metric("Missing Skills", len(missing_objs), delta_color="inverse")

                if session.output:
                    st.markdown("#### 💡 AI Feedback")
                    st.info(session.output.full_suggestion_text)

                st.markdown("#### 🛠 Skill Gap Analysis")
                col_miss, col_match = st.columns(2)
                with col_miss:
                    st.error("Missing Skills")
                    if missing_objs:
                        for s in missing_objs: st.write(f"- {s.skill_name}")
                    else: st.write("None! Perfect match.")
                
                with col_match:
                    st.success("Matched Skills")
                    if matched_objs:
                        for s in matched_objs: st.write(f"- {s.skill_name}")
                    else: st.write("No skills detected.")

    db_session.close()