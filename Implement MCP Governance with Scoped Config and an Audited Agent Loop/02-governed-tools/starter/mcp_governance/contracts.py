"""Tool contracts -- the single source of truth for every MCP tool description.

Each description is engineered to resist the failure mode from the Architect's Playbook's
"MCP Tool Specificity" (p23): an agent defaulting to a generic built-in (web search, file
grep) instead of the authoritative custom tool. Every contract therefore carries the three
fallback-resistant elements the linter checks for:

1. an explicit **"Use this when ..."** trigger,
2. explicit **differentiation** from the generic built-in ("Use this instead of ..."),
3. a concrete **Example:** invocation.

``render()`` is what gets registered as the tool's wire description in *both* the FastMCP
server and the Anthropic bridge -- never restated in the system prompt.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolContract:
    name: str
    summary: str
    when_to_use: str
    instead_of: str
    example: str

    def render(self) -> str:
        return (
            f"{self.summary}\n"
            f"Use this when {self.when_to_use}\n"
            f"{self.instead_of}\n"
            f"Example: {self.example}"
        )


# TODO (LO-5): define one ToolContract per tool the custom servers expose --
#   get_claim, search_claims (claims-database) and lookup_policy (policy-lookup).
#   Each must carry the three built-in-fallback-resistant elements the linter scores:
#     - when_to_use: the trigger ("you have a claim ID and need its status ...")
#     - instead_of:  an explicit "Use this instead of <generic built-in> ..." that says
#                    why the custom tool wins (proprietary data, system of record).
#     - example:     a concrete invocation, e.g. get_claim(claim_id="CLM-10001")
#   render() turns these into the wire description used by BOTH the FastMCP server and the
#   bridge, so descriptions stay the single source of truth -- never re-stated in the
#   system prompt. These same descriptions must later pass lint_description at full score.

get_claim_contract = ToolContract(
    name="get_claim",
    summary="Get a claim status",
    when_to_use="you have a claim ID and need its status",
    instead_of="Use this instead of a generic built-in",
    example="get_claim(claim_id='CLM-10001')"
)

search_claims_contract = ToolContract(
    name="search_claims",
    summary="Search claims",
    when_to_use="you need to search claims",
    instead_of="Use this instead of a generic built-in",
    example="search_claims(query='CLM-10001')"
)

lookup_policy_contract = ToolContract(
    name="lookup_policy",
    summary="Lookup a policy",
    when_to_use="you need to lookup a policy",
    instead_of="Use this instead of a generic built-in",
    example="lookup_policy(policy_id='POL-10001')"
)

CONTRACTS: dict[str, ToolContract] = {
    "get_claim": get_claim_contract,
    "search_claims": search_claims_contract,
    "lookup_policy": lookup_policy_contract,
}
