"""Service for building recursive ownership trees from PJ partners."""

from __future__ import annotations

import logging
import re

from app.schemas import OwnershipNode, OwnershipTree
from app.services.cnpj_service import CnpjService

logger = logging.getLogger(__name__)


class OwnershipService:
    """Builds a recursive ownership tree by resolving PJ partners."""

    def __init__(self, cnpj_service: CnpjService, max_depth: int = 3) -> None:
        self.cnpj_service = cnpj_service
        self.max_depth = max_depth

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def build_tree(self, cnpj: str) -> OwnershipTree:
        """Resolve the full ownership tree starting from *cnpj*."""
        cnpj = re.sub(r"\D", "", cnpj)

        visited: set[str] = set()
        root = await self._resolve_node(
            cnpj=cnpj,
            depth=0,
            tipo="root",
            qual=None,
            visited=visited,
        )

        # Gather metrics
        total, unresolved, cycles = self._count_metrics(root)

        return OwnershipTree(
            root=root,
            max_depth=self.max_depth,
            total_nodes=total,
            unresolved_count=unresolved,
            cycles_detected=cycles,
        )

    # ------------------------------------------------------------------
    # Internal recursion
    # ------------------------------------------------------------------

    async def _resolve_node(
        self,
        cnpj: str,
        depth: int,
        tipo: str,
        qual: str | None,
        visited: set[str],
    ) -> OwnershipNode:
        """Recursively resolve a single CNPJ into an OwnershipNode."""

        # Cycle detection
        if cnpj in visited:
            logger.warning("Cycle detected for CNPJ %s at depth %d", cnpj, depth)
            return OwnershipNode(
                cnpj=cnpj,
                razao_social="(ciclo detectado)",
                depth=depth,
                tipo=tipo,
                qual=qual,
                resolved=False,
                cycle_detected=True,
            )

        visited.add(cnpj)

        # Attempt to look up the company
        try:
            company, _cached = await self.cnpj_service.lookup(cnpj)
        except Exception as exc:
            logger.exception("Failed to resolve CNPJ %s: %s", cnpj, exc)
            return OwnershipNode(
                cnpj=cnpj,
                razao_social="(não resolvido)",
                depth=depth,
                tipo=tipo,
                qual=qual,
                resolved=False,
                error=str(exc),
            )

        # Build children from the QSA
        children: list[OwnershipNode] = []
        for partner in company.qsa:
            if partner.tipo == "PJ" and depth < self.max_depth:
                partner_cnpj = re.sub(r"\D", "", partner.cnpj_cpf_do_socio or "")
                if partner_cnpj:
                    child = await self._resolve_node(
                        cnpj=partner_cnpj,
                        depth=depth + 1,
                        tipo="pj",
                        qual=partner.qual,
                        visited=visited.copy(),  # fork to allow sibling paths
                    )
                    children.append(child)
            elif partner.tipo == "Estrangeiro":
                children.append(
                    OwnershipNode(
                        cnpj=partner.cnpj_cpf_do_socio or "",
                        razao_social=partner.nome,
                        depth=depth + 1,
                        tipo="estrangeiro",
                        qual=partner.qual,
                        resolved=True,
                    )
                )
            else:
                # PF – leaf node, no further recursion
                children.append(
                    OwnershipNode(
                        cnpj=partner.cnpj_cpf_do_socio or "",
                        razao_social=partner.nome,
                        depth=depth + 1,
                        tipo="pf",
                        qual=partner.qual,
                        resolved=True,
                    )
                )

        return OwnershipNode(
            cnpj=cnpj,
            razao_social=company.razao_social,
            depth=depth,
            tipo=tipo,
            qual=qual,
            resolved=True,
            children=children,
        )

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    @staticmethod
    def _count_metrics(node: OwnershipNode) -> tuple[int, int, int]:
        """Walk the tree and return (total_nodes, unresolved_count, cycles_detected)."""
        total = 1
        unresolved = 0 if node.resolved else 1
        cycles = 1 if node.cycle_detected else 0

        for child in node.children:
            ct, cu, cc = OwnershipService._count_metrics(child)
            total += ct
            unresolved += cu
            cycles += cc

        return total, unresolved, cycles
