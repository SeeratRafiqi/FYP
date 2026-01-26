import streamlit as st
import time
from datetime import timezone
from zoneinfo import ZoneInfo
from course_search import find_courses_for_skill
from collections import defaultdict
import pandas as pd
import altair as alt
from collections import defaultdict

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
# --- THEME STYLING ---
st.markdown("""
    <style>
:root {
        --primary-color: #ff4b4b;
        --background-color: #0E1117;
        --secondary-background-color: #262730;
        --text-color: #fafafa;
        --font: "Source Sans Pro", sans-serif;
    }

    /* 1. Main Background */
    .stApp, [data-testid="stHeader"] {
        background-color: #0E1117 !important;
    }

    /* 2. SIDEBAR FIX: Lighter than main page & White text */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #262730 !important;
    }
    [data-testid="stSidebar"] *, [data-testid="stSidebarNav"] span {
        color: #fafafa !important;
    }

    /* 3. Lock Subtext and General Text */
    p, span, label, .stCaptionContainer {
        color: #fafafa !important;
    }

    /* 4. Buttons */
    button[kind="secondary"] {
        background-color: #262730 !important;
        color: #fafafa !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
    }
    
    button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }

    /* 5. Metrics */
    [data-testid="stMetricValue"] {
        color: #00f2fe !important;
        font-size: 37px;
    }
    [data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
    }

    /* 6. Headers */
    h1, h2, h3 {
        color: #f0f2f6 !important;
        font-family: 'Inter', sans-serif;
        font-weight: 300;
    }
    h3 { font-size: 1.1rem !important; }

    /* 7. Input Boxes */
    .stTextArea textarea, .stTextInput input {
        background-color: #161a24 !important;
        color: #FAFAFA !important;
    }
            
    /* 8. File Uploader */
    [data-testid="stFileUploader"] section {
        background-color: #161a24 !important;
      
    }
    [data-testid="stFileUploader"] * {
        color: white !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #1e293b !important;
        color: white !important;
        border: 1px solid #334155 !important;
    }
.minty-text {
        color: #72efdd !important;
    }.white-text {
        color: #ffffff !important;
    }
            
    </style>
    """, unsafe_allow_html=True)

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
            font-weight: 1000 !important;
            color: #6DB6FF !important;
            margin-bottom: 0!important;
        }
        .hero-sub {
            color: #4CAF50 !important;
            font-size: 2.7rem !important;
            letter-spacing: 2px!important;
        } }
    [data-testid="stMetricLabel"] {
        color: #a0a0a0;
    }

    /* Subheader styling */
    h3 {
        color: #f0f2f6;
        font-family: 'Inter', sans-serif;
        font-weight: 300 !important;
        letter-spacing: 0.5px !important;
        font-size: 1.1rem !important;
    }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown('<p class="hero-sub !important">DISCOVER YOUR EDGE</p>', unsafe_allow_html=True)
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
    if 'current_page' not in st.session_state: st.session_state['current_page'] = "📊 Dashboard"

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

                # ✅ IMPORTANT: clear old LLM output
            st.session_state['last_analysis'] = None
            st.session_state['edit_session_id'] = session_data['id']
            st.session_state['current_page'] = "🧪 Analysis"
            st.rerun()

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712009.png", width=80)
        st.title("CareerCraft")
        
        nav_list = ["📊 Dashboard","🧪 Analysis", "📜 History"]
        #default_index = 0 if st.session_state.get('current_page') == "🧪 Analysis" else 1
        page_to_index = {
            "📊 Dashboard": 0,
            "🧪 Analysis": 1,
            "📜 History": 2
    }

        default_index = page_to_index.get(
                st.session_state.get('current_page'),
                0
            )
        
        selected_page = st.radio("Navigate", nav_list, index=default_index, key="main_navigation")
        st.markdown("---")

    # New Chat (session-level reset, like ChatGPT)
        if st.button("🧹 New Chat", use_container_width=True):
            # Reset ONLY safe state (do NOT touch widgets directly)
            st.session_state['resume_text'] = ""
            st.session_state['jd_text'] = ""
            st.session_state['target_role'] = ""
            st.session_state['last_analysis'] = None
            st.session_state['edit_session_id'] = None
            st.session_state['is_editing'] = False

            st.rerun()
        
        if selected_page != st.session_state['current_page']:
            st.session_state['current_page'] = selected_page
            st.rerun()
        
        st.markdown("---")
        st.info(f"User: {CURRENT_USER_NAME}")
        if st.button("Logout"):
            st.session_state['user_id'] = None
            st.rerun()

    # --- PAGES ---
    page = st.session_state.get('current_page', "🧪 Analysis")
    
   # ---------------------------
