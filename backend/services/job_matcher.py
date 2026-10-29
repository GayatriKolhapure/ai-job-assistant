import json
import re
from pathlib import Path


JOBS_FILE = Path(__file__).resolve().parent.parent / "data" / "jobs.json"


def load_jobs():
    """Load job listings from the JSON database."""

    if not JOBS_FILE.exists():
        raise FileNotFoundError("Job database not found.")

    with open(JOBS_FILE, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Job database must contain a JSON list.")

    return jobs


def normalize(value):
    """Convert text into a consistent format for comparison."""

    if not value:
        return ""

    return re.sub(r"\s+", " ", str(value).lower()).strip()


def match_jobs(resume, limit=10):
    """Recommend suitable jobs using skills, designation, and experience."""

    jobs = load_jobs()

    candidate_designation = normalize(resume.get("designation"))
    candidate_skills = {
        normalize(skill)
        for skill in resume.get("skills", [])
        if skill
    }
    candidate_experience = normalize(resume.get("experience"))

    candidate_is_fresher = any(
        word in candidate_experience
        for word in ["fresher", "student", "no experience", "entry level"]
    )

    recommendations = []

    senior_keywords = [
        "senior",
        "team lead",
        "team leader",
        "manager",
        "director",
        "principal",
        "staff engineer"
    ]

    for job in jobs:
        job_title = normalize(job.get("title"))
        job_description = normalize(job.get("description"))
        job_text = f"{job_title} {job_description}"

        job_skills = {
            normalize(skill)
            for skill in job.get("skills", [])
            if skill
        }

        experience_required = normalize(
            job.get("experience_required")
        )

        # Avoid clearly senior roles for fresher candidates.
        if candidate_is_fresher:
            # Exclude clearly senior job titles.
            if any(keyword in job_title for keyword in senior_keywords):
                continue

            # Check both the structured field and job description.
            experience_text = (
                experience_required + " " + job_description
            )

            if re.search(
                r"\b(?:[5-9]|[1-9]\d)\+?\s*years?\b",
                experience_text
            ):
                continue

        score = 0
        reasons = []

        # 1. Match skills.
        matched_skills = candidate_skills.intersection(job_skills)

        if candidate_skills:
            score += (
                len(matched_skills) / len(candidate_skills)
            ) * 60

            if matched_skills:
                reasons.append(
                    "Matching skills: "
                    + ", ".join(sorted(matched_skills))
                )

        # 2. Match designation.
        if candidate_designation:
            designation_words = {
                word
                for word in candidate_designation.split()
                if len(word) > 2
            }

            matching_words = [
                word
                for word in designation_words
                if word in job_text
            ]

            if matching_words:
                score += 25
                reasons.append(
                    "The job title or description matches your designation: "
                    + str(resume.get("designation", ""))
                )

        # 3. Give a bonus when the experience requirement suits a fresher.
        if candidate_is_fresher and experience_required:
            if any(
                word in experience_required
                for word in [
                    "entry level",
                    "entry-level",
                    "fresher",
                    "no experience",
                    "0 years",
                    "0-1 years",
                    "0–1 years"
                ]
            ):
                score += 15
                reasons.append(
                    "The experience requirement may suit a fresher."
                )

        # Only recommend jobs with at least one matching reason.
        if reasons:
            recommendations.append({
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "experience_required": job.get(
                    "experience_required",
                    "Not specified by source"
                ),
                "skills": job.get("skills", []),
                "description": job.get("description", ""),
                "source_link": job.get("source_link", ""),
                "match_score": round(min(score, 100), 2),
                "match_reasons": reasons
            })

    recommendations.sort(
        key=lambda job: job["match_score"],
        reverse=True
    )

    return recommendations[:max(0, limit)]
