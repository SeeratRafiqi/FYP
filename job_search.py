import requests
import urllib.parse

# --- CONFIGURATION ---
# 1. Sign up at https://serper.dev (Free)
# 2. Paste your API Key here:
SERPER_API_KEY = "f80d4f4c103f7a49b48318211f21d9141c68b784" 

def find_jobs_realtime(role, location="Malaysia", limit=5):
    """
    Searches for jobs using Google Jobs API (Serper).
    Fallback: Generates direct portal links if API fails.
    """
    if not role or not role.strip():
        return []

    # Clean the role for URLs
    role_safe = urllib.parse.quote(role)
    location_safe = urllib.parse.quote(location)
    
    jobs = []

    # --- STRATEGY 1: Serper.dev API (The Professional Way) ---
    if SERPER_API_KEY and "PASTE_YOUR_API_KEY_HERE" not in SERPER_API_KEY:
        try:
            url = "https://google.serper.dev/search"
            payload = json.dumps({
                "q": f"{role} jobs in {location}",
                "location": location,
                "num": limit
            })
            headers = {
                'X-API-KEY': SERPER_API_KEY,
                'Content-Type': 'application/json'
            }

            response = requests.post(url, headers=headers, data=payload)
            data = response.json()
            
            # Check if 'organic' results exist
            if "organic" in data:
                for item in data["organic"]:
                    jobs.append({
                        "title": item.get("title", "Job Opening"),
                        "link": item.get("link", "#"),
                        "snippet": item.get("snippet", f"Click to view details for {role}...")
                    })
                    if len(jobs) >= limit:
                        break
        except Exception as e:
            print(f"Serper API Error: {e}")
            # If API fails, we drop down to Strategy 2
            pass

    # --- STRATEGY 2: Smart Links (The "Unbreakable" Fallback) ---
    # If API returns nothing (or no key provided), generate direct links to portals.
    # This ensures the user ALWAYS sees something useful.
    if not jobs:
        print("Using Fallback Portal Links")
        
        # JobStreet Link
        jobs.append({
            "title": f"🔎 Search '{role}' on JobStreet Malaysia",
            "link": f"https://www.jobstreet.com.my/en/job-search/{role_safe}-jobs/",
            "snippet": f"Click here to view all live active listings for {role} directly on JobStreet."
        })

        # LinkedIn Link
        jobs.append({
            "title": f"🔎 Search '{role}' on LinkedIn Jobs",
            "link": f"https://www.linkedin.com/jobs/search?keywords={role_safe}&location={location_safe}",
            "snippet": "View professional network listings and easy-apply opportunities."
        })
        
        # Indeed Link
        jobs.append({
            "title": f"🔎 Search '{role}' on Indeed Malaysia",
            "link": f"https://malaysia.indeed.com/jobs?q={role_safe}&l={location_safe}",
            "snippet": "Browse aggregated job postings from various company career pages."
        })

    return jobs

import json # Helper import for the API