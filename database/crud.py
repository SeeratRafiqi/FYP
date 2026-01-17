# database/crud.py
from sqlalchemy.orm import Session, joinedload
from . import models
from datetime import datetime
from typing import List, Dict

# --- NEW: USER AUTHENTICATION ---
def create_user(db: Session, email, name, password):
    user = models.User(email=email, name=name, password=password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# ... (Keep existing history, delete, update, refresh, save functions exactly as before) ...
def get_user_history(db: Session, user_id: int):
    return (
        db.query(models.AnalysisSession)
        .options(joinedload(models.AnalysisSession.output),
                 joinedload(models.AnalysisSession.skills),
                 joinedload(models.AnalysisSession.jobs))
        .filter(models.AnalysisSession.user_id == user_id)
        .order_by(models.AnalysisSession.timestamp.desc())
        .all()
    )

def get_latest_session(db: Session, user_id: int):
    return (
        db.query(models.AnalysisSession)
        .options(joinedload(models.AnalysisSession.output))
        .filter(models.AnalysisSession.user_id == user_id)
        .order_by(models.AnalysisSession.timestamp.desc())
        .first()
    )

def delete_analysis_session(db: Session, session_id: int):
    try:
        session = db.query(models.AnalysisSession).filter(models.AnalysisSession.id == session_id).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        return False

def update_existing_analysis(db: Session, session_id: int, new_resume: str = None, new_jd: str = None):
    try:
        db_session = db.query(models.AnalysisSession).filter(models.AnalysisSession.id == session_id).first()
        if not db_session: return None
        if new_resume: db_session.resume_text = new_resume
        if new_jd: db_session.jd_text = new_jd
        db_session.timestamp = datetime.utcnow()
        db.flush()
        db.refresh(db_session)
        return db_session
    except Exception as e:
        db.rollback()
        raise e

def refresh_analysis_results(db: Session, session_id: int, new_data: Dict):
    try:
        db.query(models.LLMOutput).filter(models.LLMOutput.session_id == session_id).delete(synchronize_session='fetch')
        db.query(models.SkillMatch).filter(models.SkillMatch.session_id == session_id).delete(synchronize_session='fetch')
        db.query(models.JobListing).filter(models.JobListing.session_id == session_id).delete(synchronize_session='fetch')
        
        db_output = models.LLMOutput(
            session_id=session_id,
            fit_score=new_data.get("fit_score"),
            keyword_match=new_data.get("keyword_match"),
            skill_match=new_data.get("skill_match"),
            full_suggestion_text=new_data.get("full_suggestion_text"),
            best_suited_job=new_data.get("best_suited_job"),
            suggested_location=new_data.get("suggested_location")
        )
        db.add(db_output)

        for skill in new_data.get("skill_matches", []):
            db.add(models.SkillMatch(session_id=session_id, skill_name=skill['skill_name'], status=skill['status']))

        for job in new_data.get("job_listings", []):
            db.add(models.JobListing(session_id=session_id, title=job.get('title'), company=job.get('company'), location=job.get('location'), url=job.get('url')))
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e

def save_full_analysis(db: Session, user_id: int, resume_text: str, jd_text: str, analysis_data: Dict, resume_pdf_path: str = None):
    try:
        db_session = models.AnalysisSession(user_id=user_id, resume_text=resume_text, jd_text=jd_text, resume_pdf_path=resume_pdf_path, timestamp=datetime.utcnow())
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        db_output = models.LLMOutput(
            session_id=db_session.id,
            fit_score=analysis_data.get("fit_score"),
            keyword_match=analysis_data.get("keyword_match"), 
            skill_match=analysis_data.get("skill_match"),
            full_suggestion_text=analysis_data.get("full_suggestion_text"),
            best_suited_job=analysis_data.get("best_suited_job"),
            suggested_location=analysis_data.get("suggested_location")
        )
        db.add(db_output)

        for skill in analysis_data.get("skill_matches", []):
            db.add(models.SkillMatch(session_id=db_session.id, skill_name=skill['skill_name'], status=skill['status']))

        for job in analysis_data.get("job_listings", []):
            db.add(models.JobListing(session_id=db_session.id, title=job.get('title'), company=job.get('company'), location=job.get('location'), url=job.get('url')))
        
        db.commit()
        return db_session.id
    except Exception as e:
        db.rollback()
        raise e