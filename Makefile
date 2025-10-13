# DEX Trading Telegram Bot Makefile

.PHONY: help install setup test start clean

help: ## Show this help message
	@echo "DEX Trading Telegram Bot - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	@echo "Installing dependencies..."
	pip install -r requirements.txt

setup: ## Setup configuration
	@echo "Setting up configuration..."
	python setup_config.py

test: ## Run tests
	@echo "Running tests..."
	python test_bot.py

start: ## Start the bot
	@echo "Starting DEX Trading Bot..."
	python start_bot.py

clean: ## Clean up temporary files
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete

dev: ## Start in development mode
	@echo "Starting in development mode..."
	PYTHONPATH=src python src/main.py

connectivity: ## Test exchange connectivity
	@echo "Testing exchange connectivity..."
	python test_production_connectivity.py

backup: ## Backup data
	@echo "Backing up data..."
	mkdir -p backups
	cp -r data/ backups/data_$(shell date +%Y%m%d_%H%M%S)/

logs: ## View logs
	@echo "Viewing logs..."
	tail -f logs/bot.log

status: ## Check bot status
	@echo "Checking bot status..."
	@if [ -f "logs/bot.log" ]; then \
		echo "Bot log exists"; \
		tail -5 logs/bot.log; \
	else \
		echo "No bot log found"; \
	fi
