import re
import json
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# ----------------------------------------------------
# STEP 1 — Load the model first
# ----------------------------------------------------
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

model = load_model()

# ----------------------------------------------------
# STEP 2 — Load skills database
# ----------------------------------------------------
@st.cache_data
def load_skill_db():
    #r mean read mode
    with open("skills.json", "r") as f:
        skill_db = json.load(f)
    all_skills = set(skill.lower() for cat in skill_db.values() for skill in cat)
    return all_skills

ALL_SKILLS = load_skill_db()

# ----------------------------------------------------
# STEP 3 — Generate embeddings for all known skills
# ----------------------------------------------------
@st.cache_resource
def get_skill_embeddings():
    skills = list(ALL_SKILLS)
    embeddings = model.encode(skills, convert_to_tensor=True)
    return skills, embeddings

ALL_SKILL_LIST, ALL_SKILL_EMB = get_skill_embeddings()

# ----------------------------------------------------
# STEP 4 — Helper text cleaning functions
# ----------------------------------------------------
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    return text

def clean_tokens(text):
    tokens = re.findall(r'\b[a-zA-Z0-9\-\+\.\#]+\b', text.lower())
    return list(set(tokens))

# ----------------------------------------------------
# STEP 5 — Semantic skill extraction for resume
# ----------------------------------------------------
def get_resume_details(resume_text):
    clean_text = normalize_text(resume_text)
    tokens = clean_tokens(clean_text)
    found_skills = set()

    for token in tokens:
        token_emb = model.encode(token, convert_to_tensor=True)
        cos_scores = util.cos_sim(token_emb, ALL_SKILL_EMB)
        max_idx = cos_scores.argmax().item()
        if cos_scores[0][max_idx] > 0.75:
            found_skills.add(ALL_SKILL_LIST[max_idx])

    return {"skills": list(found_skills), "raw_text": clean_text}

# ----------------------------------------------------
# STEP 6 — Extract skills from JD
# ----------------------------------------------------
def extract_skills_from_jd(jd_text):
    jd_clean = normalize_text(jd_text)
    tokens = clean_tokens(jd_clean)
    found_skills = set()

    for token in tokens:
        token_emb = model.encode(token, convert_to_tensor=True)
        cos_scores = util.cos_sim(token_emb, ALL_SKILL_EMB)
        max_idx = cos_scores.argmax().item()
        
        if cos_scores[0][max_idx] > 0.75:
            found_skills.add(ALL_SKILL_LIST[max_idx])

    return found_skills

# ----------------------------------------------------
# STEP 7 — Compare resume and JD
# ----------------------------------------------------
def compare_resume_with_jd(resume_details, jd_text):
    jd_skills = extract_skills_from_jd(jd_text)
    # we are not calling function directly bcz we need skills only 
    # the function is extracting other stuff also for llm analysis
    resume_skills = resume_details["skills"]

    if not jd_skills or not resume_skills:
        return {
            "matched_skills": [],
            "missing_skills": list(jd_skills),
            "keyword_similarity": 0
        }

    # Generate embeddings
    resume_embeddings = model.encode(list(resume_skills), convert_to_tensor=True)
    jd_embeddings = model.encode(list(jd_skills), convert_to_tensor=True)

    # Cosine similarity
    cos_scores = util.cos_sim(jd_embeddings, resume_embeddings)

    matched_skills = []
    for i, jd_skill in enumerate(jd_skills):
        if max(cos_scores[i]) > 0.75:
            matched_skills.append(jd_skill)

    missing_skills = list(jd_skills - set(matched_skills))

    # TF-IDF similarity for overall keyword overlap
    tfidf = TfidfVectorizer()
    vectors = tfidf.fit_transform([resume_details["raw_text"], jd_text])
    keyword_sim = cosine_similarity(vectors[0], vectors[1])[0][0]

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "keyword_similarity": round(keyword_sim * 100, 2)
    }

# ----------------------------------------------------
# STEP 8 — Final score calculation
# ----------------------------------------------------
def get_final_score_and_suggestions(analysis):
    skill_score = (
        len(analysis["matched_skills"]) /
        (len(analysis["matched_skills"]) + len(analysis["missing_skills"])) * 70
    ) if analysis["matched_skills"] else 0

    keyword_score = (analysis["keyword_similarity"] / 100) * 30
    final_score = round(skill_score + keyword_score, 2)

    return final_score, round(keyword_score, 2),round(skill_score, 2)