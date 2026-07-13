"""CNPJ lookup and ownership-tree API routes."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import ErrorResponse, LookupResponse
from app.services.cnpj_service import CnpjService
from app.services.ownership import OwnershipService

router = APIRouter(prefix="/api", tags=["cnpj"])


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@router.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Return a simple health-check response."""
    return {"status": "ok"}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _validate_cnpj(raw: str) -> str:
    """Strip non-digit characters and validate that the CNPJ has 14 digits."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 14:
        raise HTTPException(
            status_code=422,
            detail="CNPJ deve conter exatamente 14 dígitos",
        )
    return digits


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@router.get(
    "/cnpj/{cnpj}",
    response_model=LookupResponse,
    responses={
        404: {"model": ErrorResponse, "description": "CNPJ not found"},
        422: {"model": ErrorResponse, "description": "Invalid CNPJ format"},
        502: {"model": ErrorResponse, "description": "Upstream API error"},
    },
    summary="Look up a CNPJ",
)
async def lookup_cnpj(
    cnpj: str,
    db: AsyncSession = Depends(get_db),
) -> LookupResponse:
    """Fetch company data for the given CNPJ.

    Results are cached in PostgreSQL for ``CACHE_TTL_HOURS`` hours.
    """
    cleaned = _validate_cnpj(cnpj)

    service = CnpjService(db=db, settings=settings)

    start = time.perf_counter()
    company, cached = await service.lookup(cleaned)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return LookupResponse(
        company=company,
        cached=cached,
        consulted_at=datetime.now(timezone.utc).isoformat(),
        source="brasilapi",
        query_duration_ms=round(elapsed_ms, 2),
    )


@router.get(
    "/cnpj/{cnpj}/ownership",
    response_model=LookupResponse,
    responses={
        404: {"model": ErrorResponse, "description": "CNPJ not found"},
        422: {"model": ErrorResponse, "description": "Invalid CNPJ format"},
        502: {"model": ErrorResponse, "description": "Upstream API error"},
    },
    summary="Look up a CNPJ with full ownership tree",
)
async def lookup_cnpj_ownership(
    cnpj: str,
    db: AsyncSession = Depends(get_db),
) -> LookupResponse:
    """Fetch company data **and** recursively build the ownership tree.

    PJ partners are resolved up to ``MAX_RECURSION_DEPTH`` levels.
    """
    cleaned = _validate_cnpj(cnpj)

    cnpj_service = CnpjService(db=db, settings=settings)
    ownership_service = OwnershipService(
        cnpj_service=cnpj_service,
        max_depth=settings.MAX_RECURSION_DEPTH,
    )

    start = time.perf_counter()
    company, cached = await cnpj_service.lookup(cleaned)
    tree = await ownership_service.build_tree(cleaned)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return LookupResponse(
        company=company,
        ownership_tree=tree,
        cached=cached,
        consulted_at=datetime.now(timezone.utc).isoformat(),
        source="brasilapi",
        query_duration_ms=round(elapsed_ms, 2),
    )
