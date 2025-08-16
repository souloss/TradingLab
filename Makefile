# ======================
# TradingLab Makefile
# ======================
.PHONY: install-backend install-frontend run-backend run-frontend dev clean


install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

install: install-backend install-frontend

run-backend:
	export PYTHONPATH=$(shell pwd)/backend && cd backend && uv run tradingapi/main.py

run-frontend:
	cd frontend && npm run dev

# 并发启动（后台）
dev:
	@$(MAKE) -j2 run-backend run-frontend


clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf backend/.venv frontend/node_modules