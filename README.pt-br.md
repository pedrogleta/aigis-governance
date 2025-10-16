# Aigis Governance

Um assistente de dados de IA que você pode conectar aos seus próprios bancos de dados. Faça perguntas em linguagem natural; o sistema escreve SQL, executa-o na conexão selecionada e retorna respostas com visualizações Vega-Lite opcionais. Uma interface de chat moderna em React transmite respostas de um backend FastAPI com tecnologia LangGraph.

## Guia de Início Rápido

### Opção A: Docker Compose (recomendado)

Pré-requisitos: Docker + Docker Compose

0) Configure as variáveis de ambiente

- Copie o template para um arquivo de ambiente real na raiz do repositório e edite conforme necessário:

   ```bash
   cp .env.example .env
   ```

- Você deve configurar pelo menos um provedor de LLM para que o aplicativo possa responder a perguntas. Qualquer um dos seguintes funciona:
   - LM Studio (compatível com OpenAI): defina `LM_STUDIO_ENDPOINT` (ex: `http://host.docker.internal:1234/v1`)
   - DeepSeek: defina `DEEPSEEK_API_KEY`
   - Google: defina `GOOGLE_API_KEY`
   - OpenAI: defina `OPENAI_API_KEY`

- Defina também segredos para autenticação e criptografia (veja `.env.example`):
   - `SECRET_KEY`, `MASTER_ENCRYPTION_KEY`

1) Na raiz do repositório, inicie os serviços:

```bash
docker compose up --build
```

2) Abra:
- Frontend (build de produção via Nginx): http://localhost:3000
- Backend API: http://localhost:8000

Notas
- O contêiner do backend executa as migrações do Alembic automaticamente na inicialização.
- Você pode personalizar os padrões através do `.env` ou variáveis de ambiente no `docker-compose.yml`.

### Opção B: Desenvolvimento local

