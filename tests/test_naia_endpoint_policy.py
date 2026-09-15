import asyncio
import json
import os
import socket
import unittest
from dataclasses import FrozenInstanceError
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

import requests
from requests.adapters import HTTPAdapter
from requests.models import Response

from easyuse_anima import bootstrap
from easyuse_anima.api.errors import ApiContractError
from easyuse_anima.api.requests import json_string, parse_json_object
from easyuse_anima.api.routes.settings import build_settings_handlers
from easyuse_anima.infrastructure.comfy import wiring
from easyuse_anima.naia import client
from easyuse_anima.naia.endpoint_policy import (
    DEFAULT_NAIA_ENDPOINTS,
    parse_naia_endpoint_policy,
)
from easyuse_anima.settings import repository, service
from easyuse_anima.settings.schema import DEFAULT_SETTINGS


class NaiaEndpointPolicyTests(unittest.TestCase):
    def setUp(self):
        policy_patch = patch.object(
            client, "resolve_naia_endpoints", return_value=DEFAULT_NAIA_ENDPOINTS,
        )
        self.policy = policy_patch.start()
        self.addCleanup(policy_patch.stop)

    def test_unapproved_destinations_never_reach_dns_or_transport(self):
        targets = (
            ("169.254.169.254", 80), ("metadata.google.internal", 80),
            ("192.168.0.2", 7243), ("127.0.0.1", 80), ("::1", 8188),
            ("2130706433", 7243), ("0x7f000001", 7243),
            ("[::ffff:169.254.169.254]", 80), ("outside.invalid", 7243),
        )
        with patch.object(requests, "Session") as session, patch.object(socket, "getaddrinfo") as dns:
            for host, port in targets:
                with self.subTest(host=host, port=port), self.assertRaisesRegex(RuntimeError, "not approved"):
                    client._post_random(host, port, {}, allow_remote_api=True)
            session.assert_not_called()
            dns.assert_not_called()

    def test_policy_accepts_exact_local_lan_and_pinned_hostname_endpoints(self):
        self.policy.return_value = parse_naia_endpoint_policy(json.dumps([
            {"host": "192.168.0.2", "port": 7243},
            {"host": "naia.example", "port": 7243, "address": "192.168.0.2"},
            {"host": "[::1]", "port": 7244},
        ]))
        cases = (
            ("LOCALHOST", 7243, False, "127.0.0.1"),
            ("[::1]", 7244, False, "[::1]"),
            ("192.168.0.2", 7243, True, "192.168.0.2"),
            ("NAIA.EXAMPLE.", 7243, True, "192.168.0.2"),
        )
        for host, port, remote, address in cases:
            self.assertEqual(
                client._build_naia_random_url(host, port, remote),
                f"http://{address}:{port}/api/comfyui/random",
            )
        with self.assertRaisesRegex(RuntimeError, "Remote NAIA API access is disabled"):
            client._build_naia_random_url("naia.example", 7243, False)
        with self.assertRaisesRegex(RuntimeError, "not approved"):
            client._build_naia_random_url("naia.example", 80, True)

    def test_invalid_operator_policy_is_rejected_without_echoing_values(self):
        cases = (
            "operator-secret", '{}', '["operator-secret"]',
            '[{"host":"naia.example","port":7243}]',
            '[{"host":"127.0.0.1","port":80,"address":"192.168.0.2"}]',
            '[{"host":"localhost","port":80,"address":"192.168.0.2"}]',
        )
        entries = [
            {"host": host, "port": 7243} for host in (
                "169.254.169.254", "fe80::1", "0.0.0.0", "224.0.0.1",
                "http://127.0.0.1", "host/evil", "host@evil", "fe80::1%eth0",
            )
        ] + [{"host": "127.0.0.1", "port": port} for port in (0, 65536, True, "7243")]
        for raw in (*cases, *(json.dumps([entry]) for entry in entries)):
            with self.subTest(raw=raw), self.assertRaises(ValueError) as raised:
                parse_naia_endpoint_policy(raw)
            self.assertEqual(str(raised.exception), "Invalid operator NAIA endpoint policy.")

    def test_settings_route_and_comfy_overlay_cannot_grant_network_permission(self):
        values = dict(DEFAULT_SETTINGS)

        async def run_inline(fn, *args):
            return fn(*args)

        def save_in_memory(key, value):
            self.assertIn(key, DEFAULT_SETTINGS)
            values[key] = str(value)
            return {"status": "ok"}

        _, handler = build_settings_handlers(
            parse_json_object=parse_json_object, json_string=json_string,
            contract_error_type=ApiContractError, contract_error_response=lambda e: {"error": str(e)},
            run_file_io=run_inline, get_settings_payload=lambda: values,
            save_setting_payload=save_in_memory, unknown_setting_error_type=KeyError,
            unknown_setting_response=lambda: {"error": "key"}, json_response=lambda d: d,
        )

        class SyntheticRequest:
            headers = {"Host": "comfy.test:8188", "Origin": "http://comfy.test:8188", "Content-Type": "application/json"}
            remote = "192.0.2.25"

            def __init__(self, key, value):
                self.payload = {"key": key, "value": value}

            async def json(self):
                return self.payload

        for key, value in (("naia.host", "169.254.169.254"), ("naia.port", 80), ("naia.allow_remote_api", True)):
            self.assertEqual(asyncio.run(handler(SyntheticRequest(key, value))), {"status": "ok"})
        overlay = repository._apply_comfy_settings(dict(DEFAULT_SETTINGS), {
            "EasyUseAnima.NAIA.Host": "169.254.169.254", "EasyUseAnima.NAIA.Port": 80,
            "EasyUseAnima.NAIA.AllowRemoteAPI": True,
        })
        for source in (values, overlay):
            with patch.object(service, "get_settings", return_value=source):
                selected = service.resolve_naia_settings()
            with patch.object(requests, "Session") as session, self.assertRaisesRegex(RuntimeError, "not approved"):
                client._post_random(selected["host"], selected["port"], {}, selected["allow_remote_api"])
            session.assert_not_called()

    def test_pinned_transport_does_not_use_dns_proxies_or_ambient_credentials(self):
        self.policy.return_value = parse_naia_endpoint_policy(
            '[{"host":"naia.example","port":7243,"address":"192.168.0.2"}]'
        )
        sent = []

        def send(adapter, request, **kwargs):
            sent.append((request, kwargs))
            response = Response()
            response.status_code = 200
            response.raw = BytesIO(b'{"ok":true}')
            return response

        with (
            patch.dict(os.environ, {"HTTP_PROXY": "http://proxy.invalid:3128", "NO_PROXY": ""}),
            patch("requests.sessions.get_netrc_auth") as netrc,
            patch.object(socket, "getaddrinfo") as dns,
            patch.object(HTTPAdapter, "send", send),
        ):
            self.assertEqual(client._post_random("naia.example", 7243, {}, True), {"ok": True})
        netrc.assert_not_called()
        dns.assert_not_called()
        request, kwargs = sent[0]
        self.assertEqual(request.url, "http://192.168.0.2:7243/api/comfyui/random")
        self.assertEqual(request.headers["Host"], "naia.example:7243")
        self.assertNotIn("Authorization", request.headers)
        self.assertFalse(kwargs["proxies"])

    def test_response_errors_are_redacted_and_connections_closed(self):
        for status, payload in ((500, b'private-service-secret'), (200, b'private-service-secret'), (200, b'{"ok":false,"secret":"private-service-secret"}')):
            response = Response()
            response.status_code = status
            response.raw = BytesIO(payload)
            with patch.object(response, "close", wraps=response.close) as close, patch.object(HTTPAdapter, "send", return_value=response), self.assertRaises(RuntimeError) as raised:
                client._post_random("127.0.0.1", 7243, {})
            self.assertNotIn("private-service-secret", str(raised.exception))
            close.assert_called_once_with()
        with patch.object(HTTPAdapter, "send", side_effect=requests.ConnectionError("proxy-password")), self.assertRaises(RuntimeError) as raised:
            client._post_random("127.0.0.1", 7243, {})
        self.assertEqual(str(raised.exception), "[EasyUse Anima] NAIA API request failed.")

    def test_bootstrap_snapshot_is_immutable_and_invalid_config_disables_naia(self):
        with patch.dict(os.environ, {"EASYUSE_ANIMA_NAIA_ENDPOINTS": '[{"host":"192.168.0.2","port":7243}]'}):
            config = bootstrap._load_runtime_config()
        with self.assertRaises(FrozenInstanceError):
            config.naia_endpoints = ()
        with patch.dict(os.environ, {"EASYUSE_ANIMA_NAIA_ENDPOINTS": '[{"host":"192.168.0.3","port":7243}]'}), patch.object(wiring, "get_runtime", return_value=SimpleNamespace(config=config)):
            self.assertIn(("192.168.0.2", 7243, "192.168.0.2"), wiring.resolve_naia_endpoints())
            self.assertNotIn(("192.168.0.3", 7243, "192.168.0.3"), wiring.resolve_naia_endpoints())
        with patch.dict(os.environ, {"EASYUSE_ANIMA_NAIA_ENDPOINTS": "operator-secret"}), self.assertLogs("ComfyUI-EasyUseAnima", level="WARNING") as logs:
            invalid = bootstrap._load_runtime_config()
        self.assertEqual(invalid.naia_endpoints, ())
        self.assertNotIn("operator-secret", " ".join(logs.output))
        self.policy.return_value = invalid.naia_endpoints
        with self.assertRaisesRegex(RuntimeError, "not approved"):
            client._post_random("127.0.0.1", 7243, {})
