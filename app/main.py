from fastapi import FastAPI, Request
from app.core.config import settings
from app.api.routes.task import router as task_router
import time
app = FastAPI(title=settings.APP_NAME)
app.include_router(task_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = round((time.time() - start_time) * 1000, 2)  # 转成毫秒
    response.headers["X-Process-Time"] = f"{process_time}ms"
    print(f"[{request.method}] {request.url.path} - {process_time}ms")
    return response