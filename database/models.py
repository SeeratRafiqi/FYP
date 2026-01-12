# # database/models.py
# from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from .connection import Base 



# # Note: We are simplifying the USERS table for now since you don't have login/auth yet.

# # 1. ANALYSIS_SESSION Table (The central log of every run)
# class AnalysisSession(Base):
#     __tablename__ = 'analysis_sessions'
#     id = Column(Integer, primary_key=True, index=True)
#     # Placeholder for a user ID if you implement login later
#     user_id = Column(Integer, default=1) 
#     timestamp = Column(DateTime, default=datetime.utcnow)
    
#     # Store the input text for history cases
#     resume_text = Column(Text, nullable=False)
#     jd_text = Column(Text, nullable=False)
#     resume_pdf_path = Column(String, nullable=True)

    
#     # Relationships to output tables
#     output = relationship("LLMOutput", back_populates="session", uselist=False, cascade="all, delete-orphan")
#     skills = relationship("SkillMatch", back_populates="session", cascade="all, delete-orphan")
#     jobs = relationship("JobListing", back_populates="session", cascade="all, delete-orphan")

# # 2. LLM_OUTPUTS Table (The single-go output)
# class LLMOutput(Base):
#     __tablename__ = 'llm_outputs'
#     session_id = Column(Integer, ForeignKey('analysis_sessions.id'), primary_key=True)
#     fit_score = Column(Float)
#     full_suggestion_text = Column(Text)
#     best_suited_job = Column(String)
#     suggested_location = Column(String)
    
#     session = relationship("AnalysisSession", back_populates="output")

# # 3. SKILL_MATCHES Table (Structured skill data)
# class SkillMatch(Base):
#     __tablename__ = 'skill_matches'
#     id = Column(Integer, primary_key=True)
#     session_id = Column(Integer, ForeignKey('analysis_sessions.id'))
#     skill_name = Column(String, nullable=False)
#     status = Column(String, nullable=False) # 'MATCHED', 'MISSING'
    
#     session = relationship("AnalysisSession", back_populates="skills")

# # 4. JOB_LISTINGS Table (The initial job postings)
# class JobListing(Base):
#     __tablename__ = 'job_listings'
#     id = Column(Integer, primary_key=True)
#     session_id = Column(Integer, ForeignKey('analysis_sessions.id'))
#     title = Column(String)
#     company = Column(String)
#     location = Column(String)
#     posting_date = Column(DateTime)
#     url = Column(String)

#     session = relationship("AnalysisSession", back_populates="jobs")


# database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .connection import Base 

class AnalysisSession(Base):
    __tablename__ = 'analysis_sessions'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, default=1) 
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    resume_text = Column(Text, nullable=False)
    jd_text = Column(Text, nullable=False)
    resume_pdf_path = Column(String, nullable=True)
    
    output = relationship("LLMOutput", back_populates="session", uselist=False, cascade="all, delete-orphan")
    skills = relationship("SkillMatch", back_populates="session", cascade="all, delete-orphan")
    jobs = relationship("JobListing", back_populates="session", cascade="all, delete-orphan")

class LLMOutput(Base):
    __tablename__ = 'llm_outputs'
    session_id = Column(Integer, ForeignKey('analysis_sessions.id'), primary_key=True)
    
    fit_score = Column(Float)
    keyword_match = Column(Float)  # ✅ Added
    skill_match = Column(Float)    # ✅ Added
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