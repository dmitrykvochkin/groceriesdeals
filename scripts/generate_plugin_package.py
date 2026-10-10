#!/usr/bin/env python3
"""Generate the ChatGPT/Codex App Directory distribution package."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "submission" / "config.json"
DEFAULT_REVIEW_CASES = ROOT / "submission" / "review-cases.json"
DEFAULT_OUTPUT_DIR = ROOT / "dist" / "plugin"
DEFAULT_ZIP_PATH = ROOT / "dist" / "kortingzoeker-chatgpt-plugin.zip"

ONBOARDING_SKILL = """---
name: get-started
description: Explain how to use kortingzoeker.com for Picnic deals, grocery lists, and meal ideas.
---

# Get started with kortingzoeker.com

Use this skill when the user asks how the plugin works or what it can do.

## What it does

- Lists currently supported Dutch supermarket deal sources.
- Fetches current Picnic deals.
- Helps build budget grocery lists and meal ideas from those deals.

## What it does not do

- Place supermarket orders
- Process payments
- Guarantee stock or final checkout prices

## Suggested first prompts

1. "Welke supermarkten ondersteunt kortingzoeker.com?"
2. "Welke fruitaanbiedingen heeft Picnic momenteel?"
3. "Maak een gezonde boodschappenlijst voor 3 avondmaaltijden onder €40 met actuele Picnic-aanbiedingen."

Always prefer tool results over invented prices. Remind the user to verify the final basket with the retailer.
"""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require_review_cases(cases: dict[str, Any]) -> None:
    positive = cases.get("positive")
    negative = cases.get("negative")
    if not isinstance(positive, list) or len(positive) != 5:
        raise SystemExit("review-cases.json must contain exactly 5 positive cases")
    if not isinstance(negative, list) or len(negative) != 3:
        raise SystemExit("review-cases.json must contain exactly 3 negative cases")

    for index, case in enumerate(positive, start=1):
        for field in ("description", "prompt", "tools_triggered", "expected_behavior"):
            if not str(case.get(field, "")).strip():
                raise SystemExit(f"positive case {index} is missing {field}")
    for index, case in enumerate(negative, start=1):
        for field in ("description", "prompt"):
            if not str(case.get(field, "")).strip():
                raise SystemExit(f"negative case {index} is missing {field}")


def copy_asset(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"Asset not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build_manifest(
    config: dict[str, Any],
    review_cases: dict[str, Any],
    *,
    mcp_url: str,
    demo_recording_url: str,
) -> dict[str, Any]:
    return {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": config["name"],
        "version": config["version"],
        "description": config["description"],
        "author": config["author"],
        "homepage": config["homepage"],
        "repository": config["repository"],
        "license": config["license"],
        "keywords": config["keywords"],
        "extensions": {
            "com.openai": {
                "interface": {
                    "displayName": config["display_name"],
                    "shortDescription": config["short_description"],
                    "longDescription": config["long_description"],
                    "developerName": config["developer_name"],
                    "category": config["category"],
                    "capabilities": config["capabilities"],
                    "websiteURL": config["website_url"],
                    "supportURL": config["support_url"],
                    "privacyPolicyURL": config["privacy_policy_url"],
                    "termsOfServiceURL": config["terms_of_service_url"],
                    "defaultPrompt": config["default_prompts"],
                    "brandColor": config["brand_color"],
                    "brandColorDark": config["brand_color_dark"],
                    "composerIcon": "./assets/icon.png",
                    "logo": "./assets/logo.png",
                },
                "onboardingSkill": "./skills/get-started/SKILL.md",
                "review": {
                    "test_cases": {
                        "positive": review_cases["positive"],
                        "negative": review_cases["negative"],
                    },
                    "demo_recording_url": demo_recording_url,
                    "commerce": bool(config.get("commerce", False)),
                    "commerce_description": config["commerce_description"],
                },
                "publication": {
                    "countries": config["countries"],
                    "release_notes": config["release_notes"],
                    "translations": config.get("translations", {}),
                },
            }
        },
        "_generated": {
            "mcp_url": mcp_url,
            "note": "Companion mcp.json is generated next to this manifest.",
        },
    }


def build_mcp_config(config: dict[str, Any], mcp_url: str) -> dict[str, Any]:
    return {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        "mcpServers": {
            config["mcp_server_name"]: {
                "type": "streamable-http",
                "url": mcp_url,
            }
        },
    }


def write_package(
    config: dict[str, Any],
    review_cases: dict[str, Any],
    *,
    output_dir: Path,
    zip_path: Path,
    mcp_url: str,
    demo_recording_url: str,
) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    logo_source = ROOT / config["logo_source"]
    composer_source = ROOT / config["composer_icon_source"]
    copy_asset(logo_source, output_dir / "assets" / "logo.png")
    copy_asset(composer_source, output_dir / "assets" / "icon.png")

    skill_path = output_dir / "skills" / "get-started" / "SKILL.md"
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(ONBOARDING_SKILL, encoding="utf-8")

    manifest = build_manifest(
        config,
        review_cases,
        mcp_url=mcp_url,
        demo_recording_url=demo_recording_url,
    )
    # Keep the public manifest free of generator-only metadata.
    manifest.pop("_generated", None)

    (output_dir / "plugin.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "mcp.json").write_text(
        json.dumps(build_mcp_config(config, mcp_url), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "REVIEW_CASES.md").write_text(
        render_review_cases_markdown(review_cases),
        encoding="utf-8",
    )

    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output_dir).as_posix())


def render_review_cases_markdown(review_cases: dict[str, Any]) -> str:
    lines = [
        "# App Directory review cases",
        "",
        "Generated from `submission/review-cases.json`.",
        "",
        "## Positive cases",
        "",
    ]
    for index, case in enumerate(review_cases["positive"], start=1):
        lines.extend(
            [
                f"### {index}. {case['description']}",
                "",
                f"- Prompt: {case['prompt']}",
                f"- Tools: `{case['tools_triggered']}`",
                f"- Expected: {case['expected_behavior']}",
                "",
            ]
        )
    lines.extend(["## Negative cases", ""])
    for index, case in enumerate(review_cases["negative"], start=1):
        lines.extend(
            [
                f"### {index}. {case['description']}",
                "",
                f"- Prompt: {case['prompt']}",
                "",
            ]
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the kortingzoeker.com ChatGPT plugin distribution package."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--review-cases", type=Path, default=DEFAULT_REVIEW_CASES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--zip-path", type=Path, default=DEFAULT_ZIP_PATH)
    parser.add_argument(
        "--mcp-url",
        help="Override the production MCP URL written into mcp.json",
    )
    parser.add_argument(
        "--demo-recording-url",
        help="Override the reviewer demo recording URL",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_json(args.config)
    review_cases = load_json(args.review_cases)
    require_review_cases(review_cases)

    mcp_url = args.mcp_url or config["mcp_url"]
    demo_recording_url = args.demo_recording_url or config["demo_recording_url"]

    write_package(
        config,
        review_cases,
        output_dir=args.output_dir,
        zip_path=args.zip_path,
        mcp_url=mcp_url,
        demo_recording_url=demo_recording_url,
    )

    print(f"Wrote package directory: {args.output_dir}")
    print(f"Wrote upload ZIP: {args.zip_path}")
    print(f"MCP URL: {mcp_url}")
    print(f"Demo recording URL: {demo_recording_url}")


if __name__ == "__main__":
    main()
