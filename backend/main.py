
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
