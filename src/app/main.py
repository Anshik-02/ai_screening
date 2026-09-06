from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.api.candidate_routes import router as candidate_router
from app.web.routes import router as web_router

app = FastAPI(
    title="TalentRank Studio",
    version="0.2.0",
    description=(
        "AI Resume Screening for recruiters (Recruiter Mode) "
        "and personalised interview prep for candidates (Candidate Mode)."
    ),
)

# Allow dashboard access from alternate local origins (e.g., VS Code Live Server).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="src/app/web/static"), name="static")

from app.services import llm_client

@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "llm_configured": llm_client.is_available(),
        "provider": llm_client._provider(),
    }

app.include_router(web_router)
app.include_router(router)
app.include_router(candidate_router)


