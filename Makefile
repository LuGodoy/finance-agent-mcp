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
	@echo " make setup     -> cria estrutura do projeto"
	@echo " make install   -> cria venv e instala dependências"
	@echo " make env       -> cria arquivos .env"
	@echo " make run       -> roda app Streamlit"
	@echo " make mcp       -> roda MCP Server"
	@echo " make test      -> roda testes"
	@echo " make clean     -> limpa caches"

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
	@mkdir -p tests
	@mkdir -p docs/screenshots

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

	@touch README.md requirements.txt pyproject.toml

	@echo "✅ Estrutura criada!"

# ==============================
# VENV + DEPENDENCIES
# ==============================
.PHONY: install
install:
	@echo "🐍 Criando ambiente virtual..."
	$(PYTHON) -m venv $(VENV)

	@echo "📦 Instalando dependências..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

	@echo "✅ Ambiente pronto!"

# ==============================
# ENV FILES
# ==============================
.PHONY: env
env:
	@echo "🔐 Criando .env.example..."

	@echo "GEMINI_API_KEY=" > .env.example
	@echo "" >> .env.example
	@echo "DB_HOST=localhost" >> .env.example
	@echo "DB_PORT=3306" >> .env.example
	@echo "DB_USER=" >> .env.example
	@echo "DB_PASSWORD=" >> .env.example
	@echo "DB_NAME=db_finance" >> .env.example
	@echo "" >> .env.example
	@echo "LOG_LEVEL=INFO" >> .env.example

	@echo "📄 Criando .env local..."
	@if [ ! -f .env ]; then cp .env.example .env; fi

	@echo "✅ Arquivos de ambiente criados!"

# ==============================
# RUN APPLICATION
# ==============================
.PHONY: run
run:
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
	@echo "🧹 Limpando caches..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Limpeza concluída!"
