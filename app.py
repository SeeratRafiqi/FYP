import streamlit as st
import time
from datetime import timezone
from zoneinfo import ZoneInfo

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="CareerCraft AI", page_icon="🚀", layout="wide")

import os
from datetime import datetime

# --- 2. IMPORTS ---
from resume_parse import extract_text_from_pdf
from skill_extract import get_resume_details, compare_resume_with_jd, get_final_score_and_suggestions
from llm import analyze_with_llm
from database.connection import engine, Base, SessionLocal
from database import crud
from job_search import find_jobs_realtime

# --- 3. DATABASE ---
Base.metadata.create_all(bind=engine)
SAVE_DIR = "resumes"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- 4. SESSION STATE ---
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'username' not in st.session_state: st.session_state['username'] = None

# --- HELPER: DB Connection ---
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# =========================================================
# 🔒 AUTHENTICATION LOGIC (LOGIN SCREEN)
# =========================================================
def show_login_page():
    # CSS for Aesthetic Login
    st.markdown("""
        <style>
        .login-container {
            padding: 1000px !important;
            border-radius: 10px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.1);
            background: white;
            text-align: center;
        }
        .hero-title {
            font-size: 3rem !important;
            font-weight: 1000;
            color: #6DB6FF ;
            margin-bottom: 0;
        }
        .hero-sub {
            color: #4CAF50;
            font-size: 2.7rem !important;
            letter-spacing: 2px;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="hero-sub">DISCOVER YOUR EDGE</p>', unsafe_allow_html=True)
        st.markdown('<p class="hero-title">CareerCraft </p>', unsafe_allow_html=True)
        st.markdown("### Step into your future, smartly.")
        st.markdown(""" <div style="font-size: 20px; color: #555; margin-top: 10px;">   An agentic resume analyzer powered by LLMs and Real-time Job Search.
                </div>""", unsafe_allow_html=True)
        
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=200)

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Welcome")
            tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

            with tab_login:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                if st.button("Login ➜", use_container_width=True):
                    db = next(get_db())
                    user = crud.get_user_by_email(db, email)
                    if user and user.password == password:
                        st.session_state['user_id'] = user.id
                        st.session_state['username'] = user.name
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
            
            with tab_signup:
                new_name = st.text_input("Full Name", key="sub_name")
                new_email = st.text_input("Email", key="sub_email")
                new_pass = st.text_input("Password", type="password", key="sub_pass")
                if st.button("Create Account", use_container_width=True):
                    db = next(get_db())
                    if crud.get_user_by_email(db, new_email):
                        st.error("Email already exists.")
                    else:
                        user = crud.create_user(db, new_email, new_name, new_pass)
                        st.success("Account created! Please login.")

# =========================================================
# MAIN APP ROUTER
# =========================================================
if not st.session_state['user_id']:
    show_login_page()
else:
    # --- GLOBAL CONSTANT FOR CURRENT USER ---
    CURRENT_USER_ID = st.session_state['user_id']
    CURRENT_USER_NAME = st.session_state['username']

    # --- SESSION STATE INIT (App Specific) ---
    if 'resume_text' not in st.session_state: st.session_state['resume_text'] = ""
    if 'jd_text' not in st.session_state: st.session_state['jd_text'] = ""
    if 'target_role' not in st.session_state: st.session_state['target_role'] = ""
    if 'edit_session_id' not in st.session_state: st.session_state['edit_session_id'] = None
    if 'current_page' not in st.session_state: st.session_state['current_page'] = "📊 Dashboard & Analyzer"

    # --- HELPER FUNCTIONS ---
    @st.dialog("Confirm Deletion")
    def confirm_delete_dialog(session_id):
        st.warning("Are you sure you want to delete this?")
        if st.button("Yes, Delete"):
            db = SessionLocal()
            try:
                crud.delete_analysis_session(db, session_id)
                st.rerun()
            finally: db.close()

    @st.dialog("Confirm Edit")
    def confirm_edit_dialog(session_data):
        st.write(f"Edit analysis for **{session_data['job_title']}**?")
        if st.button("Yes, Load"):
            st.session_state['resume_text'] = session_data['resume_text']
            st.session_state['jd_text'] = session_data['jd_text']
            st.session_state['target_role'] = session_data['job_title']
            
            st.session_state['resume_text_area'] = session_data['resume_text']
            st.session_state['jd_text_area'] = session_data['jd_text']
            st.session_state['target_role_input'] = session_data['job_title']

            st.session_state['edit_session_id'] = session_data['id']
            st.session_state['current_page'] = "📊 Dashboard & Analyzer"
            st.rerun()

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
        st.title("CareerCraft")
        
        nav_list = ["📊 Dashboard & Analyzer", "📜 History"]
        default_index = 0 if st.session_state.get('current_page') == "📊 Dashboard & Analyzer" else 1
        
        selected_page = st.radio("Navigate", nav_list, index=default_index, key="main_navigation")
        
        if selected_page != st.session_state['current_page']:
            st.session_state['current_page'] = selected_page
            st.rerun()
        
        st.markdown("---")
        st.info(f"User: {CURRENT_USER_NAME}")
        if st.button("Logout"):
            st.session_state['user_id'] = None
            st.rerun()

    # --- PAGES ---
    page = st.session_state.get('current_page', "📊 Dashboard & Analyzer")
    
    # ---------------------------
    # PAGE: DASHBOARD
    # ---------------------------
    if page == "📊 Dashboard & Analyzer":
        db_session = next(get_db())
        last_session = crud.get_latest_session(db_session, CURRENT_USER_ID)
        is_editing = st.session_state.get('edit_session_id') is not None

        if not is_editing:
            # Notifications
            if 'notification_jobs' not in st.session_state: st.session_state['notification_jobs'] = []
            if 'has_checked_notifications' not in st.session_state: st.session_state['has_checked_notifications'] = False

            if last_session and not st.session_state['has_checked_notifications']:
                prev_role = last_session.output.best_suited_job if last_session.output else None
                if prev_role and prev_role != "Unknown Role":
                    with st.spinner(f"🔔 Finding jobs for {prev_role}..."):
                        new_jobs = find_jobs_realtime(prev_role, limit=3)
                        if new_jobs:
                            st.session_state['notification_jobs'] = new_jobs
                            st.toast(f"{len(new_jobs)} new jobs found!", icon="🔔")
                st.session_state['has_checked_notifications'] = True

            if st.session_state['notification_jobs']:
                with st.container():
                    st.info(f"🔔 Found {len(st.session_state['notification_jobs'])} new jobs.")
                    with st.expander("View Jobs"):
                        for job in st.session_state['notification_jobs']:
                            st.markdown(f"**[{job['title']}]({job['link']})**")
                        if st.button("Clear"):
                            st.session_state['notification_jobs'] = []
                            st.rerun()

            st.markdown(f"## 👋 Hi, {CURRENT_USER_NAME}!")
            if last_session:
                match_score = last_session.output.fit_score if last_session.output else 0
                job_role = last_session.output.best_suited_job if last_session.output else "N/A"
                st.markdown(f"""
                <div style="background-color: #001F3F; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                    <p style="color:white; margin:0;">Last Scan: <strong>{job_role}</strong> | Score: <strong>{match_score}%</strong></p>
                </div>""", unsafe_allow_html=True)
            st.markdown("---")

        # EDIT MODE BANNER
        if is_editing:
            st.warning(f"✏️ Editing Analysis #{st.session_state['edit_session_id']}")
            if st.button("Cancel Edit"):
                st.session_state['edit_session_id'] = None
                st.session_state['resume_text'] = ""
                st.session_state['jd_text'] = ""
                st.session_state['target_role'] = ""
                if 'resume_text_area' in st.session_state: del st.session_state['resume_text_area']
                if 'jd_text_area' in st.session_state: del st.session_state['jd_text_area']
                st.rerun()

        # INPUTS
        st.subheader("🧠 New Analysis" if not is_editing else "✏️ Edit Analysis")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 1. Upload Resume")
            utype = st.radio("Type", ["PDF Upload", "Paste Text"], horizontal=True)
            if utype == "PDF Upload":
                f = st.file_uploader("PDF", type=["pdf"])
                if f: st.session_state['resume_text'] = extract_text_from_pdf(f)
            else:
                st.session_state['resume_text'] = st.text_area("Resume Text", value=st.session_state['resume_text'], height=300, key="resume_text_area")

        with c2:
            st.markdown("### 2. Job Details")
            st.session_state['target_role'] = st.text_input("Target Role", value=st.session_state['target_role'], key="target_role_input")
            st.session_state['jd_text'] = st.text_area("Job Description", value=st.session_state['jd_text'], height=300, key="jd_text_area")

        # ANALYZE BUTTON
        btn_txt = "🔄 Update" if is_editing else "🚀 Analyze"
        clicked = st.button(btn_txt, type="primary", use_container_width=True)
        if clicked:
            if not st.session_state['resume_text'] or not st.session_state['jd_text']:
                st.error("Missing inputs.")
            else:
                with st.spinner("Analyzing..."):
                    rd = get_resume_details(st.session_state['resume_text'])
                    an = compare_resume_with_jd(rd, st.session_state['jd_text'])
                    sc, kw, sk = get_final_score_and_suggestions(an)
                    llm = analyze_with_llm(st.session_state['resume_text'], st.session_state['jd_text'])
                    
                    data = {
                        "fit_score": sc, "keyword_match": kw, "skill_match": sk,
                        "full_suggestion_text": llm, "best_suited_job": st.session_state['target_role'],
                        "suggested_location": "Malaysia",
                        "skill_matches": [{"skill_name": s, "status": "MISSING"} for s in an["missing_skills"]] + 
                                         [{"skill_name": s, "status": "MATCHED"} for s in an["matched_skills"]],
                        "job_listings": []
                    }

                    if is_editing:
                        sid = st.session_state['edit_session_id']
                        crud.update_existing_analysis(db_session, sid, st.session_state['resume_text'], st.session_state['jd_text'])
                        crud.refresh_analysis_results(db_session, sid, data)
                        db_session.commit()
                        st.success("Updated!")
                        st.session_state['edit_session_id'] = None
                    else:
                        crud.save_full_analysis(db_session, CURRENT_USER_ID, st.session_state['resume_text'], st.session_state['jd_text'], data)
                        st.success("Saved!")

                        st.session_state['last_analysis'] = {
                        "sc": sc, "kw": kw, "sk": sk, "an": an, "llm": llm, "role": st.session_state['target_role']
                    }
                    

        if 'last_analysis' in st.session_state and st.session_state['last_analysis']:
                    res = st.session_state['last_analysis']
                    
                    # Extract variables from state for cleaner code
                    sc, kw, sk, an, llm = res['sc'], res['kw'], res['sk'], res['an'], res['llm']

                    # Results
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Fit", f"{sc}%")
                    m2.metric("Keyword", f"{kw}%")
                    m3.metric("Skill", f"{sk}%")
                    m4.metric("Missing", len(an['missing_skills']), delta_color="inverse")
                    
                    def split_career_alignment(llm_text):
                     markers = [
                        "### 4. Career Role Alignment",
                        "### 3. Career Role Alignment",
                        "### Career Role Alignment",
                        "### Career Alignment",
                    ]
                     for header in markers:
                        if header in llm_text:
                            before, after = llm_text.split(header, 1)
                            return before.strip(), after.strip()

                     return llm_text, "⚠️ Career alignment section not found."
                    llm_main, llm_career = split_career_alignment(llm)

                    
                    t1, t2, t3, t4 = st.tabs(["💡 AI Feedback","Career Alignment","🛠 Skills", "🌍 Jobs"])
                    with t1: st.markdown(llm_main)
                    with t2: 
                        st.subheader("🎯 Career Alignment")
                        st.markdown(llm_career)
                    with t3:
                        c1, c2 = st.columns(2)
                        with c1:
                            st.error("Missing Skills")
                            for skills in an['missing_skills']:
                                st.write(f"- {skills}")
                        with c2:
                            st.success("Matched Skills")
                            for skills in an['matched_skills']:
                                st.write(f"- {skills}")

                    with t4:
                        jobs = find_jobs_realtime(st.session_state['target_role'])
                        if jobs:
                            for j in jobs: st.markdown(f"[{j['title']}]({j['link']})")

        db_session.close()

    # ---------------------------
    # PAGE: HISTORY
    # ---------------------------
    elif page == "📜 History":
        st.title("📜 History")
        db = next(get_db())
        hist = crud.get_user_history(db, CURRENT_USER_ID)
        
        if not hist:
            st.info("No history yet.")
        else:
            for s in hist:
                fit = s.output.fit_score if s.output else 0
                kw_match = s.output.keyword_match if s.output and hasattr(s.output, 'keyword_match') else 0
                matched_objs = [s for s in s.skills if s.status == 'MATCHED']
                missing_objs = [s for s in s.skills if s.status == 'MISSING']
                total_skills = len(matched_objs) + len(missing_objs)
                skill_match_score = round((len(matched_objs) / total_skills) * 100) if total_skills > 0 else 0
                job = s.output.best_suited_job if s.output else "Analysis"
                
                myt = ZoneInfo("Asia/Kuala_Lumpur")

                date = (
                s.timestamp
               .replace(tzinfo=timezone.utc)   # 👈 THIS is the missing step
               .astimezone(myt)
               .strftime("%d %b, %H:%M")
             )
                
                with st.expander(f"{date} | {job} | {fit}%"):
                    c1, c2 = st.columns([1, 5])
                    if c1.button("✏️ Edit", key=f"e_{s.id}"):
                        data = {"id": s.id, "resume_text": s.resume_text, "jd_text": s.jd_text, "job_title": job}
                        confirm_edit_dialog(data)
                    
                    if c2.button("🗑️ Delete", key=f"d_{s.id}"):
                        confirm_delete_dialog(s.id)
                    st.divider()
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Fit Score", f"{fit}%")
                    m2.metric("Keyword Match", f"{kw_match}%")
                    m3.metric("Skill Match", f"{skill_match_score}%")
                    m4.metric("Missing Skills", len(missing_objs), delta_color="inverse")
                    if s.output: st.info(s.output.full_suggestion_text)
                    
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

        db.close()