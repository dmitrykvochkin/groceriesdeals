.PHONY: help up

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  %-10s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

up: ## Start MCP HTTP (:8438) and landing (:3438)
	@./scripts/dev-up.sh
