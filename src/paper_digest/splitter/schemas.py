from pydantic import BaseModel


class SubjectDependency(BaseModel):
    name: str
    requires: list[str]


class SubjectSplitterResponse(BaseModel):
    subjects: list[SubjectDependency]


class PaperAnalysisResponse(BaseModel):
    new_subject: str
    direct_subjects: list[str]
    subjects: list[SubjectDependency]
