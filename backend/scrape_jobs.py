import json
import re
import time
from pathlib import Path

import requests


API_URL = "https://himalayas.app/jobs/api"

OUTPUT_FILE = Path(__file__).parent / "data" / "jobs.json"

TARGET_JOBS = 2000
PAGE_SIZE = 20

HEADERS = {
    "User-Agent": "AIJobChatAssistant/1.0"
}

KNOWN_SKILLS = [
    "Java",
    "Python",
    "JavaScript",
    "TypeScript",
    "Spring Boot",
    "Spring",
    "React",
    "React.js",
    "Node.js",
    "HTML",
    "CSS",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "MongoDB",
    "REST API",
    "Docker",
    "AWS",
    "Azure",
    "Git",
    "GitHub",
    "Machine Learning",
    "Artificial Intelligence",
    "Data Analysis",
    "FastAPI",
    "Django",
    "Flask",
    "C++",
    "C#",
    "Go",
    "Ruby",
    "PHP",
    "Kotlin",
    "Swift"
]


def remove_html(text):
    """Remove HTML tags from job descriptions."""

    text = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        text or "",
        flags=re.IGNORECASE | re.DOTALL
    )

    text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_skills(text, categories):
    """Extract recognizable technical skills from job information."""

    searchable_text = (
        (text or "") + " " + " ".join(categories or [])
    ).lower()

    skills = []

    for skill in KNOWN_SKILLS:
        pattern = (
            r"(?<![a-z0-9+#.])"
            + re.escape(skill.lower())
            + r"(?![a-z0-9+#.])"
        )

        if re.search(pattern, searchable_text):
            skills.append(skill)

    return skills


def normalize_job(job):
    """Convert an API job into the required JSON structure."""

    description = remove_html(
        job.get("description") or job.get("excerpt") or ""
    )

    categories = job.get("categories") or []
    if isinstance(categories, str):
        categories = [categories]

    job_id = job.get("guid") or job.get("id")

    title = job.get("title")
    company = job.get("companyName") or job.get("company_name")

    if not job_id or not title or not company:
        return None

    return {
        "job_id": str(job_id),
        "title": title.strip(),
        "company": company.strip(),
        "location": ", ".join(job.get("locationRestrictions") or [])
        or "Remote; check listing for location restrictions",
        "experience_required": "Not specified by source",
        "skills": extract_skills(description, categories),
        "description": description,
        "source": "Himalayas",
        "source_link": job.get("applicationLink")
        or job.get("url")
        or "",
        "employment_type": job.get("employmentType") or "Not specified",
        "categories": categories
    }


def fetch_jobs():
    """Fetch real job listings using cursor-based pagination."""

    jobs_by_id = {}
    cursor = None

    while len(jobs_by_id) < TARGET_JOBS:
        params = {"limit": PAGE_SIZE}

        if cursor:
            params["cursor"] = cursor

        print(f"Fetching jobs... Collected: {len(jobs_by_id)}")

        try:
            response = requests.get(
                API_URL,
                params=params,
                headers=HEADERS,
                timeout=30
            )

            if response.status_code == 429:
                print("Rate limit reached. Waiting before retrying.")
                time.sleep(10)
                continue

            response.raise_for_status()
            payload = response.json()

        except requests.RequestException as error:
            print(f"Request failed: {error}")
            break

        except ValueError:
            print("The API returned invalid JSON.")
            break

        batch = payload.get("jobs", [])

        # Support a data-list response if the API response format changes.
        if not batch:
            batch = payload.get("data", [])

        if not batch:
            print("No more jobs returned by the API.")
            break

        for raw_job in batch:
            normalized = normalize_job(raw_job)

            if normalized:
                jobs_by_id[normalized["job_id"]] = normalized

                if len(jobs_by_id) >= TARGET_JOBS:
                    break

        next_cursor = payload.get("nextCursor")

        if not next_cursor:
            print("No next cursor returned. Reached the end of the feed.")
            break

        if next_cursor == cursor:
            print("The API returned the same cursor. Stopping safely.")
            break

        cursor = next_cursor

        # Avoid sending requests too quickly.
        time.sleep(1)

    return list(jobs_by_id.values())


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    jobs = fetch_jobs()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2, ensure_ascii=False)

    print("\nJob collection completed.")
    print(f"Unique jobs saved: {len(jobs)}")
    print(f"Output file: {OUTPUT_FILE}")

    if len(jobs) < 1500:
        print(
            "\nWARNING: Fewer than 1,500 jobs were collected. "
            "We need another permitted source to meet the assessment."
        )
    elif len(jobs) < TARGET_JOBS:
        print(
            "\nThe dataset contains at least 1,500 jobs, "
            "but fewer than the target of 2,000."
        )
    else:
        print("Target of 2,000 jobs reached.")


if __name__ == "__main__":
    main()