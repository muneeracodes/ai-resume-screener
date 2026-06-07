import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from dotenv import load_dotenv

# Import our Pydantic validation structures
from schema import ResumeScreeningReport
from langchain_groq import ChatGroq

load_dotenv()

app = FastAPI(title="AI Resume Screener API", version="1.0")

# Enable CORS so our React frontend can safely talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Groq LLM client using LLaMA 3.3
if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY is missing from environment variables.")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1, # Low temperature ensures analytical accuracy and less "hallucination"
)

# Bind the Pydantic schema to the model for structured JSON outputs
structured_llm = llm.with_structured_output(ResumeScreeningReport)

def extract_text_from_pdf(file: UploadFile) -> str:
    """Helper function to read binary PDF content and convert it to string."""
    try:
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {str(e)}")

@app.post("/api/screen", response_model=ResumeScreeningReport)
async def screen_resume(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):
    # Validate file type
    if not resume.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are currently supported.")
        
    # 1. Parse text from the uploaded file
    resume_text = extract_text_from_pdf(resume)
    if not resume_text:
        raise HTTPException(status_code=400, detail="The uploaded PDF seems to be empty or unscannable.")

    # 2. Construct the system and human prompt engineering layer
    system_prompt = (
        "You are an expert technical recruiter and Senior AI Talent Acquisition Specialist. "
        "Your task is to analyze the provided Resume text against the Job Description (JD). "
        "Perform a critical, objective, and strict evaluation. Calculate an accurate match score, "
        "extract matching and missing technical/soft keywords, and generate professional line-by-line "
        "rewrites using strong action verbs and quantified impact where applicable."
    )
    
    user_prompt = f"""
    === JOB DESCRIPTION ===
    {job_description}
    
    === APPLICANT RESUME ===
    {resume_text}
    """

    # 3. Invoke the structured AI intelligence layer
    try:
        messages = [
            ("system", system_prompt),
            ("human", user_prompt)
        ]
        # Invoking the model returns a direct instance of our ResumeScreeningReport Pydantic model
        analysis_report = structured_llm.invoke(messages)
        return analysis_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine analysis error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main.py", host="127.0.0.1", port=8000, reload=True)