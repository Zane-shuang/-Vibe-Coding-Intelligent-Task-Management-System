from fastapi import FastAPI
from app.core.config import settings
from app.api.routes.task import router as task_router

app = FastAPI(title=settings.APP_NAME)
app.include_router(task_router)

@app.get("/health")
def health():
    return {"status": "ok"}