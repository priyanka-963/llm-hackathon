# AI Hotel Revenue Risk Radar

A deploy-ready AI business insight app for hotel revenue teams.

It computes hotel KPIs from performance data, flags revenue risks, and uses Groq or Gemini to explain findings in clear business language. If no API key is configured, the dashboard still works and the chat endpoint returns a safe configuration message.

## Use Case

Revenue managers and external hotel-chain partners need quick answers like:

- Which hotels are underperforming?
- Why is revenue weak this week?
- Which property needs attention first?
- What action should the team take next?

The app supports scoped profiles:

- `internal`: can view all chains.
- `marriott`: automatically restricted to `MARRIOTT`.
- `hilton`: automatically restricted to `HILTON`.

## Run Locally

This project has two runnable frontends:

- Streamlit: use this when you want the same UI as `streamlit run streamlit_app.py`.
- FastAPI: use this when you want the API-backed HTML app served by `app/main.py`.

For Streamlit:

```bash
cd revenue-risk-radar
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

For FastAPI:

```bash
cd revenue-risk-radar
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Streamlit opens on:

```text
http://localhost:8501
```

## API Key Setup

Use Groq:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Use Gemini:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Do not put the API key in frontend JavaScript. Keep it in deployment environment variables.

## Docker

```bash
docker build -t revenue-risk-radar .
docker run --env-file .env -p 8000:8000 revenue-risk-radar
```

## Render Deployment

1. Push the repository to GitHub.
2. Create a Render Web Service using the root-level `render.yaml`.
3. If you create the service manually, set the Render root directory to `revenue-risk-radar`.
4. Add `LLM_PROVIDER=groq` and `GROQ_API_KEY` as environment variables.
5. To use Gemini instead, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`.
6. Redeploy or restart the service after saving secrets.

Render serves the FastAPI HTML app. If you previewed locally with Streamlit, the Render UI will not look identical because it is a different frontend.

## Streamlit Cloud Deployment

1. Push the repository to GitHub.
2. In Streamlit Cloud, set the main file path to `revenue-risk-radar/streamlit_app.py`.
3. Add `LLM_PROVIDER=groq` and `GROQ_API_KEY=your_key_here` in app secrets.
4. To use Gemini instead, set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY=your_key_here`.
5. Deploy.

Streamlit Cloud serves the same UI as the local Streamlit command.

## Endpoints

- `GET /`: browser UI
- `GET /health`: deployment health check
- `GET /api/options`: filter options
- `POST /api/insights`: KPI and risk analysis
- `POST /api/chat`: KPI analysis plus LLM-generated explanation

Example chat request:

```json
{
  "profile": "marriott",
  "city": "Dubai",
  "question": "Which hotel needs attention and what should we do next?"
}
```

## Verification

```bash
python scripts/smoke_test.py
```

Expected output:

```text
Smoke test passed
```

## Sources Used For Provider Integration

- Groq Chat Completions: https://console.groq.com/docs/api-reference
- Gemini `generateContent`: https://ai.google.dev/api
