.PHONY: help up plugin-package

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-16s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

up: ## Start MCP HTTP (:8438) and landing (:3438)
	@./scripts/dev-up.sh

plugin-package: ## Generate ChatGPT App Directory plugin ZIP under dist/
	@if command -v uv >/dev/null 2>&1; then uv run python scripts/generate_plugin_package.py; else python3 scripts/generate_plugin_package.py; fi