Backend
```bash
cd backend
uv venv && uv sync
# crie .env com pelo menos:
#   SECRET_KEY=change-me
#   MASTER_ENCRYPTION_KEY=change-me
#   POSTGRES_HOST=localhost
#   POSTGRES_USER=postgres
#   POSTGRES_PASSWORD=postgres
#   POSTGRES_DB=aigis_governance
# provedores de modelo opcionais:
#   LM_STUDIO_ENDPOINT=http://0.0.0.0:1234/v1
#   DEEPSEEK_API_KEY=your-deepseek-key
#   GOOGLE_API_KEY=your-google-key
#   OPENAI_API_KEY=your-openai-key
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend
```bash
cd frontend
npm install
npm run dev
```

## Destaques

- Converse com seus dados usando linguagem natural
- Agente que usa ferramentas: gera SQL e, opcionalmente, gráficos (Vega-Lite)
- Respostas via streaming com SSE
- Autenticação e conexões de banco de dados por usuário (Postgres/SQLite atualmente; extensível)
- Postgres para dados do aplicativo (usuários, threads, conexões de usuário)
- Configuração simples de modelo OSS local via LM Studio ou use seu próprio provedor
 - Seleção de modelo LLM por thread (cada thread de chat pode escolher seu próprio modelo)

## Arquitetura em resumo

- Backend (Python/FastAPI):
   - Autenticação (JWT), CRUD de conexões e testes
   - Threads de chat + streaming de Server-Sent Events
   - Agente LangGraph com ferramentas definidas no código
   - Postgres como banco de dados principal; engines dinâmicos para bancos de dados fornecidos pelo usuário
   - APIs de seleção de modelo por thread
- Frontend (React + Vite + Tailwind):
   - UI de chat com streaming ao vivo
   - Gerencie e selecione suas conexões de banco de dados
   - Renderiza especificações Vega-Lite no lado do cliente (não é necessário serviço de imagem)
- Docker Compose: inicializa Postgres, backend, frontend (MinIO está incluído, mas é opcional e não é necessário para gráficos que são renderizados no lado do cliente)

Mapa do código (selecionado):

- Backend
   - `backend/app/main.py` – App FastAPI, CORS, roteadores, `/health`
   - `backend/app/routes/auth.py` – registro/login/eu, perfil, usuários administradores
   - `backend/app/routes/chat.py` – criar thread, enviar mensagem (SSE), estado da thread
   - APIs de modelo por thread: `GET /chat/{thread_id}/model`, `POST /chat/{thread_id}/model`
   - `backend/app/routes/connections.py` – CRUD de conexões de BD por usuário + `/test`
   - `backend/app/helpers/langgraph.py` – Adaptador de streaming SSE
   - `backend/app/helpers/user_connections.py` – construir schema de BD em markdown, executar SQL
   - `backend/llm/agent.py` – Grafo de estado LangGraph + nó de ferramentas
   - `backend/llm/model.py` – Inicialização de modelo e vinculação de ferramentas
   - `backend/llm/tools.py` – Implementações das ferramentas `ask_database`, `ask_analyst`
   - `backend/llm/prompts.py` – Prompts de sistema, SQL e Vega-Lite
   - `backend/core/{config,database,types,crypto}.py` – configurações, engines, estado, AES-GCM
   - `backend/models/*`, `backend/crud/*`, `backend/schemas/*` – usuários, threads, conexões
- Frontend
   - `frontend/src/services/api.ts` – API de threads, SSE, autenticação, conexões
   - `frontend/src/components/ChatUI.tsx` – Fluxo de chat e renderização de streaming
   - `frontend/src/components/ModelSidebar.tsx` – UI de seleção de modelo por thread
   - `frontend/src/components/MessageComponents.tsx` – Renderizadores de texto/ferramenta/gráfico
   - `frontend/src/pages/*` – Login, Registro, Chat

## Como funciona

1) Conecte um banco de dados
- Crie uma conexão em Conexões: Postgres ou SQLite (caminho do arquivo)
- As senhas são armazenadas criptografadas (AES-GCM) usando uma `MASTER_ENCRYPTION_KEY`

2) Faça uma pergunta
- O frontend envia sua mensagem para `POST /chat/{thread_id}/message` e abre um stream SSE
- O prompt do agente inclui um snapshot em markdown do schema do seu BD (buscado ao vivo)

3) Fluxo do Agente (LangGraph)
- Ordem das ferramentas: `ask_database` → opcional `ask_analyst`
- `ask_database` usa um LLM para escrever SQL bruto a partir da sua solicitação e do schema, e então o executa na conexão selecionada
- `ask_analyst` transforma resultados tabulares em uma especificação JSON Vega-Lite para gráficos
- O backend transmite tokens como eventos `chunk` e saídas de ferramentas como `tool_result`
- O frontend renderiza markdown e gráficos (via react-vega)

## Ambiente

Ambiente usado pelo Compose (padrões mostrados em `docker-compose.yml`):
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `LM_STUDIO_ENDPOINT` (padrão `http://0.0.0.0:1234/v1`)
 - `DEEPSEEK_API_KEY` (opcional; ativa o provedor DeepSeek)
 - `GOOGLE_API_KEY` (opcional; ativa os modelos Gemini)
 - `OPENAI_API_KEY` (opcional; ativa os modelos OpenAI)
- `ENABLE_OPIK_TRACER` (0/1)
- Para armazenamento seguro de senhas em conexões, defina no ambiente do contêiner do backend ou em `.env` em `backend/`: `MASTER_ENCRYPTION_KEY` e `SECRET_KEY`

### Opção B: Desenvolvimento local

Backend
```bash
cd backend
uv venv && uv sync
# crie .env com pelo menos:
#   SECRET_KEY=change-me
#   MASTER_ENCRYPTION_KEY=change-me
#   POSTGRES_HOST=localhost
#   POSTGRES_USER=postgres
#   POSTGRES_PASSWORD=postgres
#   POSTGRES_DB=aigis_governance
# provedores de modelo opcionais:
#   LM_STUDIO_ENDPOINT=http://0.0.0.0:1234/v1
#   DEEPSEEK_API_KEY=your-deepseek-key
#   GOOGLE_API_KEY=your-google-key
#   OPENAI_API_KEY=your-openai-key
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend
```bash
cd frontend
npm install
npm run dev
```

## Visão geral da API

Autenticação (`/auth`)
- `POST /register` – email, nome de usuário, senha
- `POST /login` – retorna JWT; use `Authorization: Bearer <token>`
- `GET /me` – usuário atual; `PUT /me` – atualizar perfil; `POST /change-password`
- Admin: `GET /users`, `GET /users/{id}`, `DELETE /users/{id}`

Conexões (`/connections`)
- `GET /` listar, `POST /` criar, `GET/PUT/DELETE /{id}`, `POST /{id}/test`
- Suporta db_type: `postgres` ou `sqlite` (para SQLite, defina o host como o caminho do arquivo)

Chat (`/chat`)
- `POST /thread` – criar uma thread → `{ "thread_id": "uuid" }`
- `POST /{thread_id}/message` – corpo `{ text, user_connection_id? }` transmite SSE
   - Eventos: `{type:"chunk",content:string}`, `{type:"tool_result",content:any}`, `{type:"end",full_response:string}`
- `GET /{thread_id}` – mensagens persistidas
- `GET /{thread_id}/state` – snapshot do estado do grafo (ex: `db_schema`)
- `POST /{thread_id}/connection` – definir a user_connection ativa para esta thread
- `GET /{thread_id}/model` – obter o modelo atual para esta thread e o mapa de disponibilidade
- `POST /{thread_id}/model` – definir o modelo para esta thread; corpo `{ name: "qwen3-8b" | "gpt-oss-20b" | "deepseek-chat" }` (aliases como `qwen`, `gpt_oss`, `deepseek` são aceitos)

Saúde
- `GET /health` – conectividade do servidor e do Postgres

## Modelos e provedores

Os modelos suportados são inicializados em `backend/llm/model.py` usando `init_chat_model` da LangChain:
- OSS via LM Studio: `openai/gpt-oss-20b`, `qwen/qwen3-8b` (ative definindo `LM_STUDIO_ENDPOINT`)
- DeepSeek: `deepseek-chat` (ative definindo `DEEPSEEK_API_KEY`)
- Google: `gemini-2.5-pro` (ative definindo `GOOGLE_API_KEY`)
- OpenAI: `gpt-5` (ative definindo `OPENAI_API_KEY`)

A seleção é por thread: cada thread de chat pode escolher seu próprio modelo através da UI (botão Modelo perto do cabeçalho) ou das APIs listadas acima. A disponibilidade é derivada das variáveis de ambiente e retornada na resposta de `GET /chat/{thread_id}/model`.

Notas:
- Uma thread começa sem nenhum modelo selecionado; a UI mostra um indicador vermelho “Nenhum modelo selecionado” até que você escolha um.
- As ferramentas e o assistente resolvem o modelo por thread em tempo de execução. Se nenhum modelo for definido, o assistente retornará um erro solicitando que você selecione um.
- Aliases são aceitos por conveniência: `qwen` → `qwen3-8b`, `gpt_oss`/`gpt-oss` → `gpt-oss-20b`, `deepseek` → `deepseek-chat`, `gemini`/`gemini-pro` → `gemini-2.5-pro`, `gpt5` → `gpt-5`.

## Agente e ferramentas

- Grafo: `backend/llm/agent.py` (LangGraph com checkpointer em memória)
- Estado: `AigisState` inclui `messages`, `model_name`, `db_schema`, `connection`, `sql_result`
- Ferramentas:
   - `ask_database(query)` – LLM→SQL, executa via SQLAlchemy, retorna linhas/contagem
   - `ask_analyst(query)` – retorna `{ type: "vega_lite_spec", spec: <JSON> }`
- Prompts em `backend/llm/prompts.py` forçam a ordenação das ferramentas e os formatos de saída

## Notas de segurança

- `SECRET_KEY` do JWT e `MASTER_ENCRYPTION_KEY` do AES-GCM devem ser definidos
- As senhas de conexão são armazenadas criptografadas (iv + texto cifrado) no Postgres

## Solução de problemas

- 401/403 da API: certifique-se de que está enviando `Authorization: Bearer <token>`
- O streaming do SSE do chat não funciona: verifique a aba de rede nas ferramentas de desenvolvedor do navegador e os logs do backend
- “conexão não encontrada” nas respostas: selecione uma conexão na UI primeiro
- Erros de SQL retornam como resultados de ferramentas; o agente exibirá uma mensagem amigável
- Frontend 3000 → Backend 8000: CORS está habilitado para `*` por padrão em desenvolvimento

## Licença

Nenhum arquivo de licença explícito foi fornecido neste repositório. Consulte o proprietário do repositório se precisar dos termos de uso.