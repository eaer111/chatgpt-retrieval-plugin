from models.models import (
    Document,
    DocumentChunkWithScore,
    DocumentMetadataFilter,
    Query,
    QueryResult,
)
from pydantic import BaseModel
from typing import List, Optional


class UpsertRequest(BaseModel):
    documents: List[Document]


class UpsertResponse(BaseModel):
    ids: List[str]


class QueryRequest(BaseModel):
    queries: List[Query]


class QueryResponse(BaseModel):
    results: List[QueryResult]


class DeleteRequest(BaseModel):
    ids: Optional[List[str]] = None
    filter: Optional[DocumentMetadataFilter] = None
    delete_all: Optional[bool] = False


class DeleteResponse(BaseModel):
    success: bool


# 新增demo用api
class AnalysisRequest(BaseModel):
    query_results: List[QueryResult]
    analysis_query: str


class AnalysisResponse(BaseModel):
    analysis_results: str
