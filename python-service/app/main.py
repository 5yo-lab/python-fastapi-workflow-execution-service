from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.actions import router as actions_router
from app.api.workflows import router as workflows_router
from app.config import settings
from app.db.session import close_db
from app.domain.errors import AppError


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_db()


app = FastAPI(title="Workflow Execution Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


app.include_router(workflows_router)
app.include_router(actions_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
