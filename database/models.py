# database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base 

# 1. NEW: USERS TABLE
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    password = Column(String) # In production, hash this! For FYP, simple string is fine.
    
    sessions = relationship("AnalysisSession", back_populates="user")

# 2. UPDATE: Link AnalysisSession to User
class AnalysisSession(Base):
    __tablename__ = 'analysis_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id')) # Link to real user
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    resume_text = Column(Text, nullable=False)
    jd_text = Column(Text, nullable=False)
    resume_pdf_path = Column(String, nullable=True)

    user = relationship("User", back_populates="sessions") # Relationship
    
    output = relationship("LLMOutput", back_populates="session", uselist=False, cascade="all, delete-orphan")
    skills = relationship("SkillMatch", back_populates="session", cascade="all, delete-orphan")
    jobs = relationship("JobListing", back_populates="session", cascade="all, delete-orphan")

# ... (Keep LLMOutput, SkillMatch, JobListing exactly as they were) ...
class LLMOutput(Base):
    __tablename__ = 'llm_outputs'
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'), primary_key=True)
    fit_score = Column(Float)
    keyword_match = Column(Float)
    skill_match = Column(Float)
    full_suggestion_text = Column(Text)
    best_suited_job = Column(String)
    suggested_location = Column(String)
    session = relationship("AnalysisSession", back_populates="output")

class SkillMatch(Base):
    __tablename__ = 'skill_matches'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'))
    skill_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    session = relationship("AnalysisSession", back_populates="skills")

class JobListing(Base):
    __tablename__ = 'job_listings'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'))
    title = Column(String)
    company = Column(String)
    location = Column(String)
    posting_date = Column(DateTime)
    url = Column(String)
    session = relationship("AnalysisSession", back_populates="jobs")