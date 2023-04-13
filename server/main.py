import os
import uvicorn
from fastapi import FastAPI, File, HTTPException, Depends, Body, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles

from models.api import (
    DeleteRequest,
    DeleteResponse,
    QueryRequest,
    QueryResponse,
    UpsertRequest,
    UpsertResponse, AnalysisResponse, AnalysisRequest, SearchResponse, SearchRequest,
)
from datastore.factory import get_datastore
from services.file import get_document_from_file

app = FastAPI()
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="static")
app.mount("/.test-html", StaticFiles(directory=".test-html"), name="static")

# Create a sub-application, in order to access just the query endpoints in the OpenAPI schema, found at http://0.0.0.0:8000/sub/openapi.json when the app is running locally
sub_app = FastAPI(
    title="Retrieval Plugin API",
    description="A retrieval API for querying and filtering documents based on natural language queries and metadata",
    version="1.0.0",
    servers=[{"url": "https://your-app-url.com"}],
)
app.mount("/sub", sub_app)


@app.post(
    "/upsert-file",
    response_model=UpsertResponse,
)
async def upsert_file(
        file: UploadFile = File(...),
):
    document = await get_document_from_file(file)

    try:
        ids = await datastore.upsert([document])
        return UpsertResponse(ids=ids)
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=f"str({e})")


@app.post(
    "/upsert",
    response_model=UpsertResponse,
)
async def upsert(
        request: UpsertRequest = Body(...),
):
    try:
        ids = await datastore.upsert(request.documents)
        return UpsertResponse(ids=ids)
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@app.post(
    "/query",
    response_model=QueryResponse,
)
async def query_main(
        request: QueryRequest = Body(...),
):
    try:
        results = await datastore.query(
            request.queries,
        )
        return QueryResponse(results=results)
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@sub_app.post(
    "/query",
    response_model=QueryResponse,
    description="Accepts search query objects with query and optional filter. Break down complex questions into sub-questions. Refine results by criteria, e.g. time / source, don't do this often. Split queries if ResponseTooLargeError occurs.",
)
async def query(
        request: QueryRequest = Body(...),
):
    try:
        results = await datastore.query(
            request.queries,
        )
        return QueryResponse(results=results)
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@app.delete(
    "/delete",
    response_model=DeleteResponse,
)
async def delete(
        request: DeleteRequest = Body(...),
):
    if not (request.ids or request.filter or request.delete_all):
        raise HTTPException(
            status_code=400,
            detail="One of ids, filter, or delete_all is required",
        )
    try:
        success = await datastore.delete(
            ids=request.ids,
            filter=request.filter,
            delete_all=request.delete_all,
        )
        return DeleteResponse(success=success)
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@app.on_event("startup")
async def startup():
    global datastore
    datastore = await get_datastore()


def start():
    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=True)


# 新增demo用接口
from services.openai import get_chat_completion


@app.post(
    "/analysis",
    response_model=AnalysisResponse,
)
async def analysis_main(
        request: AnalysisRequest = Body(...),
):
    try:
        messages = [
            {
                "role": "system",
                "content": f"""
                    You can only respond in the role of a personal assistant, where your answers are ideally based on the returned JSON and the extracted information to answer the user's question. If there is no relevant information in the JSON, you are free to provide a response based on your own understanding. Here is the specific returned JSON:
                    {request.query_results}
                    """,
            },
            {"role": "user", "content": request.analysis_query}
        ]
        completion = get_chat_completion(messages=messages)
        return AnalysisResponse(analysis_results=completion)
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Service Error")


@app.post(
    "/search",
    response_model=SearchResponse,
)
async def analysis_main(
        request: SearchRequest = Body(...),
):
    try:
        from googlesearch import search
        return SearchResponse(query = request.search_query,results=[item.description for item in search(request.search_query, num_results=3, advanced=True)])
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail="Internal Service Error")
