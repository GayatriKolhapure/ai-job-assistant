import json
from pathlib import Path
from datetime import datetime


# Path to the application records file
DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "applications.json"
)


def load_applications():
    """Load saved application records."""
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Application data must be a JSON list.")

        return data

    except json.JSONDecodeError as error:
        raise ValueError(
            "applications.json contains invalid JSON."
        ) from error


def save_applications(applications):
    """Save application records to the JSON file."""
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            applications,
            file,
            indent=2,
            ensure_ascii=False
        )


def apply_for_job(job):
    """Record an application and prevent duplicate applications."""
    if not isinstance(job, dict):
        raise ValueError("Invalid job details.")

    job_id = job.get("job_id")

    if not job_id:
        raise ValueError("The selected job has no job ID.")

    applications = load_applications()

    # Prevent applying for the same job more than once.
    for application in applications:
        if application.get("job_id") == job_id:
            return {
                "success": False,
                "message": "You have already applied for this job.",
                "application": application
            }

    application = {
        "job_id": job_id,
        "title": job.get("title", "Unknown"),
        "company": job.get("company", "Unknown"),
        "application_date": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "status": "Recorded"
    }

    applications.append(application)
    save_applications(applications)

    return {
        "success": True,
        "message": "Your application has been recorded successfully.",
        "application": application
    }


def get_applications():
    """Return all recorded applications."""
    return load_applications()