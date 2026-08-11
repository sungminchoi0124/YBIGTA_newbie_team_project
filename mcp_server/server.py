import os
from fastmcp import FastMCP, Context
from tools.latest import get_latest_data
from tools.search import search_data
from tools.aggregation import aggregate_data

mcp = FastMCP("Crypto-MCP-Server")

def verify_auth(ctx: Context):
    expected_token = os.getenv("MCP_AUTH_TOKEN")
    if not expected_token:
        return

    headers = {}
    if ctx and hasattr(ctx, "request_context") and ctx.request_context:
        meta = getattr(ctx.request_context, "meta", None)
        if meta:
            if isinstance(meta, dict):
                headers = meta.get("headers", {})
            elif hasattr(meta, "headers"):
                headers = getattr(meta, "headers", {}) or {}

    auth_header = ""
    if isinstance(headers, dict):
        auth_header = headers.get("authorization") or headers.get("Authorization") or ""

    if not auth_header.startswith("Bearer ") or auth_header.split("Bearer ")[1] != expected_token:
        raise PermissionError("인증에 실패하였습니다. 올바른 Bearer Token이 필요합니다.")

@mcp.tool()
def get_latest_data_tool(limit: int = 10, ctx: Context = None) -> list:
    """가장 최근에 수집된 암호화폐 가격 데이터 목록을 조회합니다."""
    if ctx:
        verify_auth(ctx)
    return get_latest_data(limit=limit)

@mcp.tool()
def search_data_tool(symbol: str, limit: int = 20, ctx: Context = None) -> list:
    """특정 암호화폐 종목(BTC, ETH 등)의 과거 가격 수집 내역을 검색합니다."""
    if ctx:
        verify_auth(ctx)
    return search_data(symbol=symbol, limit=limit)

@mcp.tool()
def aggregate_data_tool(symbol: str, ctx: Context = None) -> dict:
    """특정 암호화폐 종목의 평균, 최고, 최저 가격 및 총 수집 건수를 집계합니다."""
    if ctx:
        verify_auth(ctx)
    return aggregate_data(symbol=symbol)

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8000)