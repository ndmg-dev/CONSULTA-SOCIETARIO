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
    def _cnpj_check_digits(base12: str) -> str:
        """Return the two check digits for a 12-digit CNPJ base."""

        def calc(nums: str) -> str:
            weights = list(range(2, 10)) * 2
            total = sum(int(d) * weights[i] for i, d in enumerate(reversed(nums)))
            remainder = total % 11
            return "0" if remainder < 2 else str(11 - remainder)

        d1 = calc(base12)
        d2 = calc(base12 + d1)
        return d1 + d2

    @classmethod
    def _complete_cnpj_base(cls, base8: str) -> str | None:
        """Complete an 8-digit CNPJ *root* into the full matriz CNPJ.

        BrasilAPI only returns the 8-digit root for PJ partners.  We assume
        the matriz establishment (``0001``) and compute the check digits.
        Returns ``None`` if *base8* is not exactly 8 digits.
        """
        digits = re.sub(r"\D", "", base8)
        if len(digits) != 8:
            return None
        base12 = digits + "0001"
        return base12 + cls._cnpj_check_digits(base12)

    @staticmethod
    def _detect_partner_type(partner: dict) -> str:
        """Determine whether a QSA member is PF, PJ, or Estrangeiro.

        The Receita Federal ``identificador_de_socio`` is authoritative when
        present (1=PJ, 2=PF, 3=Estrangeiro); we fall back to the document
        length (BrasilAPI returns an 8-digit root or a 14-digit CNPJ for PJ).
        """
        identificador = partner.get("identificador_de_socio")
        if identificador == 1:
            return "PJ"
        if identificador == 3:
            return "Estrangeiro"
        if identificador == 2:
            return "PF"

        cpf_cnpj: str = partner.get("cnpj_cpf_do_socio", "") or ""
        digits = re.sub(r"\D", "", cpf_cnpj)

        if len(digits) in (8, 14):
            return "PJ"

        pais = (partner.get("pais_origem") or partner.get("pais") or "").strip().upper()
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

            # For PJ partners BrasilAPI only returns the 8-digit root; build
            # the full matriz CNPJ so the ownership tree can resolve it.
            cnpj_completo = None
            if tipo == "PJ" and cpf_cnpj_raw:
                digits = re.sub(r"\D", "", cpf_cnpj_raw)
                if len(digits) == 14:
                    cnpj_completo = digits
                elif len(digits) == 8:
                    cnpj_completo = self._complete_cnpj_base(digits)

            # The Receita masks partner CPFs (e.g. ``***298554**``); flag it so
            # the UI can explain the source limitation.
            cpf_mascarado = bool(cpf_cnpj_raw and "*" in cpf_cnpj_raw)

            partners.append(
                Partner(
                    nome=p.get("nome_socio", ""),
                    qual=p.get("qualificacao_socio", ""),
                    pais_origem=p.get("pais_origem") or p.get("pais") or None,
                    nome_rep_legal=p.get("nome_representante_legal") or None,
                    qual_rep_legal=p.get("qualificacao_representante_legal") or None,
                    faixa_etaria=p.get("faixa_etaria") or None,
                    cnpj_cpf_do_socio=cpf_cnpj_raw,
                    cnpj_completo=cnpj_completo,
                    cpf_mascarado=cpf_mascarado,
                    identificador_de_socio=p.get("identificador_de_socio"),
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
