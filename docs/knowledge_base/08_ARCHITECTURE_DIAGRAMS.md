# 08. Архитектурные диаграммы

## 1) Инфраструктура (упрощённо)

```mermaid
flowchart LR
    U[User / Telegram] --> TG[Telegram Bot API]
    TG --> TR[Traefik HTTPS :443]
    TR --> N8N[n8n Master Workflow]
    TR --> ADM[Adminer UI]
    N8N --> A2[Agent 2 Planner]
    N8N --> A3[Agent 3 Nano Banana / Pollinations]
    N8N --> A5[Agent 5 Gemini/Flow]
    N8N --> A4[Agent 4 Kling Video]
    N8N --> MNA[Memory Neuro Agent]
    N8N --> T[Tavily Search]
    N8N --> PM[(Postgres Memory)]
    PM --> PR[PostgREST API]
```

## 2) Пайплайн master (актуальный)

```mermaid
flowchart TD
    S[Telegram Trigger] --> AC[Access Control]
    AC --> SW{Allowed?}
    SW -- no --> DENY[Telegram Reply: access denied]
    SW -- yes --> TXT[Set Text]
    TXT --> RP[Router | Intent Parse]
    RP --> MGR[AGENT 1 | Manager]
    MEM[Postgres Chat Memory] --> MGR
    MGR --> TOOLS[Agents 2/3/4/5 + Tavily + Memory Neuro]
    MGR --> G[Reply Guardrail]
    G --> OUT[Telegram Reply]
    MGR --> ERR[Set Error Reply]
    ERR --> OUT
```

## 3) Access control

```mermaid
flowchart LR
    TG[Telegram Trigger] --> AC[Access Control]
    AC --> SW{Allowed?}
    SW -- yes --> CORE[Main logic]
    SW -- no --> DENY[Reply: access denied]
```
