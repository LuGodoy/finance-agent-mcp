# 💰 Personal Finance AI Agent (MCP Architecture)

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)]
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red)]
[![LLM](https://img.shields.io/badge/LLM-Gemini-orange)]
[![Architecture](https://img.shields.io/badge/Architecture-MCP-green)]
[![Status](https://img.shields.io/badge/Status-Active-success)]

Assistente inteligente de finanças pessoais e familiares utilizando **IA generativa**, arquitetura **MCP (Model Context Protocol)**, integração com **Gemini LLM**, banco de dados **MySQL** e interface conversacional construída com **Streamlit**.

---

## ✨ Visão Geral

Este projeto demonstra a construção de um **AI Agent completo**, capaz de responder perguntas sobre gastos financeiros utilizando dados reais armazenados em banco de dados.

O sistema integra:

- 🤖 Large Language Model (Google Gemini)
- 🧠 Agente inteligente para interpretação das perguntas
- 🔌 MCP Server para acesso estruturado aos dados
- 🗄️ Banco de dados MySQL
- 🎨 Interface conversacional com Streamlit

---

## 🧠 O que este projeto demonstra

✅ Construção de AI Agent end-to-end  
✅ Integração LLM + Banco de Dados  
✅ Arquitetura MCP com Tool Calling  
✅ Separação clara entre camadas da aplicação  
✅ Organização profissional de projeto Python  
✅ Boas práticas de engenharia de software

---

## 🏗️ Arquitetura do Sistema

```

Usuário
↓
Streamlit (Chat Interface)
↓
Finance Agent (Gemini LLM)
↓
MCP Client
↓
MCP Server (Tools)
↓
MySQL Database

```

---

## 📂 Estrutura do Projeto

```

.
├── app
│   ├── __init__.py
│   ├── main.py
│   └── styles.css
│
├── database
│   ├── __init__.py
│   └── connection.py
│
├── docs
│   └── screenshots
│
├── .env.exemple
├── LICENSE
│
├── llm
│   ├── __init__.py
│   ├── client_gemini.py
│   └── prompts.py
│
├── Makefile
│
├── mcp_server
│   ├── __init__.py
│   ├── server.py
│   └── tools
│       ├── __init__.py
│       ├── expense_items_tool.py
│       └── expense_summary_tool.py
│
├── pyproject.toml
├── README.md
├── requirements.txt
│
├── shared
│   ├── __init__.py
│   ├── config_logging.py
│   ├── config.py
│   └── date_config.py
│
└── tests
    └── __init__.py

````

---

## 🚀 Como executar o projeto

### 1️⃣ Clonar o repositório

```bash
git clone https://github.com/SEU-USUARIO/personal-finance-ai-agent-mcp.git
cd personal-finance-ai-agent-mcp
````

---

### 2️⃣ Criar ambiente virtual e instalar dependências

```bash
make install
```

Esse comando irá:

* criar o ambiente virtual `.venv`
* instalar todas as dependências necessárias

---

### 3️⃣ Criar variáveis de ambiente

```bash
make env
```

Será criado um arquivo `.env`.

Edite o arquivo e preencha com suas credenciais:

```
GEMINI_API_KEY=sua_chave_aqui

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=personal_finance

LOG_LEVEL=INFO
```

---

### 4️⃣ Executar a aplicação

```bash
make run
```

A aplicação estará disponível em:

```
http://localhost:8501
```

---

## 🤖 Executar o MCP Server

```bash
make mcp
```

---

## 🧪 Executar testes

```bash
make test
```

---

## ⚙️ Stack Tecnológica

* Python 3.13+
* Streamlit
* Google Gemini (LLM)
* MCP (Model Context Protocol)
* MySQL
* SQLAlchemy
* Pydantic
* Pytest
* Python-Dotenv

---

## 🔑 Decisões de Engenharia (Key Engineering Decisions)

* Separação entre **Agent**, **MCP Server** e **Database Layer**
* Uso de Tools MCP para evitar acesso direto do LLM ao banco
* Cache do agente com `st.cache_resource`
* Arquitetura modular preparada para múltiplos modelos LLM
* Organização orientada à escalabilidade e manutenção

---

## 🎯 Objetivo do Projeto

Projeto desenvolvido como portfólio técnico para demonstrar habilidades em:

* AI Agents
* LLM Engineering
* Arquitetura Backend
* Integração de Dados
* Design de Software

---

## ⚡ Tempo médio de setup

> ⏱️ Aproximadamente **2 minutos** após o clone do repositório.

---

## 📸 Demonstração

Adicione imagens da aplicação em:

```
docs/screenshots/
```

Exemplo:

```md
![App Screenshot](docs/screenshots/app.png)
```

---

## 👩‍💻 Autora

**Luciene Silva**
Data Science • AI Agents • Software Engineering

---

## 📄 Licença

Este projeto foi desenvolvido para fins educacionais e demonstração de portfólio.

```
