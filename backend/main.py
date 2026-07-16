import os

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

import models  # noqa: F401  (모델을 등록해 create_all이 4테이블을 인식하게 함)
from database import Base, engine
from routers import auth, messages, tasks, teams

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskFlow API")

DEFAULT_ORIGINS = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", DEFAULT_ORIGINS).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "VALIDATION_ERROR", "message": "올바른 형식이 아닙니다"}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    # api_error()가 만든 detail은 이미 { error: {...} } 형태이므로 그대로 반환한다.
    # (FastAPI 기본 핸들러는 이걸 { detail: {...} }로 한 번 더 감싸버린다.)
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "ERROR", "message": str(exc.detail)}})


app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(tasks.router)
app.include_router(messages.router)


@app.get("/health")
def health():
    return {"status": "ok"}


FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
# Vercel에서는 frontend/를 별도 정적 파일로 서빙하므로(vercel.json) 여기서 마운트하지 않는다.
if not os.environ.get("VERCEL") and os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
