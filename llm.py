import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# FIX: Added matched_skills and missing_skills as arguments
def analyze_with_llm(resume_text, jd_text, matched_skills, missing_skills):
    # Prepare skills as strings for the prompt
    matched_str = ", ".join(matched_skills) if matched_skills else "None identified"
    missing_str = ", ".join(missing_skills) if missing_skills else "None identified"

    prompt = f"""
You are an AI Career Advisor and mentor.

You are speaking directly to a student who is preparing for their career. 
Your role is to help them understand how well their current profile fits the target job and how they can realistically improve.

IMPORTANT:
- Do NOT re-calculate or infer skills.
- Use the provided matched skills, missing skills, and weak areas as ground truth.
- Focus on explanation, guidance, and encouragement rather than listing skills mechanically.
- Keep the tone warm, supportive, and personalized — like a mentor reviewing their resume.

---

### 1. Your Key Strengths for This Role
Using the matched skills and experiences provided:
- Highlight 3–4 of the strongest alignments.
- Explain *why* each strength matters for this job.
- Frame them as “what you’re already doing right” and how they help you stand out.

Speak directly to the student (e.g., “One thing you’re doing well is…”).

---

### 2. Growth Areas to Focus On Next
Based on the missing and matched skills provided in {matched_str} and {missing_str}:
- Identify 3–4 important areas where growth would significantly improve their fit.
- Explain *why these gaps matter* for this role.
- Give practical, student-friendly suggestions such as:
- specific project ideas
- learning paths
- certifications or hands-on practice

make it in a point form list.Choose the important skills from the missing skills list.
Avoid generic advice — tailor suggestions to the student’s current level.
---

### 3. Resume Improvement & Skill Development Roadmap
Provide them with a roadmap to enhance their resume and skills over the next 3–4 months:
- Break it down into clear, actionable steps.
- Prioritize based on impact and feasibility for a student.

---

### 4. Career Role Alignment 
- Assess whether this job is a strong match for the student *at their current stage*.
- Be honest but encouraging.

If the alignment is weak:
- Suggest 1–2 alternative roles that better fit their current skills.
- Do NOT repeat the same job title as the JD.
- For each role:
  - Brief description
  - Why it may be a better stepping stone right now
Put the job suggestions in a point form list.
Frame alternatives as strategic options, not failures.

---

### Tone & Style Guidelines
- Speak directly to the student (“you”).
- Be encouraging, realistic, and specific.
- Avoid repeating skill names unnecessarily.
- Avoid sounding like an ATS or checklist.
- The goal is clarity, confidence, and a clear next plan.

---

Here is the data:

Resume Text: {resume_text}
Job Description: {jd_text}
"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are the CareerCraft Coach, a warm and supportive career mentor."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(GROQ_BASE_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ My apologies, I ran into a slight hiccup analyzing your profile: {e}"