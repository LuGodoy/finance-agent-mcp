# ==============================
# CONFIG
# ==============================
PYTHON=python3
VENV=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

# ==============================
# HELP
# ==============================
.PHONY: help
help:
	@echo "📦 Comandos disponíveis:"
	@echo " make setup       -> cria estrutura do projeto"
	@echo " make install     -> cria venv e instala dependências"
	@echo " make env         -> cria arquivos .env"
	@echo " make run         -> roda app Streamlit"
	@echo " make mcp         -> roda MCP Server"
	@echo " make list-models -> lista modelos disponíveis no Gemini"
	@echo " make test        -> roda testes"
	@echo " make lint        -> executa linter e formatador (Ruff)"
	@echo " make clean       -> limpa caches e logs"

# ==============================
# PROJECT STRUCTURE
# ==============================
.PHONY: setup
setup:
	@echo "🚀 Criando estrutura do projeto..."

	@mkdir -p app
	@mkdir -p database
	@mkdir -p llm
	@mkdir -p mcp_server/tools
	@mkdir -p shared
	@mkdir -p assets
	@mkdir -p tests
	@mkdir -p docs/screenshots
	@mkdir -p docs/diagrams
	@mkdir -p docs/gifs
	@mkdir -p utils

	@touch app/__init__.py app/main.py app/styles.css
	@touch database/__init__.py database/connection.py
	@touch llm/__init__.py llm/client_gemini.py llm/prompts.py

	@touch mcp_server/__init__.py
	@touch mcp_server/server.py
	@touch mcp_server/tools/__init__.py
	@touch mcp_server/tools/expense_items.py
	@touch mcp_server/tools/expense_summary.py

	@touch shared/__init__.py
	@touch shared/config_logging.py
	@touch shared/date_config.py

	@touch tests/__init__.py
	@touch tests/test_gemini_client.py tests/test_infra.py 
	@touch utils/__init__.py utils/list_models.py

	@touch assets/bot.png assets/user.png

	@touch README.md pyproject.toml LICENSE

	@echo "✅ Estrutura criada!"

# ==============================
# VENV + DEPENDENCIES
# ==============================
.PHONY: install
install:
	@echo "🐍 Criando ambiente virtual..."
	$(PYTHON) -m venv $(VENV)

	@echo "📦 Instalando dependências do pyproject.toml..."
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

	@echo "✅ Ambiente pronto!"

# ==============================
# ENV FILES
# ==============================
.PHONY: env
env:
	@echo "📄 Criando .env local a partir do .env.example..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Arquivo .env criado! Preencha GEMINI_API_KEY antes de rodar."; \
	else \
		echo "⚠️  Arquivo .env já existe. Nenhuma alteração feita."; \
	fi

# ==============================
# WAIT FOR DB (Docker only)
# ==============================
.PHONY: wait-db
wait-db:
	@if docker ps --filter name=finance_mysql --filter status=running --format "{{.Names}}" 2>/dev/null | grep -q finance_mysql; then \
		echo "⏳ Aguardando MySQL ficar saudável..."; \
		until [ "$$(docker inspect --format='{{.State.Health.Status}}' finance_mysql 2>/dev/null)" = "healthy" ]; do \
			printf "."; sleep 2; \
		done; \
		echo " ✅ Banco pronto!"; \
	fi

# ==============================
# RUN APPLICATION
# ==============================
.PHONY: run
run: wait-db
	@echo "🚀 Iniciando Streamlit..."
	$(PY) -m streamlit run app/main.py

# ==============================
# RUN MCP SERVER
# ==============================
.PHONY: mcp
mcp:
	@echo "🤖 Iniciando MCP Server..."
	$(PY) mcp_server/server.py

# ==============================
# TESTS
# ==============================
.PHONY: test
test:
	@echo "🧪 Executando testes..."
	$(PY) -m pytest -v

# ==============================
# CLEAN
# ==============================
.PHONY: clean
clean:
	@echo "🧹Limpando caches e arquivos temporários..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf *.egg-info
	rm -f *.log
	@echo "✅ Limpeza concluída!"

# ==============================
# Models list
# ==============================
.PHONY: list-models
list-models:
	@echo "🔍 Listando modelos Gemini..."
	$(PY) utils/list_models.py

# ==============================
# LINT & FORMAT
# ==============================
.PHONY: lint
lint:
	@echo "🔍 Rodando Ruff (Lint + Fix)..."
	$(PY) -m ruff check . --fix
	@echo "🎨 Rodando Ruff (Format)..."
	$(PY) -m ruff format .