import asyncio
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_api_module():
    package_name = "easyuse_anima_profile_test_package"
    package = types.ModuleType(package_name)
    package.__path__ = [str(ROOT)]
    sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(
        f"{package_name}.api",
        ROOT / "api.py",
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RouteRegistry:
    def __init__(self):
        self.handlers = {}

    def get(self, path):
        def register(handler):
            self.handlers[path] = handler
            return handler

        return register

    def post(self, path):
        return self.get(path)


class JsonRequest:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload


def load_api_routes():
    routes = RouteRegistry()
    fake_server = types.ModuleType("server")
    fake_server.PromptServer = type(
        "PromptServer",
        (),
        {"instance": types.SimpleNamespace(routes=routes)},
    )
    fake_aiohttp = types.ModuleType("aiohttp")
    fake_aiohttp.web = types.SimpleNamespace(
        json_response=lambda payload, status=200: {"payload": payload, "status": status},
    )
    with patch.dict(sys.modules, {"server": fake_server, "aiohttp": fake_aiohttp}):
        api = load_api_module()
    return api, routes


class LoraProfileStorageTests(unittest.TestCase):
    def test_api_import_tolerates_prompt_server_without_instance(self):
        fake_server = types.ModuleType("server")
        fake_server.PromptServer = type("PromptServer", (), {})
        fake_aiohttp = types.ModuleType("aiohttp")
        fake_aiohttp.web = types.SimpleNamespace()

        with patch.dict(sys.modules, {"server": fake_server, "aiohttp": fake_aiohttp}):
            api = load_api_module()

        self.assertIsNone(api.routes)

    def test_save_and_load_lora_profile_set(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(api, "LORA_PROFILE_DIR", Path(tmp)):
                saved = api._save_lora_profile(
                    "style:preset",
                    {
                        "profile_count": "2",
                        "profile_index": 5,
                        "profile_data": {
                            "1": {"name": "Old name", "style_prompt": "@a", "loras": []},
                            "2": {
                                "style_prompt": "@b",
                                "loras": [{"name": "foo.safetensors", "strength": 0.8}],
                            },
                        },
                    },
                )

                self.assertEqual(saved["name"], "style_preset")
                self.assertEqual(saved["profile_count"], 2)
                self.assertEqual(saved["profile_index"], 1)
                self.assertNotIn("name", saved["profile_data"]["1"])
                self.assertTrue((Path(tmp) / "style_preset.json").is_file())

                profiles = api._list_lora_profiles()
                self.assertEqual([profile["name"] for profile in profiles], ["style_preset"])

                loaded = api._load_lora_profile("style_preset")
                self.assertEqual(loaded["profile_data"]["2"]["style_prompt"], "@b")
                self.assertEqual(loaded["profile_data"]["2"]["loras"][0]["name"], "foo.safetensors")

    def test_filename_identity_collisions_require_explicit_overwrite(self):
        api = load_api_module()
        collision_cases = (
            ("foo?bar", "foo*bar", "foo_bar"),
            (f"{'t' * 80}a", f"{'t' * 80}b", "t" * 80),
            ("Portrait", "portrait", "Portrait"),
            ("Windows Name", "Windows Name. ", "Windows Name"),
        )

        for original_name, colliding_name, filename in collision_cases:
            with self.subTest(original_name=original_name, colliding_name=colliding_name):
                with tempfile.TemporaryDirectory() as tmp:
                    with patch.object(api, "LORA_PROFILE_DIR", Path(tmp)):
                        api._save_lora_profile(
                            original_name,
                            {"profile_data": {"1": {"style_prompt": "first"}}},
                        )
                        for overwrite_kwargs in ({}, {"overwrite": False}):
                            with self.subTest(overwrite_kwargs=overwrite_kwargs):
                                with self.assertRaisesRegex(FileExistsError, "Profile already exists"):
                                    api._save_lora_profile(
                                        colliding_name,
                                        {"profile_data": {"1": {"style_prompt": "second"}}},
                                        **overwrite_kwargs,
                                    )

                        preserved = api._load_lora_profile(colliding_name)
                        self.assertEqual(preserved["profile_data"]["1"]["style_prompt"], "first")
                        self.assertEqual(preserved["name"], filename)

                        overwritten = api._save_lora_profile(
                            colliding_name,
                            {"profile_data": {"1": {"style_prompt": "second"}}},
                            overwrite=True,
                        )
                        self.assertEqual(overwritten["name"], filename)
                        self.assertEqual(
                            api._load_lora_profile(original_name)["profile_data"]["1"]["style_prompt"],
                            "second",
                        )
                        self.assertEqual(
                            [path.name for path in Path(tmp).glob("*.json")],
                            [f"{filename}.json"],
                        )

    def test_windows_reserved_profile_names_are_rejected(self):
        api = load_api_module()
        for name in ("CON", "con.txt", "LPT9", "COM¹.txt", "aux."):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "reserved on Windows"):
                api._sanitize_lora_profile_name(name)

    def test_profile_paths_remain_within_the_configured_root(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for name in ("../outside", r"C:\outside", r"\\server\share\outside"):
                with self.subTest(name=name):
                    self.assertEqual(api._lora_profile_path(name, root).parent, root)

    def test_empty_lora_profile_name_is_rejected(self):
        api = load_api_module()
        with self.assertRaises(ValueError):
            api._sanitize_lora_profile_name(" ")


    def test_list_loras_refreshes_folder_paths_cache_and_normalizes_names(self):
        api = load_api_module()
        clear_calls = []
        fake_folder_paths = types.SimpleNamespace(
            filename_list_cache={"loras": "stale", "checkpoints": "keep"},
            cache_helper=types.SimpleNamespace(
                active=False,
                clear=lambda: clear_calls.append("clear"),
            ),
            get_filename_list=lambda category: [
                "None",
                "style\\한글.safetensors",
                "style/한글.safetensors",
                "",
                "extra/foo.pt",
            ],
        )

        with patch.dict(sys.modules, {"folder_paths": fake_folder_paths}):
            loras = api._list_loras()

        self.assertEqual(loras, ["style\\한글.safetensors", "extra/foo.pt"])
        self.assertNotIn("loras", fake_folder_paths.filename_list_cache)
        self.assertEqual(fake_folder_paths.filename_list_cache["checkpoints"], "keep")
        self.assertEqual(clear_calls, ["clear"])

    def test_fix_lora_profile_payload_matches_unique_file_name(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            lora_path = Path(tmp) / "foo.safetensors"
            lora_path.write_bytes(b"local lora")

            def get_full_path(category, name):
                if category == "loras" and str(name).replace("\\", "/") == "local/foo.safetensors":
                    return str(lora_path)
                return None

            fake_folder_paths = types.SimpleNamespace(
                filename_list_cache={},
                get_filename_list=lambda category: ["local/foo.safetensors"] if category == "loras" else [],
                get_full_path=get_full_path,
            )

            with patch.dict(sys.modules, {"folder_paths": fake_folder_paths}):
                fixed = api._fix_lora_profile_payload({
                    "profile_count": 1,
                    "profile_index": 1,
                    "profile_data": {
                        "1": {
                            "style_prompt": "",
                            "loras": [{"name": "shared/foo.safetensors", "strength": 0.8}],
                        },
                    },
                })

        lora = fixed["profile_data"]["1"]["loras"][0]
        self.assertEqual(lora["name"], "local/foo.safetensors")
        self.assertNotIn("sha256", lora)
        self.assertEqual(fixed["fixed"][0]["reason"], "file")
        self.assertEqual(fixed["unresolved"], [])

    def test_fix_lora_profile_payload_does_not_match_by_hash(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            lora_path = Path(tmp) / "bar.safetensors"
            lora_path.write_bytes(b"renamed local lora")

            def get_full_path(category, name):
                if category == "loras" and str(name).replace("\\", "/") == "local/bar_changed.safetensors":
                    return str(lora_path)
                return None

            fake_folder_paths = types.SimpleNamespace(
                filename_list_cache={},
                get_filename_list=lambda category: ["local/bar_changed.safetensors"] if category == "loras" else [],
                get_full_path=get_full_path,
            )

            with patch.dict(sys.modules, {"folder_paths": fake_folder_paths}):
                fixed = api._fix_lora_profile_payload({
                    "profile_count": 1,
                    "profile_index": 1,
                    "profile_data": {
                        "1": {
                            "style_prompt": "",
                            "loras": [{"name": "shared/not_the_same.safetensors", "sha256": "abc123"}],
                        },
                    },
                })

        lora = fixed["profile_data"]["1"]["loras"][0]
        self.assertEqual(lora["name"], "shared/not_the_same.safetensors")
        self.assertEqual(lora["sha256"], "abc123")
        self.assertEqual(fixed["fixed"], [])
        self.assertEqual(fixed["unresolved"], [{"profile": "1", "name": "shared/not_the_same.safetensors"}])

    def test_fix_lora_profile_payload_leaves_ambiguous_file_name_unresolved(self):
        api = load_api_module()
        fake_folder_paths = types.SimpleNamespace(
            filename_list_cache={},
            get_filename_list=lambda category: ["a/foo.safetensors", "b/foo.safetensors"] if category == "loras" else [],
            get_full_path=lambda category, name: None,
        )

        with patch.dict(sys.modules, {"folder_paths": fake_folder_paths}):
            fixed = api._fix_lora_profile_payload({
                "profile_count": 1,
                "profile_index": 1,
                "profile_data": {
                    "1": {
                        "style_prompt": "",
                        "loras": [{"name": "shared/foo.safetensors"}],
                    },
                },
            })

        lora = fixed["profile_data"]["1"]["loras"][0]
        self.assertEqual(lora["name"], "shared/foo.safetensors")
        self.assertEqual(fixed["fixed"], [])
        self.assertEqual(fixed["unresolved"], [{"profile": "1", "name": "shared/foo.safetensors"}])

    def test_fix_lora_profile_payload_skips_lora_list_when_current_paths_exist(self):
        api = load_api_module()
        with tempfile.TemporaryDirectory() as tmp:
            lora_path = Path(tmp) / "exists.safetensors"
            lora_path.write_bytes(b"local lora")

            def get_filename_list(_category):
                raise AssertionError("LoRA list should not be scanned when paths already exist")

            def get_full_path(category, name):
                if category == "loras" and str(name).replace("\\", "/") == "local/exists.safetensors":
                    return str(lora_path)
                return None

            fake_folder_paths = types.SimpleNamespace(
                filename_list_cache={},
                get_filename_list=get_filename_list,
                get_full_path=get_full_path,
            )

            with patch.dict(sys.modules, {"folder_paths": fake_folder_paths}):
                fixed = api._fix_lora_profile_payload({
                    "profile_count": 1,
                    "profile_index": 1,
                    "profile_data": {
                        "1": {
                            "style_prompt": "",
                            "loras": [{"name": "local/exists.safetensors"}],
                        },
                    },
                })

        self.assertEqual(fixed["fixed"], [])
        self.assertEqual(fixed["unresolved"], [])
        self.assertEqual(fixed["missing"], 0)


class LoraProfileApiRouteTests(unittest.TestCase):
    PATH = "/easyuse_anima/lora_profiles/save"
    BASE_PAYLOAD = {"name": "Saved", "profile_data": {}}

    def test_profile_overwrite_accepts_json_booleans_and_defaults_false(self):
        api, routes = load_api_routes()
        handler = routes.handlers[self.PATH]
        overwrite_cases = (
            ({}, False),
            ({"overwrite": False}, False),
            ({"overwrite": True}, True),
        )

        for overwrite_payload, expected in overwrite_cases:
            with self.subTest(overwrite=overwrite_payload):
                with patch.object(
                    api,
                    "_save_lora_profile",
                    return_value={"name": "Saved"},
                ) as operation:
                    response = asyncio.run(
                        handler(JsonRequest({**self.BASE_PAYLOAD, **overwrite_payload}))
                    )

                self.assertEqual(response["status"], 200)
                self.assertIs(operation.call_args.kwargs["overwrite"], expected)

    def test_profile_overwrite_rejects_non_boolean_json_values(self):
        api, routes = load_api_routes()
        handler = routes.handlers[self.PATH]

        for overwrite in ("false", "true", 0, 1, "", None, [], {}):
            with self.subTest(overwrite=overwrite):
                with patch.object(api, "_save_lora_profile") as operation:
                    response = asyncio.run(
                        handler(JsonRequest({**self.BASE_PAYLOAD, "overwrite": overwrite}))
                    )

                self.assertEqual(response["status"], 400)
                self.assertEqual(
                    response["payload"],
                    {"status": "error", "message": "overwrite must be a JSON boolean"},
                )
                operation.assert_not_called()

    def test_profile_conflict_uses_existing_error_json_shape_with_409_status(self):
        api, routes = load_api_routes()
        handler = routes.handlers[self.PATH]

        with patch.object(
            api,
            "_save_lora_profile",
            side_effect=FileExistsError("Profile already exists"),
        ):
            response = asyncio.run(handler(JsonRequest(self.BASE_PAYLOAD)))

        self.assertEqual(response["status"], 409)
        self.assertEqual(
            response["payload"],
            {"status": "error", "message": "Profile already exists"},
        )


class AutocompleteApiRouteTests(unittest.TestCase):
    def test_autocomplete_route_forwards_valid_limits_and_uses_resolver_fallback(self):
        class RouteRegistry:
            def __init__(self):
                self.get_handlers = {}

            def get(self, path):
                def register(handler):
                    self.get_handlers[path] = handler
                    return handler

                return register

            def post(self, path):
                return self.get(path)

        routes = RouteRegistry()
        fake_server = types.ModuleType("server")
        fake_server.PromptServer = type(
            "PromptServer",
            (),
            {"instance": types.SimpleNamespace(routes=routes)},
        )
        fake_aiohttp = types.ModuleType("aiohttp")
        fake_aiohttp.web = types.SimpleNamespace(
            json_response=lambda payload, status=200: {"payload": payload, "status": status},
        )

        with patch.dict(sys.modules, {"server": fake_server, "aiohttp": fake_aiohttp}):
            api = load_api_module()

        calls = []

        def search(query, *, limit, path, category):
            calls.append({"query": query, "limit": limit, "path": path, "category": category})
            return {"results": [{"tag": f"match {index}"} for index in range(limit)]}

        handler = routes.get_handlers["/easyuse_anima/autocomplete"]
        with (
            patch.object(api, "resolve_autocomplete_limit", return_value=51),
            patch.object(api, "resolve_autocomplete_source", return_value="test_source"),
            patch.object(
                api,
                "resolve_autocomplete_source_path",
                return_value=("test_source", Path("tags.csv")),
            ),
            patch.object(api, "search_autocomplete", side_effect=search),
        ):
            for raw_limit, expected_limit in (("51", 51), ("100", 100), ("bad", 51)):
                with self.subTest(raw_limit=raw_limit):
                    response = asyncio.run(
                        handler(types.SimpleNamespace(query={"q": "match", "limit": raw_limit}))
                    )
                    self.assertEqual(response["status"], 200)
                    self.assertEqual(len(response["payload"]["results"]), expected_limit)

        self.assertEqual([call["limit"] for call in calls], [51, 100, 51])


if __name__ == "__main__":
    unittest.main()
