# database/crud.py
from sqlalchemy.orm import Session, joinedload
from . import models
from datetime import datetime
from typing import List, Dict

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
        print(f"Delete error: {e}")
        return False

# --- UPDATED: Better update function ---
def update_existing_analysis(db: Session, session_id: int, new_resume: str = None, new_jd: str = None):
    """
    Updates the resume and JD text for an existing analysis session.
    Note: This should be called BEFORE refresh_analysis_results()
    """
    try:
        db_session = db.query(models.AnalysisSession).filter(models.AnalysisSession.id == session_id).first()
        
        if not db_session:
            print(f"Session {session_id} not found")
            return None
            
        # Update text fields
        if new_resume:
            db_session.resume_text = new_resume
        if new_jd:
            db_session.jd_text = new_jd
            
        # Update timestamp
        db_session.timestamp = datetime.utcnow()
        
        # Flush changes but don't commit yet (let the caller commit)
        db.flush()
        db.refresh(db_session)
        
        print(f"✅ Updated session {session_id} texts")
        return db_session
        
    except Exception as e:
        db.rollback()
        print(f"Update error: {e}")
        raise e

def refresh_analysis_results(db: Session, session_id: int, new_data: Dict):
    """
    Deletes old analysis results and creates new ones.
    This includes: LLM Output, Skills, and Jobs.
    """
    try:
        print(f"🔄 Refreshing results for session {session_id}")
        
        # 1. Delete old data with 'fetch' synchronization
        deleted_outputs = db.query(models.LLMOutput).filter(models.LLMOutput.session_id == session_id).delete(synchronize_session='fetch')
        deleted_skills = db.query(models.SkillMatch).filter(models.SkillMatch.session_id == session_id).delete(synchronize_session='fetch')
        deleted_jobs = db.query(models.JobListing).filter(models.JobListing.session_id == session_id).delete(synchronize_session='fetch')
        
        print(f"  Deleted: {deleted_outputs} outputs, {deleted_skills} skills, {deleted_jobs} jobs")
        
        # 2. Create new Output
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
        print(f"  ✅ Added new output with fit_score={new_data.get('fit_score')}")

        # 3. Create new Skills
        skill_count = 0
        for skill in new_data.get("skill_matches", []):
            db.add(models.SkillMatch(
                session_id=session_id, 
                skill_name=skill['skill_name'], 
                status=skill['status']
            ))
            skill_count += 1
        print(f"  ✅ Added {skill_count} skills")

        # 4. Create new Jobs (if any)
        job_count = 0
        for job in new_data.get("job_listings", []):
            db.add(models.JobListing(
                session_id=session_id,
                title=job.get('title'),
                company=job.get('company'),
                location=job.get('location'),
                url=job.get('url')
            ))
            job_count += 1
        print(f"  ✅ Added {job_count} jobs")

        # Flush to ensure all changes are ready
        db.flush()
        print(f"✅ Successfully refreshed all results for session {session_id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error in refresh_analysis_results: {e}")
        raise e

def save_full_analysis(db: Session, user_id: int, resume_text: str, jd_text: str, analysis_data: Dict, resume_pdf_path: str = None):
    """
    Saves a brand new analysis session with all related data.
    """
    try:
        # 1. Create Session
        db_session = models.AnalysisSession(
            user_id=user_id, 
            resume_text=resume_text, 
            jd_text=jd_text, 
            resume_pdf_path=resume_pdf_path, 
            timestamp=datetime.utcnow()
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)

        # 2. Save Output Scores
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

        # 3. Save Skills
        for skill in analysis_data.get("skill_matches", []):
            db.add(models.SkillMatch(
                session_id=db_session.id, 
                skill_name=skill['skill_name'], 
                status=skill['status']
            ))

        # 4. Save Jobs
        for job in analysis_data.get("job_listings", []):
            db.add(models.JobListing(
                session_id=db_session.id, 
                title=job.get('title'), 
                company=job.get('company'), 
                location=job.get('location'), 
                url=job.get('url')
            ))
        
        db.commit()
        print(f"✅ Saved new analysis session {db_session.id}")
        return db_session.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Save error: {e}")
        raise e