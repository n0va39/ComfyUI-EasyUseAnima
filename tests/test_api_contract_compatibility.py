from __future__ import annotations

import ast
import importlib
import sys
import types
import unittest
from pathlib import Path

import api_contract
from easyuse_anima.api import errors, requests, responses


ROOT = Path(__file__).resolve().parents[1]
API_PATH = ROOT / "api.py"
EXPECTED_EXPORTS = [
    "REQUEST_ID_HEADER",
    "ApiContractError",
    "error_payload",
    "create_request_id",
    "attach_request_id_header",
    "correlate_response",
    "parse_json_object",
    "json_object",
    "json_string",
    "json_boolean",
    "json_integer",
    "json_uuid_string",
]


def canonical_exports(errors_module, requests_module, responses_module):
    return {
        "REQUEST_ID_HEADER": responses_module.REQUEST_ID_HEADER,
        "ApiContractError": errors_module.ApiContractError,
        "error_payload": responses_module.error_payload,
        "create_request_id": responses_module.create_request_id,
        "attach_request_id_header": responses_module.attach_request_id_header,
        "correlate_response": responses_module.correlate_response,
        "parse_json_object": requests_module.parse_json_object,
        "json_object": requests_module.json_object,
        "json_string": requests_module.json_string,
        "json_boolean": requests_module.json_boolean,
        "json_integer": requests_module.json_integer,
        "json_uuid_string": requests_module.json_uuid_string,
    }


class ApiContractCompatibilityTests(unittest.TestCase):
    def test_root_public_surface_is_an_exact_identity_shim(self):
        expected = canonical_exports(errors, requests, responses)
        self.assertEqual(api_contract.__all__, EXPECTED_EXPORTS)
        for name, value in expected.items():
            with self.subTest(name=name):
                self.assertIs(getattr(api_contract, name), value)
        self.assertFalse(hasattr(api_contract, "_field_error"))

    def test_package_relative_import_mode_preserves_identity(self):
        parent_name = "_api_contract_compat_parent"
        parent = types.ModuleType(parent_name)
        parent.__path__ = [str(ROOT)]
        sys.modules[parent_name] = parent
        try:
            root_module = importlib.import_module(f"{parent_name}.api_contract")
            errors_module = importlib.import_module(
                f"{parent_name}.easyuse_anima.api.errors"
            )
            requests_module = importlib.import_module(
                f"{parent_name}.easyuse_anima.api.requests"
            )
            responses_module = importlib.import_module(
                f"{parent_name}.easyuse_anima.api.responses"
            )
            expected = canonical_exports(
                errors_module,
                requests_module,
                responses_module,
            )
            self.assertEqual(root_module.__all__, EXPECTED_EXPORTS)
            for name, value in expected.items():
                with self.subTest(name=name):
                    self.assertIs(getattr(root_module, name), value)
        finally:
            for name in tuple(sys.modules):
                if name == parent_name or name.startswith(f"{parent_name}."):
                    sys.modules.pop(name, None)

    def test_api_imports_only_canonical_contract_owners(self):
        tree = ast.parse(API_PATH.read_text(encoding="utf-8"), filename=str(API_PATH))
        imports = [node for node in tree.body if isinstance(node, ast.ImportFrom)]
        modules = {
            node.module
            for node in imports
            if node.level == 1 and node.module is not None
        }
        self.assertTrue(
            {
                "easyuse_anima.api.errors",
                "easyuse_anima.api.requests",
                "easyuse_anima.api.responses",
            }.issubset(modules)
        )
        self.assertNotIn("api_contract", modules)


if __name__ == "__main__":
    unittest.main()
