# 写作助手 AI 请求 / 响应 Schema
from pydantic import BaseModel, Field

# 与服务端截断策略对齐的正文上限
CONTENT_MD_MAX = 12000
TITLE_MAX = 200


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
    title: str = Field(default="", max_length=TITLE_MAX)
    content_md: str = Field(default="", max_length=CONTENT_MD_MAX)


class ExpandVO(BaseModel):
    appendix_md: str


class SummaryDTO(BaseModel):
    title: str = Field(default="", max_length=TITLE_MAX)
    content_md: str = Field(default="", max_length=CONTENT_MD_MAX)


class TextCandidateVO(BaseModel):
    label: str
    text: str


class SummaryVO(BaseModel):
    candidates: list[TextCandidateVO]


class OpeningDTO(BaseModel):
    title: str = Field(default="", max_length=TITLE_MAX)
    content_md: str = Field(default="", max_length=CONTENT_MD_MAX)


class OpeningVO(BaseModel):
    candidates: list[TextCandidateVO]
