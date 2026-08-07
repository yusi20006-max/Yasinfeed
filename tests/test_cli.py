import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
import io
import subprocess
from yasinfeed.cli.main import main, mask_sensitive_data


class TestCLIExtended(unittest.TestCase):

    def setUp(self):
        self._orig_argv = sys.argv

    def tearDown(self):
        sys.argv = self._orig_argv

    def test_version_subcommand_via_subprocess(self):
        r = subprocess.run(
            [sys.executable, "-m", "yasinfeed.cli.main", "version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("YasinFeed CLI v0.1", r.stdout)
        self.assertIn("YasinFeed Engine v0.1.0", r.stdout)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_version_subcommand_direct(self, mock_stdout):
        sys.argv = ["yasinfeed", "version"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed CLI v0.1", output)
        self.assertIn("YasinFeed Engine v0.1.0", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.load_config")
    def test_config_subcommand(self, mock_load_config, mock_stdout):
        mock_load_config.return_value = {
            "app": {"name": "YasinFeed"},
            "rewrite": {
                "openai": {
                    "api_key": "sk-secret-key-12345",
                    "model": "gpt-3.5-turbo"
                }
            }
        }
        sys.argv = ["yasinfeed", "config"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed", output)
        self.assertIn("********", output)
        self.assertNotIn("sk-secret-key-12345", output)

    def test_mask_sensitive_data(self):
        raw_data = {
            "api_key": "somekey",
            "password": "somepassword",
            "token": "sometoken",
            "secret": "somesecret",
            "safe_key": "safestuff",
            "nested": {
                "github_token": "githubtoken"
            },
            "list_data": [
                {"db_password": "pass"}
            ],
            "non_string": None,
            "port": 8000
        }
        masked = mask_sensitive_data(raw_data)
        self.assertEqual(masked["api_key"], "********")
        self.assertEqual(masked["password"], "********")
        self.assertEqual(masked["token"], "********")
        self.assertEqual(masked["secret"], "********")
        self.assertEqual(masked["safe_key"], "********")  # because it ends in "key"
        self.assertEqual(masked["nested"]["github_token"], "********")
        self.assertEqual(masked["list_data"][0]["db_password"], "********")
        self.assertEqual(masked["port"], 8000)
        self.assertIsNone(masked["non_string"])

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_doctor_subcommand(self, mock_stdout):
        sys.argv = ["yasinfeed", "doctor"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed Doctor Diagnostic", output)
        self.assertIn("Python Version", output)
        self.assertIn("Required Dependencies", output)
        self.assertIn("Configuration Availability", output)
        self.assertIn("Storage/Database Status", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.urlopen")
    @patch("yasinfeed.cli.main.get_stored_pid")
    def test_status_stopped(self, mock_get_stored_pid, mock_urlopen, mock_stdout):
        mock_get_stored_pid.return_value = 0
        mock_urlopen.side_effect = Exception("API down")
        sys.argv = ["yasinfeed", "status"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed Engine status: STOPPED", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.urlopen")
    @patch("yasinfeed.cli.main.get_stored_pid")
    @patch("yasinfeed.cli.main.is_pid_running")
    def test_status_running_api_unresponsive(self, mock_is_pid_running, mock_get_stored_pid, mock_urlopen, mock_stdout):
        mock_get_stored_pid.return_value = 1234
        mock_is_pid_running.return_value = True
        mock_urlopen.side_effect = Exception("API down")
        sys.argv = ["yasinfeed", "status"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed Engine status: RUNNING (PID: 1234, but API is unresponsive)", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.urlopen")
    @patch("yasinfeed.cli.main.get_stored_pid")
    def test_status_running_api_active(self, mock_get_stored_pid, mock_urlopen, mock_stdout):
        mock_get_stored_pid.return_value = 1234
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"status": "ok", "system": {"pid": 1234, "uptime_seconds": 3600}, "checks": {"storage": {"status": "healthy", "message": "Database connection verified"}}, "metrics": {"api_requests": 42}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        sys.argv = ["yasinfeed", "status"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed Engine status: RUNNING (API is active)", output)
        self.assertIn("PID: 1234", output)
        self.assertIn("Uptime: 3600 seconds", output)
        self.assertIn("storage: HEALTHY (Database connection verified)", output)
        self.assertIn("api_requests: 42", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.get_stored_pid")
    @patch("yasinfeed.cli.main.is_pid_running")
    @patch("subprocess.Popen")
    def test_start_command_already_running(self, mock_popen, mock_is_pid_running, mock_get_stored_pid, mock_stdout):
        mock_get_stored_pid.return_value = 5555
        mock_is_pid_running.return_value = True
        sys.argv = ["yasinfeed", "start"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("YasinFeed Engine is already running (PID: 5555)", output)
        mock_popen.assert_not_called()

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.get_stored_pid")
    @patch("yasinfeed.cli.main.is_pid_running")
    @patch("subprocess.Popen")
    @patch("yasinfeed.cli.main.urlopen")
    @patch("builtins.open", new_callable=mock_open)
    def test_start_command_success(self, mock_file, mock_urlopen, mock_popen, mock_is_pid_running, mock_get_stored_pid, mock_stdout):
        mock_get_stored_pid.return_value = 0
        mock_is_pid_running.return_value = True

        mock_process = MagicMock()
        mock_process.pid = 7777
        mock_popen.return_value = mock_process

        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        sys.argv = ["yasinfeed", "start"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Starting YasinFeed Engine...", output)
        self.assertIn("Engine process spawned with PID 7777", output)
        self.assertIn("YasinFeed Engine started successfully (PID: 7777)", output)
        mock_file.assert_called_with("yasinfeed.pid", "w")

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("yasinfeed.cli.main.get_stored_pid")
    @patch("yasinfeed.cli.main.is_pid_running")
    @patch("os.kill")
    @patch("os.path.exists")
    @patch("os.remove")
    def test_stop_command_success(self, mock_remove, mock_exists, mock_kill, mock_is_pid_running, mock_get_stored_pid, mock_stdout):
        mock_get_stored_pid.return_value = 8888
        mock_is_pid_running.side_effect = [True, False]  # running when stop begins, stopped after SIGTERM
        mock_exists.return_value = True

        sys.argv = ["yasinfeed", "stop"]
        main()
        output = mock_stdout.getvalue()
        self.assertIn("Stopping YasinFeed Engine safely (PID: 8888)", output)
        self.assertIn("YasinFeed Engine stopped cleanly", output)
        mock_kill.assert_any_call(8888, 15)  # SIGTERM
        mock_remove.assert_called_with("yasinfeed.pid")

    @patch("sys.stderr", new_callable=io.StringIO)
    def test_invalid_command_handling(self, mock_stderr):
        sys.argv = ["yasinfeed", "nonexistent-command"]
        with self.assertRaises(SystemExit):
            main()
        self.assertIn("invalid choice", mock_stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
