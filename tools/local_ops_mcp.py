#!/usr/bin/env python3
"""总控台 Codex MCP：将工作区安全同步为启动台卡片。"""

from __future__ import annotations

import json
import os
import socket
import sys
import urllib.error
import urllib.request


PORT_START = 9600
PORT_TRIES = 10
HTTP_TIMEOUT_SEC = 5
SERVER_INFO = {"name": "local-ops", "version": "1.0.0"}


def configure_stdio():
    """Use UTF-8 for the line-delimited MCP protocol on Windows."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")

TOOLS = [
    {
        "name": "get_project_candidates",
        "description": (
            "只读识别指定 Codex 工作区的启动候选命令，不创建卡片也不执行项目。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cwd": {
                    "type": "string",
                    "description": "Codex 当前工作区的绝对路径。",
                },
            },
            "required": ["cwd"],
            "additionalProperties": False,
        },
    },
    {
        "name": "sync_project",
        "description": (
            "将 Codex 工作区幂等同步到总控台启动台。只创建或更新同步元数据，"
            "绝不启动项目；默认会为前端、后端等每个独立服务同步一个最高优先级候选。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cwd": {
                    "type": "string",
                    "description": "Codex 当前工作区的绝对路径。",
                },
                "candidateIndex": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "候选命令索引；缺省时使用优先级最高的候选。",
                },
            },
            "required": ["cwd"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_synced_projects",
        "description": "按项目组列出由 Codex MCP 同步到当前总控台的独立服务与端口。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
]


class ConsoleUnavailable(RuntimeError):
    pass


class ConsoleClient:
    def __init__(self):
        self.base_url: str | None = None

    def _discover(self) -> str:
        if self.base_url:
            return self.base_url
        for port in range(PORT_START, PORT_START + PORT_TRIES):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    pass
                base_url = "http://127.0.0.1:%d" % port
                self._request_at(base_url, "GET", "/api/health")
                self.base_url = base_url
                return base_url
            except (OSError, ConsoleUnavailable):
                continue
        raise ConsoleUnavailable(
            "未找到正在运行的总控台（请先运行 D:\\workspace\\local-ops\\start.ps1）。"
        )

    def _request_at(self, base_url: str, method: str, path: str, body=None):
        payload = None
        headers = {"Accept": "application/json"}
        if body is not None:
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(
            base_url + path, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SEC) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                data = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                data = {}
            raise ConsoleUnavailable(data.get("error") or "总控台请求失败：HTTP %d" % exc.code) from exc
        except (OSError, urllib.error.URLError) as exc:
            raise ConsoleUnavailable("无法连接总控台：%s" % exc.reason) from exc
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConsoleUnavailable("总控台返回了无效响应") from exc
        if isinstance(data, dict) and data.get("ok") is False:
            raise ConsoleUnavailable(data.get("error") or "总控台请求失败")
        return data

    def request(self, method: str, path: str, body=None):
        base_url = self._discover()
        try:
            return self._request_at(base_url, method, path, body)
        except ConsoleUnavailable:
            self.base_url = None
            raise


CLIENT = ConsoleClient()


def require_cwd(arguments):
    cwd = arguments.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip():
        raise ValueError("cwd 必须是非空的工作区路径")
    return os.path.abspath(os.path.expanduser(cwd.strip()))


def call_tool(name, arguments):
    arguments = arguments if isinstance(arguments, dict) else {}
    if name == "get_project_candidates":
        return CLIENT.request("POST", "/api/project/detect", {"cwd": require_cwd(arguments)})
    if name == "sync_project":
        payload = {"cwd": require_cwd(arguments)}
        if "candidateIndex" in arguments:
            payload["candidateIndex"] = arguments["candidateIndex"]
        return CLIENT.request("POST", "/api/integrations/codex/sync", payload)
    if name == "list_synced_projects":
        state = CLIENT.request("GET", "/api/state")
        grouped = {}
        order = []
        for app in state.get("apps", []):
            sync = app.get("sync")
            if not isinstance(sync, dict) or sync.get("origin") != "codex":
                continue
            project_key = sync.get("projectKey") or sync.get("key")
            if not project_key:
                continue
            if project_key not in grouped:
                grouped[project_key] = {
                    "key": project_key,
                    "name": sync.get("projectName") or app.get("name") or "未命名项目",
                    "cwd": sync.get("projectPath") or app.get("cwd"),
                    "services": [],
                }
                order.append(project_key)
        for app in state.get("apps", []):
            sync = app.get("sync") if isinstance(app.get("sync"), dict) else {}
            project = app.get("project") if isinstance(app.get("project"), dict) else {}
            project_key = (sync.get("projectKey") or sync.get("key")
                           if sync.get("origin") == "codex"
                           else project.get("key"))
            if project_key not in grouped:
                continue
            if sync.get("origin") == "codex":
                grouped[project_key]["name"] = sync.get("projectName") or grouped[project_key]["name"]
                grouped[project_key]["cwd"] = sync.get("projectPath") or grouped[project_key]["cwd"]
            ports = app.get("ports") or ([] if app.get("port") is None else [app["port"]])
            grouped[project_key]["services"].append({
                "id": app.get("id"),
                "name": app.get("name"),
                "role": sync.get("role") or "service",
                "cwd": app.get("cwd"),
                "command": app.get("command"),
                "running": bool(app.get("running")),
                "ports": ports,
            })
        projects = []
        for project_key in order:
            project = grouped[project_key]
            project["runningCount"] = sum(
                1 for service in project["services"] if service["running"])
            project["ports"] = sorted({port for service in project["services"]
                                       for port in service["ports"]
                                       if isinstance(port, int)})
            projects.append(project)
        return {
            "projects": projects,
        }
    raise ValueError("未知工具：%s" % name)


def send(message):
    sys.stdout.write(json.dumps(message, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def tool_result(result, is_error=False):
    text = result if isinstance(result, str) else json.dumps(
        result, ensure_ascii=False, indent=2)
    payload = {"content": [{"type": "text", "text": text}]}
    if is_error:
        payload["isError"] = True
    return payload


def handle(message):
    method = message.get("method")
    request_id = message.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        requested = (message.get("params") or {}).get("protocolVersion")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": requested or "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = call_tool(params.get("name"), params.get("arguments"))
            payload = tool_result(result)
        except (ConsoleUnavailable, ValueError) as exc:
            payload = tool_result(str(exc), is_error=True)
        return {"jsonrpc": "2.0", "id": request_id, "result": payload}
    if request_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": "不支持的方法：%s" % method},
    }


def main():
    configure_stdio()
    for line in sys.stdin:
        try:
            message = json.loads(line)
            if not isinstance(message, dict):
                raise ValueError("请求必须是对象")
            response = handle(message)
        except (ValueError, json.JSONDecodeError) as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": str(exc)},
            }
        if response is not None:
            send(response)


if __name__ == "__main__":
    main()
