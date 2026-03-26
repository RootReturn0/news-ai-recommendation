# news-ai-recommendation

FastAPI + Telegram Bot + OpenAI/Tavily powered personalized news agent.

## Run

1. Create and activate a virtualenv.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Fill `.env` with the needed values:
- `TG_BOT_TOKEN`
- `TAVILY_API_KEY` for `/news`
- `OPENAI_API_KEY` or your OpenAI-compatible gateway credentials for summary generation

4. Start the app:

```bash
uvicorn app.main:app --reload
```

## Endpoints

- `GET /health`
- `POST /telegram/webhook`
- `POST /telegram/debug`

## Commands

- `/topics AI, startups`
- `/keywords OpenAI, YC`
- `/settings`
- `/news today`
- `/hotnews`

## Notes

- `/news` uses Tavily search when `TAVILY_API_KEY` is configured.
- `/hotnews` reads from [yc-example.xml](/Users/return0/Study/Learning/Programming/news-ai-recommendation/data/rss/yc-example.xml).
- If no OpenAI-compatible credentials are configured, the app falls back to rule-based summaries.
