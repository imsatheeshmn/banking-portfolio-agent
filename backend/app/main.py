"""FastAPI application entrypoint with centralized error contracts."""

from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.domain.exceptions import (
    DomainError,
    InsufficientHoldingsError,
    InvalidStateTransitionError,
    ValidationError,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="Enterprise Bitemporal Investment Data Engineering & Portfolio Intelligence Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InsufficientHoldingsError)
async def insufficient_holdings_handler(
    request: Request, exc: InsufficientHoldingsError
) -> JSONResponse:
    """RFC 7807 handler for long-only holdings violations (ADR-003)."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://api.portfolio.internal/errors/insufficient-holdings",
            "title": "Insufficient Holdings",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "code": exc.code,
            "detail": exc.message,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """RFC 7807 handler for domain validation failures."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "https://api.portfolio.internal/errors/validation-failure",
            "title": "Validation Failure",
            "status": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "code": exc.code,
            "detail": exc.message,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(
    request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    """RFC 7807 handler for illegal state machine transitions."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "type": "https://api.portfolio.internal/errors/state-conflict",
            "title": "Invalid State Transition",
            "status": status.HTTP_409_CONFLICT,
            "code": exc.code,
            "detail": exc.message,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Catch-all RFC 7807 handler for other domain exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "type": "https://api.portfolio.internal/errors/domain-error",
            "title": "Domain Exception",
            "status": status.HTTP_400_BAD_REQUEST,
            "code": exc.code,
            "detail": exc.message,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Basic health check and readiness probe."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.ENVIRONMENT,
    }


# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
