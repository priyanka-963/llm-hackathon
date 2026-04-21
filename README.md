# AI Hotel Revenue Risk Radar

The app source lives in [`revenue-risk-radar/`](revenue-risk-radar/).

If you deploy from this GitHub repository on Render, use the root-level `render.yaml`. It points Render at the app folder with `rootDir: revenue-risk-radar`.

If you want the hosted app to look like your local Streamlit preview, deploy `revenue-risk-radar/streamlit_app.py` on Streamlit Community Cloud and set the secrets there.

For AI answers in any hosted environment, add one of these secret configurations:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
```

or:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
```

Do not commit real API keys to GitHub.
