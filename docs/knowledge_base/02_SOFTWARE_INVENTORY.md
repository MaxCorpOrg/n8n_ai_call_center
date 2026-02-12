# 02. Программное обеспечение и версии

## 1) Базовое ПО

| Категория | Компонент | Версия/Тег | Где используется |
|---|---|---|---|
| ОС | Ubuntu | 24.04 | Сервер ai-core-1 |
| Workflow engine | n8n | `2.6.4` (baseline в watchlist) | Основной сервис |
| Reverse proxy | Traefik | `v2.11.36` | HTTPS + ACME |
| Cache | Redis | `7.4-alpine` | В составе n8n stack |
| DB (memory) | PostgreSQL | `16-alpine` | `docker-compose.memory.yml` |
| DB API | PostgREST | `latest` | REST API к `agent_memory` |
| DB UI | Adminer | `latest` | UI через Traefik на 443 |
| Контейнеризация | Docker Engine + Compose plugin | TODO | Прод-стек |
| БД (call center) | PostgreSQL | `16-alpine` | `docker-compose.callcenter.yml` |

## 2) Инвентарь n8n workflow

| Workflow ID | Название | Роль |
|---|---|---|
| `C8Wmmjuv5hC425PM` | MEDIA_AGENT_1 | Master Orchestrator TG |
| `ABnHZb9Ee2YOtfr2` | MEDIA_AGENT_ROUTER | Intent Router (Code+Switch) |
| `KeKhk230Zy3Iz0a4` | MEDIA_AGENT_2 | Script Planner |
| `KFWMYCaEpWAdVIn3` | MEDIA_AGENT_3 | Nano Banana / Pollinations Image |
| `LG1KGfhnNCICjNra` | MEDIA_AGENT_5 | Gemini Nano Banana / Flow Image |
| `DUJBo0tvHA5qIafi` | MEDIA_AGENT_4 | Kling Video |
| `K5es5hBE05LEeB1j` | KB_SYNC_AGENT | Knowledge Base Sync |
| `kcH2rlqr8aZoOPiO` | MEMORY_NEURO_AGENT | GitHub Markdown Memory |

## 3) Ключевые интеграции (без секретов)

| Интеграция | Назначение | Где задаётся |
|---|---|---|
| Telegram Bot API | Диалог с пользователем | Credentials `telegramApi` |
| Mistral OpenAI-compatible | LLM для агентов | Credentials `openAiApi` |
| Tavily | Интернет-поиск | HTTP Tool в master |
| Kling API | Генерация видео | Agent 4 |
| Gemini/Vertex | Генерация изображений | Agent 5 |
| PostgreSQL Chat Memory | Память диалога (`agent_memory`) | Узел `Postgres Chat Memory` в Master |
| GitHub API | Долговременная markdown memory + KB Sync | `MEMORY_GITHUB_TOKEN`, `KB_GITHUB_TOKEN` |

## 4) Команды инвентаризации
```bash
# Образы/контейнеры
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'

# Версия n8n (через контейнер)
docker compose --env-file .env.https -f docker-compose.https.yml exec -T n8n n8n --version

# Проверить pinned image
rg -n "docker.n8n.io/n8nio/n8n" docker-compose*.yml

# Проверить memory stack
docker compose --env-file .env.https --env-file .env.memory \
  -f docker-compose.https.yml -f docker-compose.memory.yml ps
```
