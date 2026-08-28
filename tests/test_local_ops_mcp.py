import importlib.util
from pathlib import Path
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "local_ops_mcp.py"
SPEC = importlib.util.spec_from_file_location("local_ops_mcp", MODULE_PATH)
local_ops_mcp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(local_ops_mcp)


class LocalOpsMcpTests(unittest.TestCase):
    def test_initialize_and_tool_listing_follow_mcp_protocol(self):
        initialized = local_ops_mcp.handle({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26"},
        })
        self.assertEqual(initialized["result"]["protocolVersion"], "2025-03-26")

        listed = local_ops_mcp.handle({
            "jsonrpc": "2.0", "id": 2, "method": "tools/list",
        })
        self.assertEqual(
            [tool["name"] for tool in listed["result"]["tools"]],
            ["get_project_candidates", "sync_project", "list_synced_projects"],
        )

    def test_sync_tool_delegates_to_atomic_console_route(self):
        with mock.patch.object(local_ops_mcp.CLIENT, "request", return_value={"ok": True}) as request:
            result = local_ops_mcp.call_tool("sync_project", {
                "cwd": r"D:\workspace\demo", "candidateIndex": 1,
            })

        self.assertEqual(result, {"ok": True})
        request.assert_called_once_with(
            "POST", "/api/integrations/codex/sync",
            {"cwd": r"D:\workspace\demo", "candidateIndex": 1},
        )

    def test_default_sync_omits_candidate_index_for_multi_service_selection(self):
        with mock.patch.object(local_ops_mcp.CLIENT, "request", return_value={"ok": True}) as request:
            result = local_ops_mcp.call_tool("sync_project", {"cwd": r"D:\workspace\demo"})

        self.assertEqual(result, {"ok": True})
        request.assert_called_once_with(
            "POST", "/api/integrations/codex/sync",
            {"cwd": r"D:\workspace\demo"},
        )

    def test_list_synced_projects_groups_services_and_ports(self):
        state = {"apps": [
            {"id": "front", "name": "Demo · frontend", "cwd": r"D:\demo\frontend",
             "command": "npm run dev", "running": True, "ports": [5173], "port": 5173,
             "sync": {"origin": "codex", "projectKey": "codex:demo",
                      "projectName": "Demo", "projectPath": r"D:\demo", "role": "frontend"}},
            {"id": "back", "name": "Demo · backend", "cwd": r"D:\demo\backend",
             "command": "python main.py", "running": False, "ports": [], "port": 8000,
             "sync": {"origin": "codex", "projectKey": "codex:demo",
                      "projectName": "Demo", "projectPath": r"D:\demo", "role": "backend"}},
            {"id": "proxy", "name": "Demo proxy", "cwd": r"D:\demo\tools",
             "command": "python proxy.py", "running": True, "ports": [8787], "port": 8787,
             "project": {"key": "codex:demo", "name": "Demo", "cwd": r"D:\demo"},
             "sync": None},
        ]}
        with mock.patch.object(local_ops_mcp.CLIENT, "request", return_value=state):
            result = local_ops_mcp.call_tool("list_synced_projects", {})

        self.assertEqual(len(result["projects"]), 1)
        project = result["projects"][0]
        self.assertEqual(project["runningCount"], 2)
        self.assertEqual(project["ports"], [5173, 8000, 8787])
        self.assertEqual([service["role"] for service in project["services"]],
                         ["frontend", "backend", "service"])