# PAGE: DASHBOARD
# ---------------------------

# ---------------------------
    CARD_HEIGHT = 273
    CHART_PADDING = {"left": 10, "right": 10, "top": 10, "bottom": 20}

    if page == "📊 Dashboard":
        
        st.title("📊 Dashboard")
        st.markdown("""  <style>
    /* Softer background */
    .stApp {  }

    /* More rounded cards */
    div[data-testid="stVerticalBlock"] > div:has(div.stExpander, div.element-container) {
       padding-top: 10px !important;
       padding-bottom: 10px !important;
       padding-left: 15px !important;
       padding-right: 15px !important;

        background-color: #1e293b;
        border-radius: 20px !important; /* Extra rounded for a friendly feel */
        border: 1px solid #334155;
    }

    /* Supportive Metrics */
    [data-testid="stMetricValue"] {
        color: #72efdd !important;
        font-size: 40px !important;
        font-weight: 500 !important;
    }
    
    /* Warm headers */
    h3 {
        color: #f8fafc !important;
        font-family: 'Inter', sans-serif;
        font-weight: 400 !important;
        font-size: 1.1rem !important;
    }
        CARD_HEIGHT = 240
       CHART_PADDING = {"left": 20, "right": 20, "top": 10, "bottom": 20}

    </style>""", unsafe_allow_html=True)
       
   
    # --- HEADER ---
        st.markdown(f"## 👋 Hi, {CURRENT_USER_NAME}!")
        
        db = next(get_db())
        last_session = crud.get_latest_session(db, CURRENT_USER_ID)
        history = crud.get_user_history(db, CURRENT_USER_ID)
        db.close()

        # --- TOP KPI ROW (The "Inspiration" Look) ---
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        #st.markdown(f"""<div style="font-size: 1.1rem !important;"></div>""", unsafe_allow_html=True)
        total_scans = len(history)
        avg_total_fit = sum([s.output.fit_score for s in history if s.output]) / total_scans if total_scans > 0 else 0
        history_sorted = sorted(history, key=lambda x: x.timestamp)
        fit_scores = [s.output.fit_score for s in history_sorted if s.output]

        trend_label = "Not enough data"

        if len(fit_scores) >= 3:
            recent_avg = sum(fit_scores[-2:]) / 2
            previous_avg = sum(fit_scores[:-2]) / len(fit_scores[:-2])

            if recent_avg > previous_avg + 2:
                trend_label = "📈 Improving"
            elif recent_avg < previous_avg - 2:
                trend_label = "📉Needs Attention"
            else:
                trend_label = "➖ Stable"
        
        with m_col1:
            st.metric("Total Scans", total_scans)
        with m_col2:
            st.metric("Avg Fit Score", f"{avg_total_fit:.1f}%")
        with m_col3:
            if last_session and last_session.output:
                st.metric("Latest Score", f"{last_session.output.fit_score}%")
            else:
                st.metric("Latest Score", "N/A")
        with m_col4:
                st.markdown(f"""
                    <div style="text-align: center; height: 70px; display: flex; flex-direction: column; justify-content: center;">
                        <div class="white-text" style="margin:0;font-size: 0.8rem; font-weight: 500; text-transform: uppercase;">Our Recent Discovery</div>
                        <div class="minty-text" style="margin:0; font-size: 1.5rem; font-weight: 700;">{trend_label}</div>
                    </div>
                """, unsafe_allow_html=True)

          


        st.markdown("---")

        # --- LAST SCAN HERO BANNER ---
        if last_session:
            match_score = last_session.output.fit_score if last_session.output else 0
            job_role = last_session.output.best_suited_job if last_session.output else "N/A"
            st.markdown(f"""
                <div style="  background: #161a24; width: 100%;  padding: 18px; border-radius: 10px; border-left: 4px solid #4facfe;margin-bottom: 20px;">
                    <p style="color:#a0a0a0; margin:0; font-size: 1.0rem; font-weight: 500; text-transform: uppercase;">Our recent discovery</p>
                    <h2 style="color:white; margin:0; font-size: 1.5rem;">{job_role} </span></h2>
                    
                </div>""", unsafe_allow_html=True)

        # Two-column layout for dashboard cards
        col1, col2 = st.columns(2)

        # Prep Data (Your core logic)
        role_scores = defaultdict(list)
        for s in history:
            if not s.output or not s.output.best_suited_job: continue
            role = s.output.best_suited_job.strip().title()
            role_scores[role].append(s.output.fit_score)

        # =========================
        # CARD 1: FIT SCORE BY ROLE (Aesthetic Bar)
        # =========================
        with col1:
            st.subheader("📈 How well you align with your goals?")
            
            avg_scores = [{"Role": r, "Score": sum(sc)/len(sc)} for r, sc in role_scores.items()]
            if not avg_scores:
                st.info("No data")
            else:
                df = pd.DataFrame(avg_scores)

                chart = (
                    alt.Chart(df)
                    .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, color="#479db0")
                    .encode(
                        x=alt.X("Role:N", axis=alt.Axis(labelAngle=-40, title="Analyzed Job Roles")),
                        y=alt.Y("Score:Q", axis=alt.Axis(grid=False, title="Avg Fit Score")),
                        tooltip=["Role", alt.Tooltip("Score:Q", format=".2f")]
                    )
                    .properties(height=CARD_HEIGHT, padding=CHART_PADDING)
                    .configure_view(strokeOpacity=0)
                )

                st.altair_chart(chart, use_container_width=True)


        # =========================
        # CARD 2: TOP ROLES (Vibrant Ranking)
        # =========================
        with col2:
            st.subheader("🏆 Roles That Best Fit Your Skills")

            if not role_scores:
                st.info("No data")
            else:
                df_top = (
                    pd.DataFrame(
                        [{"Role": r, "Score": sum(sc)/len(sc)} for r, sc in role_scores.items()]
                    )
                    .sort_values("Score", ascending=False)
                    .head(3)
                )
                chart = (
                    alt.Chart(df_top)
                    .mark_bar(cornerRadiusEnd=8)
                    .encode(
                        x=alt.X("Score:Q", title="Avg Fit Score"),
                        y=alt.Y("Role:N", sort='-x', title="Analyzed Job Roles"),
                        color=alt.Color(
                            "Role:N",
                            scale=alt.Scale(range=["#5a4479", "#7932b2", "#cf90ff"]),
                            legend=None
                        ),
                        tooltip=["Role", alt.Tooltip("Score:Q", format=".2f")]
                    )
                    .properties(height=CARD_HEIGHT, padding=CHART_PADDING)
                    .configure_view(strokeOpacity=0)
                )

                st.altair_chart(chart, use_container_width=True)
        # =========================
        # CARD 3: RESUME STRENGTH (Minimalist Donut)
        # =========================
        with col1:
            st.subheader("🧠 Your Skill Coverage Overview")

            matched = sum(1 for s in history for sk in getattr(s, "skills", []) if sk.status == "MATCHED")
            missing = sum(1 for s in history for sk in getattr(s, "skills", []) if sk.status == "MISSING")

            if matched + missing == 0:
                st.info("No skill data")
            else:
                df = pd.DataFrame({
                    "Status": ["Matched", "Missing"],
                    "Count": [matched, missing]
                })

                chart = (
                    alt.Chart(df)
                    .mark_arc(innerRadius=50, outerRadius=105, stroke="#161a24", strokeWidth=2)
                    .encode(
                        theta="Count:Q",
                        color=alt.Color(
                            "Status:N",
                            scale=alt.Scale(range=["#48cae4", "#df7141"]),
                            legend=None
                        ),
                        tooltip=["Status", "Count"]
                    )
                    .properties(height=CARD_HEIGHT, padding=CHART_PADDING)
                )

                st.altair_chart(chart, use_container_width=True)


        # =========================
        # CARD 4: SKILL GAPS (Neon Horizontal)
        # =========================
        with col2:
            st.subheader("🧩 Skills You May Want to Strengthen")

            skill_counts = defaultdict(int)
            for s in history:
                for sk in getattr(s, "skills", []):
                    if sk.status == "MISSING":
                        skill_counts[sk.skill_name] += 1

            if not skill_counts:
                st.info("No data")
            else:
                df = (
                    pd.DataFrame([{"Skill": k, "Freq": v} for k, v in skill_counts.items()])
                    .sort_values("Freq", ascending=False)
                    .head(5)
                )

                chart = (
                    alt.Chart(df)
                    .mark_rule(color="#ff4ecd")
                    .encode(x=alt.X("Freq:Q", title="Frequency of Missing Skill Occurrence"), y=alt.Y("Skill:N", sort='-x', title="Skills"))
                    +
                    alt.Chart(df)
                    .mark_circle(size=120, color="#ff4ecd")
                    .encode(
                        x="Freq:Q",
                        y="Skill:N",
                        tooltip=["Skill", "Freq"]
                    )
                ).properties(height=CARD_HEIGHT, padding=CHART_PADDING).configure_view(strokeOpacity=0)

                st.altair_chart(chart, use_container_width=True)



    # ---------------------------
    # PAGE: DASHBOARD
    # ---------------------------
    elif page == "🧪 Analysis":
        db_session = next(get_db())
        last_session = crud.get_latest_session(db_session, CURRENT_USER_ID)
        is_editing = st.session_state.get('edit_session_id') is not None
        # --- Agentic Notification ---
          
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
                    st.markdown(f"""
                        <div style="background: rgba(82, 183, 136, 0.1); padding: 20px; border-radius: 15px; border: 1px solid #52b788; margin-bottom: 20px;">
                            <h4 style="margin:0; color:#52b788; font-size: 1.1rem;">👋 I've been looking around for you!</h4>
                            <p style="color:#dae1e7; margin:5px 0 15px 0; font-size: 0.9rem;">
                                Based on our last chat, I found <b>3 new roles</b> that might be a great fit for your journey.
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                    with st.expander("✨ View these opportunities"):
                        for job in st.session_state['notification_jobs']:
                            st.markdown(f"**[{job['title']}]({job['link']})**")
                        if st.button("Clear"):
                            st.session_state['notification_jobs'] = []
                            st.rerun()

            
            
            st.markdown("---")

        # EDIT MODE BANNER
        if is_editing:
            st.warning(f"✏️ Editing Analysis ")

        # INPUTS
        st.markdown(f"<div style='font-size: 1.9rem; font-weight: bold; color: #48d1cc;'>🌱 Let's work on your next move together</div>", unsafe_allow_html=True)
        st.write("Upload your story (resume) and tell me where you'd like to go next.")
        st.markdown("<div style='margin-bottom: 16px;'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"<div style='font-size: 1.25rem; font-weight: bold; color: #ffffff;'>✨ 1. Your Background</div>", unsafe_allow_html=True)
            # Using a helper text to make it feel guided
            st.caption("How would you like to share your experience with me?")
            

            utype = st.radio("Type", ["PDF Upload", "Paste Text"], horizontal=True)
            if utype == "PDF Upload":
                f = st.file_uploader("PDF", type=["pdf"])
                if f: st.session_state['resume_text'] = extract_text_from_pdf(f)
            else:
                st.session_state['resume_text'] = st.text_area("Paste your resume here...", value=st.session_state['resume_text'], height=245, key="resume_text_area")


        with c2:
            st.markdown(f"<div style='font-size: 1.25rem; font-weight: bold;color: #ffffff;'>🎯 2. Your Goal</div>", unsafe_allow_html=True)
            st.session_state['target_role'] = st.text_input("What\'s the dream role we\'re looking at today?",value=st.session_state['target_role'], key="target_role_input", placeholder="e.g. Mobile Application Developer")
            st.session_state['jd_text'] = st.text_area("Tell me a bit about the job requirements:", placeholder="Paste the job details here...", height=285, value=st.session_state['jd_text'],  key="jd_text_area")
            
            



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
                    llm = analyze_with_llm(st.session_state['resume_text'], st.session_state['jd_text'],an['matched_skills'], an['missing_skills'])
                    
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
                        st.session_state['last_analysis'] = {
                            "sc": sc,
                            "kw": kw,
                            "sk": sk,
                            "an": an,
                            "llm": llm,
                            "role": st.session_state['target_role']}
                        
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

                    
                    t1, t2, t3, t4 = st.tabs(["🛠 Skill Map","💡My Feedback","🧭 Other Paths to Explore", "🌍 Job openings for you"])
                    # t1, t2, t3, t4 = st.tabs(["💡 Craft Analysis ","Your path","🛠 Your Toolkit", "🌍 Oppurtunities for you"])

                    
                   
                    with t1:
                        c1, c2 = st.columns(2)

                        # -------- Missing Skills --------
                        with c1:
                            st.error("Missing Skills")

                            if an['missing_skills']:
                                for skill in an['missing_skills']:
                                    st.write(f"- {skill}")

                                st.markdown("### 📘 Learning Resources")

                                with st.expander("View courses for missing skills"):
                                    for skill in an['missing_skills']:
                                        st.markdown(f"**🔹 {skill}**")
                                        courses = find_courses_for_skill(skill)

                                        for c in courses:
                                            st.markdown(f"- [{c['title']}]({c['link']})")
                                            if c.get("snippet"):
                                                st.caption(c["snippet"])
                                                
                            else:
                                st.write("No missing skills 🎉")
                    

                        # -------- Matched Skills --------
                        with c2:
                            st.success("Matched Skills")
                            for skill in an['matched_skills']:
                                st.write(f"- {skill}")
                    with t2: st.markdown(llm_main)
                    with t3: 
                        st.markdown(llm_career)
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