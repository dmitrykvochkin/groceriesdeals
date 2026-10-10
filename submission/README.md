# ChatGPT App Directory submission assets

Source files used to generate the kortingzoeker.com plugin distribution package.

## Contents

| File | Purpose |
| --- | --- |
| `config.json` | Listing metadata, MCP URL, localization, commerce flags |
| `review-cases.json` | Exactly 5 positive and 3 negative App Directory review cases |
| `README.md` | This guide |

## Generate the package

From the repository root:

```bash
make plugin-package
# or:
python3 scripts/generate_plugin_package.py
```

Optional overrides:

```bash
python3 scripts/generate_plugin_package.py \
  --mcp-url https://mcp.kortingzoeker.com/mcp \
  --demo-recording-url https://kortingzoeker.com/review/demo \
  --output-dir dist/plugin
```

This writes:

- `dist/plugin/` — unpacked Agent Plugins package
- `dist/kortingzoeker-chatgpt-plugin.zip` — uploadable ZIP

## Before uploading

1. Deploy the website pages (`/`, `/privacy`, `/terms`, `/support`) on HTTPS.
2. Point `mcp_url` at the public production MCP endpoint.
3. Replace `demo_recording_url` with a real reviewer-accessible walkthrough.
4. Re-run the generator and upload the ZIP in the OpenAI plugin submission portal.
5. Complete domain verification and tool scanning in the portal.

## Review-case expectations

Positive cases should trigger the listed tools and stay within returned Picnic deal data.
Negative cases should refuse ordering/payment, unsupported retailers, and unrelated tasks without inventing grocery-tool behavior.
