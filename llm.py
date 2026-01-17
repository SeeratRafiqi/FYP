import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("🚨 ERROR: GROQ_API_KEY is not loaded or is empty.")
    # You might want to exit or raise an error here
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

def analyze_with_llm(resume_text, jd_text):
    prompt = f"""

You are an AI Career Advisor. I will provide you with:
1. A student's resume
2. A job description (JD)

Your task is to carefully analyze the resume against the JD and return a structured evaluation with the following sections: Write your response in a way as if you are directly talking to the person whose resume is being evaluated.

### 1. Key Strengths
- List 3–4 strong skills, experiences, or achievements from the resume that directly match the JD.
- Explain why they are valuable for this role.



### 3. Areas to Improve
- Identify 3–4 skills or experiences that the student should improve or gain.
- Provide practical suggestions (e.g., courses, projects, certifications).

### 4. Resume Improvement & Skill Development. Display it in a table format.
For each missing or weak skill (choose 3–4 critical ones):
* Skill/Experience: [Name]
* Importance for this Job: [CRITICAL / IMPORTANT / NICE-TO-HAVE]

and also provide courses for the missing skills ,with links from sites like coursera, edx, udemy only. Return only the course title and the platform name (e.g., Coursera, Udemy). Do not invent URLs."

### 3. Career Role Alignment
- Check if the student’s resume aligns well with the Job they are going for
- If not, suggest 1–2 alternative job roles that align better with their skills.
- For each suggested role, give a short description and why it could be a better match.But dont repeat the same job title as in the jd.

Keep your tone supportive, clear, and practical. Avoid generic advice — make suggestions personalized to the provided resume and JD


Here is the data:
Resume: {resume_text}
Job Description: {jd_text}
"""


    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are an expert in resume evaluation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4
    }
    print("🔍 Debug: Sending request to Groq API...")
    # print("🔍 Debug: GROQ_API_KEY loaded:", bool(GROQ_API_KEY))
    # print("🔍 Debug: Headers being sent:", HEADERS)
    # print("🔍 Debug: Payload being sent:", payload)

    try:
        response = requests.post(GROQ_BASE_URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        result = response.json()
        # print("✅ Success: Response received.")
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as http_err:
        # print("❌ HTTPError:", response.text)
        return f"⚠️ LLM evaluation failed: {http_err}"
    except Exception as e:
        # print("❌ General Exception:", str(e))
        return f"⚠️ LLM evaluation failed: {e}"
# analyze_with_llm("sghagdh","jgdhd")
