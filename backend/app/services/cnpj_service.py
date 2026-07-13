"""Service for looking up CNPJ data via BrasilAPI with PostgreSQL caching."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models import CnpjCache
from app.schemas import CompanyData, Partner

logger = logging.getLogger(__name__)


class CnpjService:
    """Handles CNPJ lookups against BrasilAPI and manages the local cache."""

    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def lookup(self, cnpj: str) -> tuple[CompanyData, bool]:
        """Look up a CNPJ, returning ``(CompanyData, cached: bool)``.

        The method checks the local cache first.  If the cached entry is
        still valid (within ``CACHE_TTL_HOURS``), it is returned directly.
        Otherwise a fresh request is made to BrasilAPI and the cache is
        upserted.
        """
        cnpj = self._clean_cnpj(cnpj)

        # 1. Try cache ------------------------------------------------
        cached_entry = await self._get_cached(cnpj)
        if cached_entry is not None:
            company = self._parse_response(cnpj, cached_entry.data)
            return company, True

        # 2. Fetch from BrasilAPI -------------------------------------
        raw_data = await self._fetch_from_api(cnpj)

        # 3. Upsert cache --------------------------------------------
        await self._upsert_cache(cnpj, raw_data)

        # 4. Parse & return -------------------------------------------
        company = self._parse_response(cnpj, raw_data)
        return company, False

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    async def _get_cached(self, cnpj: str) -> CnpjCache | None:
        """Return the cached entry if it exists and has not expired."""
        stmt = select(CnpjCache).where(CnpjCache.cnpj == cnpj)
        result = await self.db.execute(stmt)
        entry: CnpjCache | None = result.scalar_one_or_none()

        if entry is None:
            return None

        ttl = timedelta(hours=self.settings.CACHE_TTL_HOURS)
        if datetime.now(timezone.utc) - entry.consulted_at > ttl:
            logger.info("Cache expired for CNPJ %s", cnpj)
            return None

        return entry

    async def _upsert_cache(self, cnpj: str, data: dict) -> None:
        """Insert or update the cache row for *cnpj*."""
        stmt = select(CnpjCache).where(CnpjCache.cnpj == cnpj)
        result = await self.db.execute(stmt)
        entry: CnpjCache | None = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if entry is not None:
            entry.data = data
            entry.consulted_at = now
            entry.source = "brasilapi"
        else:
            entry = CnpjCache(
                cnpj=cnpj,
                data=data,
                consulted_at=now,
                source="brasilapi",
            )
            self.db.add(entry)

        await self.db.flush()

    # ------------------------------------------------------------------
    # BrasilAPI interaction
    # ------------------------------------------------------------------

    async def _fetch_from_api(self, cnpj: str) -> dict:
        """Call BrasilAPI and return the raw JSON response dict."""
        url = f"{self.settings.CNPJ_API_BASE_URL}/{cnpj}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)

            if response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="CNPJ não encontrado",
                )

            if response.status_code != 200:
                logger.error(
                    "BrasilAPI returned status %s for CNPJ %s",
                    response.status_code,
                    cnpj,
                )
                raise HTTPException(
                    status_code=502,
                    detail="Erro ao consultar BrasilAPI",
                )

            return response.json()

        except httpx.HTTPError as exc:
            logger.exception("HTTP error fetching CNPJ %s: %s", cnpj, exc)
            raise HTTPException(
                status_code=502,
                detail="Erro ao consultar BrasilAPI",
            ) from exc

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_cnpj(cnpj: str) -> str:
        """Strip everything that is not a digit."""
        return re.sub(r"\D", "", cnpj)

    @staticmethod
    def _detect_partner_type(partner: dict) -> str:
        """Determine whether a QSA member is PF, PJ, or Estrangeiro."""
        cpf_cnpj: str = partner.get("cnpj_cpf_do_socio", "") or ""
        digits = re.sub(r"\D", "", cpf_cnpj)

        if len(digits) == 14:
            return "PJ"

        pais = (partner.get("pais_origem") or "").strip().upper()
        if pais and pais != "BRASIL":
            return "Estrangeiro"

        return "PF"

    def _parse_response(self, cnpj: str, data: dict) -> CompanyData:
        """Build a ``CompanyData`` schema from raw BrasilAPI JSON."""
        qsa_raw: list[dict] = data.get("qsa") or []

        partners: list[Partner] = []
        for p in qsa_raw:
            tipo = self._detect_partner_type(p)
            cpf_cnpj_raw = p.get("cnpj_cpf_do_socio") or None
            partners.append(
                Partner(
                    nome=p.get("nome_socio", ""),
                    qual=p.get("qualificacao_socio", ""),
                    pais_origem=p.get("pais_origem") or None,
                    nome_rep_legal=p.get("nome_representante_legal") or None,
                    qual_rep_legal=p.get("qualificacao_representante_legal") or None,
                    faixa_etaria=p.get("faixa_etaria") or None,
                    cnpj_cpf_do_socio=cpf_cnpj_raw,
                    tipo=tipo,
                )
            )

        pj_partners = [p for p in partners if p.tipo == "PJ"]

        return CompanyData(
            cnpj=cnpj,
            razao_social=data.get("razao_social", ""),
            nome_fantasia=data.get("nome_fantasia") or None,
            situacao_cadastral=data.get("descricao_situacao_cadastral") or None,
            data_situacao_cadastral=data.get("data_situacao_cadastral") or None,
            data_inicio_atividade=data.get("data_inicio_atividade") or None,
            cnae_fiscal_descricao=data.get("cnae_fiscal_descricao") or None,
            uf=data.get("uf") or None,
            municipio=data.get("municipio") or None,
            natureza_juridica=data.get("natureza_juridica") or None,
            porte=data.get("porte") or None,
            capital_social=data.get("capital_social"),
            qsa=partners,
            pj_partners=pj_partners,
            has_pj_partners=len(pj_partners) > 0,
        )
