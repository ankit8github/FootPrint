from fastapi import FastAPI, Request, Response
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.contracts import DemoSnapshot, Health

app = FastAPI(
    title="PV1 synthetic Phase 0 API",
    version="0.1.0",
    description="Local scaffold only. No record ingestion or analysis endpoints.",
    docs_url=None,
    redoc_url=None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])


@app.middleware("http")
async def response_headers(request: Request, call_next: RequestResponseEndpoint) -> Response:
    response: Response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/api/v1/health")
def health() -> Health:
    """Process liveness only; does not assert database readiness."""
    return Health()


@app.get("/api/v1/demo")
def demo() -> DemoSnapshot:
    return DemoSnapshot()
