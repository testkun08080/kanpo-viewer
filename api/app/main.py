from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import Settings
from .api.pdf import router as pdf

settings = Settings()

# Create FastAPI app instance with settings
app = FastAPI(
    title=settings.project_name,
    description=settings.project_description,
    version=settings.version,
    root_path=settings.root_path,
    docs_url="/docs" if settings.debug else None,  # 本番環境ではドキュメント無効化
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware with domain whitelist
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # 必要なメソッドのみ許可
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "User-Agent",
    ],
)

# Add router for PDF download api
app.include_router(pdf, prefix="/pdf")

# Simple root endpoint
@app.get("/")
async def read_root():
    return {
        "message": "Kanpo PDF Download API",
        "version": settings.version,
        "endpoints": {
            "health": "/api/pdf/health",
            "download": "/api/pdf/download"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
