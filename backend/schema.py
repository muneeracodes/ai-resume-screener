from pydantic import BaseModel, Field
from typing import List

class KeywordAnalysis(BaseModel):
    found_keywords: List[str] = Field(description="Important keywords from the job description that are present in the resume.")
    missing_keywords: List[str] = Field(description="Critical keywords or skills missing from the resume that are heavily weighted in the job description.")

class SectionRewrite(BaseModel):
    section_name: str = Field(description="The section of the resume to improve (e.g., Experience, Summary, Projects).")
    current_text: str = Field(description="The original weak text from the resume.")
    suggested_rewrite: str = Field(description="The optimized text incorporating missing metrics, action verbs, and matching keywords.")

class ResumeScreeningReport(BaseModel):
    match_score: int = Field(description="An overall semantic alignment score between 0 and 100 based on experience, skills, and depth.")
    justification: str = Field(description="A brief paragraph justifying the assigned match score.")
    keyword_analysis: KeywordAnalysis
    recommended_rewrites: List[SectionRewrite]