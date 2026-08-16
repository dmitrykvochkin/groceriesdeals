"""Launch a virtual Android device in Genymotion SaaS."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Start a Genymotion SaaS virtual device from a recipe."
    )
    parser.add_argument(
        "recipe_uuid",
        nargs="?",
        default=os.environ.get("GENYMOTION_RECIPE_UUID"),
        help="Recipe UUID (or set GENYMOTION_RECIPE_UUID).",
    )
    parser.add_argument(
        "--name",
        default="groceriesdeals",
        help="Instance name (default: groceriesdeals).",
    )
    parser.add_argument(
        "--max-run-duration",
        type=int,
        default=60,
        metavar="MINUTES",
        help="Automatically stop after this many minutes (default: 60).",
    )
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Return before the instance is fully started.",
    )
    parser.add_argument(
        "--adb-connect",
        action="store_true",
        help="Connect the started instance to ADB (requires Android SDK setup).",
    )
    return parser


def find_gmsaas() -> str:
    executable = shutil.which("gmsaas")
    if executable:
        return executable

    sibling = Path(sys.executable).with_name("gmsaas")
    if sibling.is_file():
        return str(sibling)

    raise RuntimeError("gmsaas is unavailable; run this command through `uv run`.")


def run_gmsaas(executable: str, arguments: Sequence[str]) -> dict[str, Any]:
    command = [executable, "--format", "json", *arguments]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        detail = completed.stderr.strip() or completed.stdout.strip() or "No output"
        raise RuntimeError(f"gmsaas failed: {detail}") from None

    if completed.returncode != 0 or result.get("exit_code", 0) != 0:
        error = result.get("error", {})
        detail = error.get("message") or result.get("exit_code_desc") or "Unknown error"
        raise RuntimeError(f"gmsaas failed: {detail}")

    return result


def instance_uuid_from(result: dict[str, Any]) -> str:
    instance = result.get("instance")
    if not isinstance(instance, dict) or not instance.get("uuid"):
        raise RuntimeError("gmsaas response did not contain an instance UUID.")
    return str(instance["uuid"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.recipe_uuid:
        parser.error("recipe_uuid is required (or set GENYMOTION_RECIPE_UUID)")
    if args.max_run_duration <= 0:
        parser.error("--max-run-duration must be greater than zero")
    if args.adb_connect and args.no_wait:
        parser.error("--adb-connect cannot be combined with --no-wait")
    if not os.environ.get("GENYMOTION_API_TOKEN"):
        parser.error("GENYMOTION_API_TOKEN is not set")

    try:
        executable = find_gmsaas()
        start_arguments = [
            "instances",
            "start",
            args.recipe_uuid,
            args.name,
            "--max-run-duration",
            str(args.max_run_duration),
        ]
        if args.no_wait:
            start_arguments.append("--no-wait")

        instance_uuid = instance_uuid_from(run_gmsaas(executable, start_arguments))
        print(f"Started Genymotion instance: {instance_uuid}")

        if args.adb_connect:
            adb_result = run_gmsaas(
                executable, ["instances", "adbconnect", instance_uuid]
            )
            adb_serial = adb_result.get("instance", {}).get("adb_serial")
            if adb_serial:
                print(f"ADB connected: {adb_serial}")

        print(f"Stop it with: uv run gmsaas instances stop {instance_uuid}")
        return 0
    except RuntimeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
