"""Inventory domain service.

Pure, synchronous business logic over a local inventory dataset. Every public method returns
a :class:`ToolResult`; no exception crosses the method boundary. The MCP server (see
:mod:`inventory_agent.server`) wraps these methods as tools.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from inventory_agent.errors import ErrorCategory, ToolResult

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "inventory.json"

_SKU_PATTERN = re.compile(r"^SKU-\d{4}$")


class InventoryService:
    """In-memory inventory state loaded from a JSON dataset."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._warehouses: dict[str, Any] = data["warehouses"]
        self._products: dict[str, Any] = data["products"]

    @classmethod
    def from_file(cls, path: Path | None = None) -> InventoryService:
        raw = json.loads((path or DEFAULT_DATA_PATH).read_text())
        return cls(raw)

    # -- validation helpers ------------------------------------------------------------

    def _resolve_product(self, sku: str) -> tuple[dict[str, Any] | None, ToolResult | None]:
        """Return (product, None) or (None, validation_error)."""
        # A malformed SKU and an unknown SKU are both VALIDATION failures.
        if not _SKU_PATTERN.match(sku):
            return (None, ToolResult.fail(ErrorCategory.VALIDATION, f"Malformed SKU: {sku!r}"))
        product = self._products.get(sku)
        if product is None:
            return (None, ToolResult.fail(ErrorCategory.VALIDATION, f"Unknown SKU: {sku!r}"))
        return (product, None)

    def _check_warehouse(self, warehouse_id: str) -> ToolResult | None:
        """Return a validation error if the warehouse id is unknown, else None."""
        if warehouse_id not in self._warehouses:
            return ToolResult.fail(ErrorCategory.VALIDATION, f"Unknown warehouse: {warehouse_id!r}")
        return None

    # -- tool handlers -----------------------------------------------------------------

    def check_stock(self, sku: str, warehouse_id: str) -> ToolResult:
        # Read-only lookup. An offline warehouse is TRANSIENT (retry later); a SKU with zero
        # units at a warehouse is a SUCCESS with quantity 0, not an error.
        product, validation_error = self._resolve_product(sku)
        if validation_error:
            return validation_error
        warehouse_error = self._check_warehouse(warehouse_id)
        if warehouse_error:
            return warehouse_error
        if self._warehouses[warehouse_id]["status"] != "online":
            return ToolResult.fail(
                ErrorCategory.TRANSIENT, f"Warehouse {warehouse_id} is offline"
            )
        quantity = product["stock"].get(warehouse_id, 0)
        return ToolResult.ok({"quantity": quantity})

    def update_price(self, sku: str, new_price: float, manager_approved: bool) -> ToolResult:
        # A non-positive price is VALIDATION. Without manager approval, block the mutation
        # BEFORE changing anything (PERMISSION). Only mutate once approved.
        product, validation_error = self._resolve_product(sku)
        if validation_error:
            return validation_error
        if new_price <= 0:
            return ToolResult.fail(ErrorCategory.VALIDATION, "Price must be positive")
        if not manager_approved:
            return ToolResult.fail(ErrorCategory.PERMISSION, "Manager approval required")
        previous_price = product["price"]
        product["price"] = new_price
        return ToolResult.ok({"previous_price": previous_price, "new_price": new_price})

    def process_return(self, sku: str, order_id: str, days_since_purchase: int) -> ToolResult:
        # Negative days is VALIDATION. A return past the SKU's return window is a BUSINESS
        # failure (a valid request the business rejects).
        product, validation_error = self._resolve_product(sku)
        if validation_error:
            return validation_error
        if days_since_purchase < 0:
            return ToolResult.fail(
                ErrorCategory.VALIDATION, "Days since purchase cannot be negative"
            )
        if days_since_purchase > product["return_window_days"]:
            return ToolResult.fail(
                ErrorCategory.BUSINESS, "Return past the return window for this SKU"
            )
        return ToolResult.ok({"rma_id": f"RMA-{order_id}"})

    def flag_shrinkage(self, sku: str, warehouse_id: str, suspected_units: int) -> ToolResult:
        # Validate the SKU and warehouse; suspected_units must be a positive integer.
        _product, validation_error = self._resolve_product(sku)
        if validation_error:
            return validation_error
        warehouse_error = self._check_warehouse(warehouse_id)
        if warehouse_error:
            return warehouse_error
        if suspected_units <= 0:
            return ToolResult.fail(
                ErrorCategory.VALIDATION, "Suspected units must be a positive integer"
            )
        return ToolResult.ok(
            {"shrinkage_case_id": f"SHRINKAGE-{sku}-{warehouse_id}-{suspected_units}"}
        )
