import json
import os
import subprocess
import unittest
from unittest.mock import patch

from groceriesdeals.genymotion import instance_uuid_from, main, run_gmsaas


class GenymotionTests(unittest.TestCase):
    @patch("groceriesdeals.genymotion.subprocess.run")
    def test_run_gmsaas_requests_json_output(self, run) -> None:
        run.return_value = subprocess.CompletedProcess(
            [], 0, stdout=json.dumps({"exit_code": 0}), stderr=""
        )

        result = run_gmsaas("gmsaas", ["instances", "list"])

        self.assertEqual(result["exit_code"], 0)
        run.assert_called_once_with(
            ["gmsaas", "--format", "json", "instances", "list"],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_instance_uuid_is_extracted(self) -> None:
        result = {"instance": {"uuid": "instance-id"}, "exit_code": 0}

        self.assertEqual(instance_uuid_from(result), "instance-id")

    @patch.dict(os.environ, {"GENYMOTION_API_TOKEN": "secret"}, clear=True)
    @patch("groceriesdeals.genymotion.run_gmsaas")
    @patch("groceriesdeals.genymotion.find_gmsaas", return_value="gmsaas")
    def test_main_starts_with_a_bounded_duration(self, _find, run) -> None:
        run.return_value = {
            "instance": {"uuid": "instance-id"},
            "exit_code": 0,
        }

        exit_code = main(["recipe-id", "--max-run-duration", "30"])

        self.assertEqual(exit_code, 0)
        run.assert_called_once_with(
            "gmsaas",
            [
                "instances",
                "start",
                "recipe-id",
                "groceriesdeals",
                "--max-run-duration",
                "30",
            ],
        )


if __name__ == "__main__":
    unittest.main()
