
import json
import re
from pathlib import Path


JOBS_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "jobs.json"
)


def load_jobs():
    """Load job listings from the JSON database."""

    if not JOBS_FILE.exists():
        raise FileNotFoundError("Job database not found.")

    with JOBS_FILE.open("r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Job database must contain a JSON list.")

    return jobs


def normalize(value):
    """Normalize text for comparison."""

    if not value:
        return ""

    return re.sub(r"\s+", " ", str(value).lower()).strip()


def extract_experience_years(text):
    """Extract explicitly stated experience requirements."""

    text = normalize(text)

    patterns = [
        r"\b(\d{1,2})\s*\+\s*years?\b",
        r"\b(\d{1,2})\s*-\s*\d{1,2}\s*years?\b",
        r"\b(\d{1,2})\s*years?\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return int(match.group(1))

    return None


def is_fresher(resume):
    """Identify candidates applying as freshers."""

    experience = normalize(resume.get("experience"))
    designation = normalize(resume.get("designation"))

    fresher_keywords = [
        "fresher",
        "student",
        "no experience",
        "entry level",
        "entry-level",
        "recent graduate",
        "graduate",
        "internship experience mentioned",
    ]

    return (
        any(word in experience for word in fresher_keywords)
        or any(
            word in designation
            for word in ["intern", "trainee"]
        )
    )


def is_software_job(job):
    """Exclude jobs unrelated to software development."""

    title = normalize(job.get("title"))

    software_keywords = [
        "software developer",
        "software engineer",
        "software development",
        "java developer",
        "python developer",
        "backend developer",
        "back-end developer",
        "frontend developer",
        "front-end developer",
        "full stack developer",
        "full-stack developer",
        "fullstack developer",
        "web developer",
        "application developer",
        "mobile developer",
        "android developer",
        "ios developer",
        "react developer",
        "node.js developer",
        "nodejs developer",
        "spring boot developer",
        "platform engineer",
        "devops engineer",
        "cloud engineer",
        "site reliability engineer",
        "sre ",
        "qa engineer",
        "quality assurance engineer",
        "automation tester",
        "test automation engineer",
        "software tester",
        "software architect",
        "embedded software engineer",
        "firmware engineer",
    ]

    return any(keyword in title for keyword in software_keywords)


def is_senior_job(title):
    """Identify clearly senior or leadership positions."""

    senior_keywords = [
        "senior",
        "staff",
        "team lead",
        "team leader",
        "engineering lead",
        "technical lead",
        "tech lead",
        "manager",
        "director",
        "principal",
        "head of ",
        "chief "
    ]

    return any(keyword in title for keyword in senior_keywords)


def match_jobs(resume, limit=10):
    """
    Recommend relevant software jobs using skills,
    designation, and experience suitability.
    """

    jobs = load_jobs()

    candidate_designation = normalize(
        resume.get("designation")
    )

    candidate_skills = {
        normalize(skill)
        for skill in resume.get("skills", [])
        if skill
    }

    candidate_is_fresher = is_fresher(resume)

    recommendations = []

    # Generic words that should not determine job relevance.
    ignored_designation_words = {
        "software",
        "developer",
        "engineer",
        "intern",
        "trainee",
        "junior",
        "entry",
        "level",
    }

    designation_words = {
        word
        for word in re.findall(
            r"[a-z0-9+#.]+",
            candidate_designation
        )
        if len(word) > 2
        and word not in ignored_designation_words
    }

    for job in jobs:
        job_title = normalize(job.get("title"))
        job_description = normalize(job.get("description"))

        if not job_title:
            continue

        # First, exclude unrelated career fields.
        if not is_software_job(job):
            continue

        # Exclude clearly senior roles for freshers.
        if candidate_is_fresher and is_senior_job(job_title):
            continue

        experience_required = normalize(
            job.get("experience_required")
        )

        # Check explicit experience requirements.
        if candidate_is_fresher:
            experience_text = (
                experience_required + " " + job_description
            )

            required_years = extract_experience_years(
                experience_text
            )

            if required_years is not None and required_years >= 3:
                continue

        job_skills = {
            normalize(skill)
            for skill in job.get("skills", [])
            if skill
        }

        matched_skills = candidate_skills.intersection(
            job_skills
        )

        job_text = job_title + " " + job_description

        matching_designation_words = [
            word
            for word in designation_words
            if word in job_title
        ]

        # A relevant software title is required.
        # Matching generic skills alone is not sufficient.
        if not is_software_job(job):
            continue

        # Calculate a score using skill matches.
        score = 0
        reasons = []

        if candidate_skills:
            skill_score = (
                len(matched_skills)
                / len(candidate_skills)
            ) * 60

            score += skill_score

        if matched_skills:
            reasons.append(
                "Matching skills: "
                + ", ".join(sorted(matched_skills))
            )

        if matching_designation_words:
            score += 25

            reasons.append(
                "The job title matches your designation: "
                + str(resume.get("designation", ""))
            )

        # Prefer entry-level roles for fresher candidates.
        entry_level_keywords = [
            "intern",
            "internship",
            "trainee",
            "junior",
            "entry level",
            "entry-level",
            "graduate",
            "associate developer",
        ]

        if candidate_is_fresher and any(
            keyword in job_title
            for keyword in entry_level_keywords
        ):
            score += 15

            reasons.append(
                "The position is identified as an entry-level role."
            )

        # Only include jobs with a meaningful match.
        if not matched_skills and not matching_designation_words:
            continue

        if score < 15:
            continue

        recommendations.append({
            "job_id": job.get("job_id"),
            "title": job.get("title", "Unknown title"),
            "company": job.get("company", "Unknown company"),
            "location": job.get("location", "Not specified"),
            "experience_required": job.get(
                "experience_required",
                "Not specified by source"
            ),
            "skills": job.get("skills", []),
            "description": job.get("description", ""),
            "source_link": job.get("source_link", ""),
            "match_score": round(min(score, 100), 2),
            "match_reasons": reasons,
        })

    recommendations.sort(
        key=lambda job: job["match_score"],
        reverse=True
    )

    return recommendations[:max(0, limit)]