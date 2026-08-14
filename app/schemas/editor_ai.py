# 写作助手 AI 请求 / 响应 Schema
from pydantic import BaseModel, Field


class TopicAnalyzeDTO(BaseModel):
    keyword: str = Field(min_length=1, max_length=64)


class TopicAngleVO(BaseModel):
    angle: str
    title: str
    hint: str = ""
    outline_md: str = ""


class TopicAnalyzeVO(BaseModel):
    insight: str
    angles: list[TopicAngleVO]


class ExpandDTO(BaseModel):
    title: str = ""
    content_md: str = ""


class ExpandVO(BaseModel):
    appendix_md: str


class SummaryDTO(BaseModel):
    title: str = ""
    content_md: str = ""


class TextCandidateVO(BaseModel):
    label: str
    text: str


class SummaryVO(BaseModel):
    candidates: list[TextCandidateVO]


class OpeningDTO(BaseModel):
    title: str = ""
    content_md: str = ""


class OpeningVO(BaseModel):
    candidates: list[TextCandidateVO]
