import requests
import urllib.parse
import json

SERPER_API_KEY = "YOUR_API_KEY_HERE"

TRUSTED_PLATFORMS = [
    "Coursera",
    "Udemy",
    "edX",
    "Pluralsight",
    "freeCodeCamp"
]

def find_courses_for_skill(skill, limit=3):
    """
    Finds REAL courses for a missing skill using Google Search (Serper).
    Falls back to trusted platforms if API fails.
    """

    if not skill or not skill.strip():
        return []

    skill_safe = urllib.parse.quote(skill)
    courses = []

    # -------- Strategy 1: Serper Search --------
    if SERPER_API_KEY:
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": f"best {skill} online course site:coursera.org OR site:udemy.com OR site:edx.org",
                "num": limit
            })

            headers = {
                "X-API-KEY": SERPER_API_KEY,
                "Content-Type": "application/json"
            }

            res = requests.post(url, headers=headers, data=payload)
            data = res.json()

            if "organic" in data:
                for item in data["organic"]:
                    courses.append({
                        "title": item.get("title", f"{skill} Course"),
                        "link": item.get("link"),
                        "snippet": item.get("snippet", "")
                    })
                    if len(courses) >= limit:
                        break

        except Exception as e:
            print(f"Course API error: {e}")

    # -------- Strategy 2: Fallback (Always works) --------
    if not courses:
        courses.extend([
            {
                "title": f"📘 Learn {skill} on Coursera",
                "link": f"https://www.coursera.org/search?query={skill_safe}",
                "snippet": "University-level courses and certificates."
            },
            {
                "title": f"🎓 Learn {skill} on Udemy",
                "link": f"https://www.udemy.com/courses/search/?q={skill_safe}",
                "snippet": "Hands-on practical courses."
            },
            # {
            #     "title": f"🆓 Learn {skill} on freeCodeCamp",
            #     "link": f"https://www.freecodecamp.org/news/search/?query={skill_safe}",
            #     "snippet": "Free tutorials and guides."
            # }
        ])

    return courses
