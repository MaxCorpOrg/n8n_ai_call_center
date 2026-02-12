# База знаний: Agent Ops / Server & Workspace Management

**Назначение:** единый справочник для агента управления инфраструктурой, n8n-воркспейсами, мониторингом и безопасностью.

## Структура
1. `01_INFRASTRUCTURE_AND_WORKSPACES.md` — серверы, сеть, VPN, рабочие пространства.
2. `02_SOFTWARE_INVENTORY.md` — ОС, сервисы, версии, зависимости.
3. `03_AUTOMATION_BACKUP_RESTORE.md` — автоматизация, бэкапы, восстановление.
4. `04_MONITORING_LOGGING_AUDIT.md` — метрики, алерты, логи и аудит.
5. `05_SECURITY_ACCESS_POLICIES.md` — доступы, шифрование, патчи, уязвимости.
6. `06_TROUBLESHOOTING_AND_SUPPORT.md` — типовые сбои и эскалация.
7. `07_USER_PROCEDURES_FAQ.md` — инструкции пользователям и FAQ.
8. `08_ARCHITECTURE_DIAGRAMS.md` — Mermaid-диаграммы инфраструктуры.
9. `09_PROJECT_CHANGELOG_AND_STATE.md` — что сделано в проекте, последние изменения.

## Быстрый поиск
```bash
# По IP
rg -n "147.45.213.87" docs/knowledge_base

# По имени сервера
rg -n "ai-core-1|n8n" docs/knowledge_base

# По workspace
rg -n "media_orchestrator_v1|workflowId|ABnHZb9Ee2YOtfr2" docs/knowledge_base

# По типу ресурса
rg -n "VPN|backup|restore|alert|critical" docs/knowledge_base

# По памяти и PostgreSQL
rg -n "postgres_memory|postgrest|agent_memory|Memory Neuro|Postgres Chat Memory" docs/knowledge_base

# По визуальному доступу к БД
rg -n "Adminer|ADMINER_DOMAIN|ADMINER_BASICAUTH" docs/knowledge_base
```

## Правила обновления
- После инфраструктурных изменений обновлять минимум: `01`, `02`, `05`, `09`.
- После изменений memory/adminer обязательно обновлять: `01`, `03`, `05`, `06`, `08`, `09`.
- После изменений workflow/агентов обновлять: `09` и при необходимости `08`.
- После инцидента обновлять: `06` + `04` (если менялись алерты).

## Шаблон записи изменения
```md
### YYYY-MM-DD HH:MM UTC — Короткое название
- Что изменено:
- Зачем:
- Риск/влияние:
- Проверка:
- Ответственный:
```
