from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routes.chat import router as chat_router
from app.routes.auth import router as auth_router
from app.routes.connections import router as connections_router
from app.routes.models import router as models_router
from fastapi import Depends
from core.database import get_postgres_db

load_dotenv(override=True)

app = FastAPI()

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active threads (in production, use a proper database)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(connections_router)
app.include_router(models_router)


@app.get("/health")
async def health_check(db=Depends(get_postgres_db)):
    """Basic health check. Verifies server is up and can access the Postgres DB."""
    try:
        # simple DB call to verify connectivity
        list(db.execute("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "db": db_status}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
