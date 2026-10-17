"""Read/query-only MCP client. Credentials stay in local connector configuration."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ALLOWED = {"query-store-coupons", "query-my-coupons", "query-meals", "query-meal-detail", "calculate-price", "list-nutrition-foods"}

class Client:
    def __init__(self, config_path=None):
        token = os.environ.get("MCD_MCP_TOKEN")
        if token:
            auth = "Bearer " + token
        else:
            if not config_path:
                raise ValueError("需要 MCD_MCP_TOKEN 环境变量或显式指定本机 MCP 配置路径")
            config = json.loads(Path(config_path).read_text(encoding="utf-8"))
            server = config["mcpServers"]["mcd-mcp"]
            if server.get("url", "").rstrip("/") != "https://mcp.mcd.cn":
                raise ValueError("只允许官方 MCP 地址")
            auth = server["headers"]["Authorization"]
        self.headers = {"Authorization": auth, "Content-Type": "application/json",
                        "Accept": "application/json, text/event-stream"}
        self.seq = 0
        result = self.rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                       "clientInfo": {"name": "mcd-smart-choice", "version": "0.2.0"}})
        version = result.get("result", {}).get("protocolVersion")
        if version:
            self.headers["MCP-Protocol-Version"] = version
        self.rpc("notifications/initialized", {}, notification=True)

    def rpc(self, method, params, notification=False):
        self.seq += 1
        body = dict(jsonrpc="2.0", method=method, params=params)
        if not notification:
            body["id"] = self.seq
        req = Request("https://mcp.mcd.cn", data=json.dumps(body).encode(), headers=self.headers, method="POST")
        with urlopen(req, timeout=40) as response:
            session = response.headers.get("Mcp-Session-Id")
            if session:
                self.headers["Mcp-Session-Id"] = session
            payload = response.read().decode("utf-8")
        if notification or not payload.strip():
            return {}
        if payload.lstrip().startswith("{"):
            parsed = json.loads(payload)
        else:
            parsed = None
            for event in payload.replace("\r\n", "\n").split("\n\n"):
                chunks = [line[5:].lstrip() for line in event.splitlines() if line.startswith("data:")]
                if chunks:
                    candidate = json.loads("\n".join(chunks))
                    if candidate.get("id") == body["id"]:
                        parsed = candidate
            if parsed is None:
                raise ValueError("MCP 未返回匹配的响应")
        if "error" in parsed:
            raise ValueError("MCP JSON-RPC error; inspect sanitized local record")
        return parsed

    def tools(self):
        return self.rpc("tools/list", {}).get("result", {}).get("tools", [])

    def call(self, name, arguments):
        if name not in ALLOWED:
            raise ValueError("此客户端仅允许查询与试算，不允许下单、领券或兑换")
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})["result"]
        if result.get("isError"):
            raise ValueError("工具执行失败；不将失败结果作为报价")
        return result


def unpack(result):
    if isinstance(result.get("structuredContent"), dict):
        return result["structuredContent"]
    for item in result.get("content", []):
        if item.get("type") == "text":
            try:
                return json.loads(item["text"])
            except (ValueError, TypeError):
                continue
    raise ValueError("没有可识别的结构化业务响应")
