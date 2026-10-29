from services.job_matcher import match_jobs
from services.application_service import apply_for_job


def process_message(message, resume=None):
    """
    Coordinate user requests for the AI Job Chat Assistant.
    """

    if not message or not message.strip():
        return {
            "message": "Please tell me what kind of job you are looking for.",
            "recommendations": []
        }

    user_message = message.strip()
    message_lower = user_message.lower()

    # Check whether the user has uploaded a resume.
    if resume is None:
        return {
            "message": (
                "Please upload your PDF or DOCX resume first. "
                "Then I can recommend jobs based on your profile."
            ),
            "recommendations": []
        }

    # Handle job application requests.
    if any(word in message_lower for word in ["apply", "application", "submit my application"]):
        try:
            from services.job_matcher import load_jobs

            jobs = match_jobs(resume, limit=10)

            if not jobs:
                return {
                    "message": "No matching jobs found. Please find a suitable job before applying.",
                    "recommendations": []
                }

            # Check whether the user specified a job ID.
            selected_job = next(
                (
                    job for job in jobs
                    if str(job.get("job_id", "")) in user_message
                ),
                None
            )

            # If no job ID was provided, ask the user to select a job.
            if selected_job is None:
                return {
                    "message": (
                        "Please select a job from the recommendations "
                        "and provide its job ID so I can record your application."
                    ),
                    "total": len(jobs),
                    "recommendations": jobs
                }

            result = apply_for_job(selected_job)

            return {
                "message": result["message"],
                "total": 1 if result["success"] else 0,
                "recommendations": [selected_job],
                "application": result.get("application")
            }

        except (FileNotFoundError, ValueError):
            return {
                "message": "Unable to record your application. Please try again.",
                "recommendations": []
            }

    # Generate job recommendations.
    try:
        recommendations = match_jobs(resume, limit=10)

        if not recommendations:
            return {
                "message": (
                    "I couldn't find matching jobs. "
                    "Try updating your resume or job preferences."
                ),
                "recommendations": []
            }

        # Refine results using a location preference.
        if "remote" in message_lower:
            recommendations = [
                job for job in recommendations
                if "remote" in str(job.get("location", "")).lower()
                or "remote" in str(job.get("title", "")).lower()
                or "remote" in str(job.get("description", "")).lower()
            ]

        # Refine results using a skill mentioned in the request.
        requested_skills = [
            skill
            for skill in [
                "java",
                "spring boot",
                "python",
                "javascript",
                "react",
                "sql",
                "mysql"
            ]
            if skill in message_lower
        ]

        if requested_skills:
            recommendations = [
                job for job in recommendations
                if any(
                    skill in " ".join(
                        str(item) for item in job.get("skills", [])
                    ).lower()
                    or skill in str(job.get("title", "")).lower()
                    or skill in str(job.get("description", "")).lower()
                    for skill in requested_skills
                )
            ]

        if not recommendations:
            return {
                "message": (
                    "No jobs matched those preferences. "
                    "Try another skill or remove the remote preference."
                ),
                "recommendations": []
            }

        return {
            "message": (
                f"I found {len(recommendations)} jobs "
                "that match your profile and preferences."
            ),
            "total": len(recommendations),
            "recommendations": recommendations
        }

    except (FileNotFoundError, ValueError):
        return {
            "message": (
                "I couldn't access the job database. "
                "Please check the job listings file."
            ),
            "recommendations": []
        }