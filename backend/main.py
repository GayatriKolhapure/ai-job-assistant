
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, HTTPException
from services.resume_parser import parse_resume
from fastapi import Body
from services.job_matcher import match_jobs
from agents.orchestrator import process_message
from services.application_service import apply_for_job, get_applications


# Create the FastAPI application
app = FastAPI(
    title="AI Job Chat Assistant",
    description="An AI-powered assistant for resume parsing and job recommendations.",
    version="1.0.0"
)

# Allow the React frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your frontend URL before production
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Welcome endpoint
@app.get("/")
def home():
    return {
        "message": "Welcome to the AI Job Chat Assistant!",
        "status": "Backend is running successfully"
    }


# Health-check endpoint
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "AI Job Chat Assistant"
    }


@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Please select a resume file."
            )

        if not file.filename.lower().endswith((".pdf", ".docx")):
            raise HTTPException(
                status_code=400,
                detail="Only PDF and DOCX files are supported."
            )

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty."
            )

        resume_data = parse_resume(file_bytes, file.filename)

        return {
            "message": "Resume uploaded and parsed successfully!",
            "resume": resume_data
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process this resume. Please try another file."
        )

    finally:
        await file.close()



@app.post("/api/jobs/recommend")
def recommend_jobs(resume: dict = Body(...)):
    try:
        if not resume.get("skills") and not resume.get("designation"):
            raise HTTPException(
                status_code=400,
                detail="Resume must contain skills or a designation."
            )

        recommendations = match_jobs(resume)

        if not recommendations:
            return {
                "message": "No matching jobs found. Try updating your resume.",
                "total": 0,
                "recommendations": []
            }

        return {
            "message": "Job recommendations generated successfully.",
            "total": len(recommendations),
            "recommendations": recommendations
        }

    except HTTPException:
        raise

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate job recommendations."
        )



@app.post("/api/chat")
def chat(message: str = Body(...), resume: dict = Body(...)):
    try:
        if not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Please enter a message."
            )

        result = process_message(message, resume)

        return {
            "message": result.get("message", ""),
            "total": result.get("total", 0),
            "recommendations": result.get("recommendations", [])
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to process your message."
        )

@app.post("/api/applications")
def apply_to_job(job_id: str):
    from services.job_matcher import load_jobs

    try:
        jobs = load_jobs()

        selected_job = next(
            (job for job in jobs if str(job.get("job_id")) == job_id),
            None
        )

        if selected_job is None:
            raise HTTPException(status_code=404, detail="Job not found.")

        result = apply_for_job(selected_job)

        if not result["success"]:
            raise HTTPException(status_code=409, detail=result["message"])

        return result

    except HTTPException:
        raise
    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Unable to record the application."
        )

@app.get("/api/applications")
def list_applications():
    try:
        applications = get_applications()

        return {
            "total": len(applications),
            "applications": applications
        }

    except (FileNotFoundError, ValueError):
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve application records."
        )