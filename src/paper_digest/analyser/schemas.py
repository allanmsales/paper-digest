from pydantic import BaseModel, HttpUrl


class PaperAnalysisRequest(BaseModel):
    paper_url: HttpUrl


class PaperAnalyzerResponse(BaseModel):
    new_subject: str
    direct_subjects: list[str]
