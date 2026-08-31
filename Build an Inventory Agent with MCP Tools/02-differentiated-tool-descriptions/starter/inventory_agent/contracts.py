"""Tool contracts — the single source of truth for each tool's description.

A description is the primary mechanism an LLM uses to choose a tool. When two tools accept the
same input (``check_stock`` and ``process_return`` both take a product id), only an explicit
boundary clause keeps the agent from misrouting. Each contract therefore carries its purpose,
inputs, outputs, an explicit "do not use for" boundary, an example query, and an edge-case note.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContract:
    name: str
    purpose: str
    inputs: str
    outputs: str
    boundaries: str
    example_query: str
    edge_case: str

    def render(self) -> str:
        """Render the contract into the description string registered with the tool."""
        return (
            f"Purpose: {self.purpose}\n"
            f"Inputs: {self.inputs}\n"
            f"Outputs: {self.outputs}\n"
            f"Do NOT use for: {self.boundaries}\n"
            f"Example query: {self.example_query}\n"
            f"Edge case: {self.edge_case}"
        )


# TODO: Write a differentiated contract for each of the four single-purpose tools. Fill in every
# field with real text. The two tools that share a product-id input (check_stock and
# process_return) must each name the other in their `boundaries` ("do not use for...") so the
# agent never confuses a stock lookup with a return. Keep each tool single-purpose: no catch-all
# "mode" tool. Replace the empty strings below.
CONTRACTS: dict[str, ToolContract] = {
    "check_stock": ToolContract(
        name="check_stock",
        purpose="Check the current stock level for a given SKU. Do not use for processing returns or flagging shrinkage or updating prices.",
        inputs="SKU",
        outputs="Stock level",
        boundaries="process_return",
        example_query="check_stock(SKU=123456)",
        edge_case="A SKU with zero units at a warehouse is a successful result (quantity 0), not an error. An offline warehouse is a transient failure the agent may retry.",
    ),
    "update_price": ToolContract(
        name="update_price",
        purpose="Update the price for a given SKU. Do not use for processing returns or flagging shrinkage or checking stock.",
        inputs="SKU, new price",
        outputs="Previous price, new price",
        boundaries="check_stock",
        example_query="update_price(SKU=123456, new price=100.00)",
        edge_case="A non-positive price is rejected as a validation error. A change without manager approval is blocked before any mutation and returned as a permission failure.",
    ),
    "process_return": ToolContract(
        name="process_return",
        purpose="Process a return for a given SKU. Do not use for checking stock or updating prices or flagging shrinkage.",
        inputs="SKU, order ID, days since purchase",
        outputs="RMA ID",
        boundaries="check_stock",
        example_query="process_return(SKU=123456, order ID=1234567890, days since purchase=10)",
        edge_case="A return past the SKU's return window is a business rejection (a valid request the business declines), not a validation error. Negative days since purchase is a validation error.",
    ),
    "flag_shrinkage": ToolContract(
        name="flag_shrinkage",
        purpose="Flag a shrinkage event for a given SKU. Do not use for checking stock or updating prices or processing returns.",
        inputs="SKU, warehouse ID, suspected units",
        outputs="Shrinkage case ID",
        boundaries="check_stock",
        example_query="flag_shrinkage(SKU=123456, warehouse ID=1234567890, suspected units=10)",
        edge_case="Suspected units must be a positive integer; zero or negative units is a validation error. This records a suspected-loss case for review, it does not adjust stock levels.",
    ),
}
