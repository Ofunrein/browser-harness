import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import admin
import daemon


class _Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _ExitedProcess:
    def poll(self):
        return 1


class _StaleSocket:
    def settimeout(self, _timeout):
        pass

    def connect(self, _path):
        pass

    def sendall(self, _data):
        pass

    def recv(self, _size):
        return b'{"error":"cdp disconnected"}\n'

    def close(self):
        pass


class AttachOnlyTests(unittest.TestCase):
    def test_chrome_beta_profile_is_preferred(self):
        self.assertIn("Google/Chrome Beta", str(daemon.PROFILES[0]))

    def test_stale_profile_is_skipped_for_live_profile(self):
        with tempfile.TemporaryDirectory() as root:
            stale = Path(root) / "stale"
            live = Path(root) / "live"
            stale.mkdir()
            live.mkdir()
            (stale / "DevToolsActivePort").write_text("1111\n/devtools/browser/stale\n")
            (live / "DevToolsActivePort").write_text("2222\n/devtools/browser/live\n")

            def connect(address, timeout):
                if address[1] == 1111:
                    raise ConnectionRefusedError()
                return _Connection()

            with patch.object(daemon, "PROFILES", [stale, live]), \
                 patch.object(daemon.socket, "create_connection", side_effect=connect), \
                 patch.dict(os.environ, {"BU_ATTACH_TIMEOUT": "0"}, clear=False):
                os.environ.pop("BU_CDP_WS", None)
                self.assertEqual(
                    daemon.get_ws_url(),
                    "ws://127.0.0.1:2222/devtools/browser/live",
                )

    def test_missing_endpoint_fails_without_browser_action(self):
        with tempfile.TemporaryDirectory() as root, \
             patch.object(daemon, "PROFILES", [Path(root)]), \
             patch.dict(os.environ, {"BU_ATTACH_TIMEOUT": "0"}, clear=False):
            os.environ.pop("BU_CDP_WS", None)
            with self.assertRaisesRegex(RuntimeError, "attach-only"):
                daemon.get_ws_url()

    def test_daemon_failure_never_opens_permission_ui(self):
        self.assertFalse(hasattr(admin, "_open_chrome_inspect"))
        with patch.object(admin, "daemon_alive", return_value=False), \
             patch.object(admin, "_log_tail", return_value="attach failed"), \
             patch("subprocess.Popen", return_value=_ExitedProcess()):
            with self.assertRaisesRegex(RuntimeError, "attach-only mode"):
                admin.ensure_daemon(wait=0)

    def test_unhealthy_shared_daemon_is_not_recycled(self):
        with patch.object(admin, "daemon_alive", return_value=True), \
             patch.object(admin.socket, "socket", return_value=_StaleSocket()), \
             patch.object(admin, "restart_daemon") as restart:
            with self.assertRaisesRegex(RuntimeError, "not recycled"):
                admin.ensure_daemon(wait=0)
            restart.assert_not_called()


if __name__ == "__main__":
    unittest.main()
