"""Pydantic schemas for API request/response serialization."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Partner (QSA member)
# ---------------------------------------------------------------------------

class Partner(BaseModel):
    """A single partner / QSA member of a company."""

    nome: str
    qual: str = Field(..., description="Qualificação do sócio")
    pais_origem: str | None = None
    nome_rep_legal: str | None = None
    qual_rep_legal: str | None = None
    faixa_etaria: str | None = None
    cnpj_cpf_do_socio: str | None = None
    tipo: str = Field(
        default="PF",
        description="Computed partner type: 'PF', 'PJ', or 'Estrangeiro'",
    )


# ---------------------------------------------------------------------------
# Company data
# ---------------------------------------------------------------------------

class CompanyData(BaseModel):
    """Parsed company information from BrasilAPI."""

    cnpj: str
    razao_social: str
    nome_fantasia: str | None = None
    situacao_cadastral: str | None = None
    data_situacao_cadastral: str | None = None
    data_inicio_atividade: str | None = None
    cnae_fiscal_descricao: str | None = None
    uf: str | None = None
    municipio: str | None = None
    natureza_juridica: str | None = None
    porte: str | None = None
    capital_social: float | None = None
    qsa: list[Partner] = []
    pj_partners: list[Partner] = Field(
        default=[],
        description="Filtered list containing only PJ (legal-entity) partners",
    )
    has_pj_partners: bool = False


# ---------------------------------------------------------------------------
# Ownership tree
# ---------------------------------------------------------------------------

class OwnershipNode(BaseModel):
    """A single node in the recursive ownership tree."""

    cnpj: str
    razao_social: str
    depth: int = 0
    tipo: str = Field(
        default="root",
        description="Node type: 'root', 'pj', 'pf', 'estrangeiro'",
    )
    qual: str | None = None
    resolved: bool = True
    cycle_detected: bool = False
    error: str | None = None
    children: list[OwnershipNode] = []


class OwnershipTree(BaseModel):
    """Complete ownership tree with metadata."""

    root: OwnershipNode
    max_depth: int
    total_nodes: int
    unresolved_count: int
    cycles_detected: int


# ---------------------------------------------------------------------------
# API responses
# ---------------------------------------------------------------------------

class LookupResponse(BaseModel):
    """Top-level response for CNPJ lookup endpoints."""

    company: CompanyData
    ownership_tree: OwnershipTree | None = None
    cached: bool = False
    consulted_at: str
    source: str = "brasilapi"
    query_duration_ms: float


class ErrorResponse(BaseModel):
    """Standard error payload."""

    detail: str
    cnpj: str | None = None
