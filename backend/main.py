
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File, HTTPException
from services.resume_parser import parse_resume

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