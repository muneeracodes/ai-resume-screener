from pydantic import BaseModel, Field
from typing import List, Literal

class WeakSection(BaseModel):
    original: str = Field(description="The original weak text from the resume section.")
    rewrite: str = Field(description="The optimized text incorporating strong action metrics and keywords.")
    reason: str = Field(description="The analytical reason why this section was weak and needs improvement.")

class ResumeAnalysisResult(BaseModel):
    match_score: int = Field(description="An overall alignment score between 0 and 100.")
    score_rationale: str = Field(description="A brief paragraph justifying the assigned match score.")
    missing_keywords: List[str] = Field(description="Critical keywords or skills missing from the resume.")
    strengths: List[str] = Field(description="Key strengths and matching keywords found in the resume.")
    weak_sections: List[WeakSection] = Field(description="List of specific sections requiring optimization.")
    recommendation: Literal["strong_match", "moderate_match", "weak_match", "no_match"] = Field(
        description="Categorical recommendation based strictly on the match score."
    )