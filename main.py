import uvicorn
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.product import router as products_router
from src.core.config import settings


def create_app():
    app = FastAPI(
        title=settings.app_title,
        docs_url="/docs",
        openapi_url="/docs.json",
        default_response_class=ORJSONResponse,
    )
    app.include_router(products_router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.app_log_level,
    )
