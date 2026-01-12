import streamlit as st
st.set_page_config(page_title="CareerCraft — History", layout="wide")

import os
from datetime import datetime

from database.connection import engine, Base, SessionLocal
from database import models, crud

from skill_extract import (
    get_resume_details,
    compare_resume_with_jd,
    get_final_score_and_suggestions,
)

# ----------- Helper functions -----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def parse_llm_sections(raw_text: str):
    sections = []
    current_title = "Overall Feedback"
    buffer = []

    for line in (raw_text or "").splitlines():
        stripped = line.strip()
        if stripped.startswith("###"):
            if buffer:
                sections.append((current_title, "\n".join(buffer).strip()))
            current_title = stripped.lstrip("#").strip()
            buffer = []
        else:
            buffer.append(line)

    if buffer:
        sections.append((current_title, "\n".join(buffer).strip()))

    return sections

# ----------- Page UI -----------

st.title("📜 Analysis History")

FAKE_USER_ID = 1

db_session = next(get_db())
try:
    sessions = crud.get_user_history(db_session, user_id=FAKE_USER_ID)
finally:
    db_session.close()

if not sessions:
    st.info("No past analyses found yet. Run an analysis first.")
else:
    for s in sessions:
        fit = s.output.fit_score if s.output else None

        header = f"Session #{s.id} — {s.timestamp.strftime('%Y-%m-%d %H:%M')} — Fit: {fit if fit is not None else 'N/A'}%"

        with st.expander(header):

            # recompute for display
            resume_details_hist = get_resume_details(s.resume_text)
            analysis_hist = compare_resume_with_jd(resume_details_hist, s.jd_text)
            score_hist, keyword_match_hist = get_final_score_and_suggestions(analysis_hist)

            st.markdown("### 📊 Scores")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Similarity Score", f"{score_hist}%")
            with c2:
                st.metric("Keyword Match Score", f"{keyword_match_hist}%")

            st.markdown("### 🛠 Skills Overview")
            st.write(f"**Matched Skills:** {', '.join(analysis_hist['matched_skills']) or 'None'}")
            st.write(f"**Missing Skills:** {', '.join(analysis_hist['missing_skills']) or 'None'}")

            st.markdown("### 📄 Resume (preview)")
            resume_preview = (s.resume_text[:500] + "...") if len(s.resume_text) > 500 else s.resume_text
            st.write(resume_preview)

            if s.resume_pdf_path:
                st.download_button(
                    "📄 Download Resume (PDF)",
                    data=open(s.resume_pdf_path, "rb").read(),
                    file_name=os.path.basename(s.resume_pdf_path),
                    mime="application/pdf"
                )

            st.markdown("### 📄 Job Description (preview)")
            jd_preview = (s.jd_text[:500] + "...") if len(s.jd_text) > 500 else s.jd_text
            st.write(jd_preview)

            if s.output and s.output.full_suggestion_text:
                st.markdown("### 🤖 LLM Feedback")
                sections = parse_llm_sections(s.output.full_suggestion_text)

                if not sections:
                    st.markdown(s.output.full_suggestion_text)
                else:
                    for i in range(0, len(sections), 2):
                        row_sections = sections[i:i+2]
                        cols = st.columns(len(row_sections))
                        for col, (title, content) in zip(cols, row_sections):
                            with col:
                                st.markdown(
                                    f"""
                                    <div style="
                                        border:1px solid #e0e0e0;
                                        border-radius:12px;
                                        padding:16px;
                                        background:#f9f9f9;
                                        margin-bottom:16px;">
                                        <strong>{title}</strong><br>
                                        {content}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
