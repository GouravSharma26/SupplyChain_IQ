# Local Setup and Deployment

## Local development
1. Install a supported Python version (prefer Python 3.11 or 3.12).
2. Create and activate a virtual environment.
3. Install dependencies from `requirements.txt`.
4. Run `pytest -q`.
5. Start the app with `streamlit run app.py`.
6. Open the local URL printed by Streamlit.

Example commands (Windows PowerShell):
```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

Example commands (macOS/Linux):
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
streamlit run app.py
```

## Deployment checklist
- Push a clean, runnable project to GitHub.
- Confirm the repository contains `app.py`, `requirements.txt`, sample data, and required source modules.
- Select Streamlit Community Cloud if available; otherwise use a compatible hosting service already accessible.
- Configure repository, branch, and app entry point.
- Add secrets only through the hosting platform's secret manager; the MVP should not require secrets.
- Inspect build logs and fix dependency or path errors.
- Open the public URL in a browser and complete the smoke-test checklist.
- Add the verified URL and deployment date to README and `RELEASE_REPORT.md`.

## Common deployment issues
- Missing package: add the dependency to requirements and redeploy.
- Incorrect Python version: choose a supported runtime and pin compatible dependencies.
- Data file not found: use repository-relative paths based on `Path(__file__)`, not the process working directory.
- Slow startup: keep the sample dataset modest and avoid unnecessary model fitting at import time.
- Local-only file path: replace absolute developer paths with repository-relative paths.
- Secret missing: remove unnecessary secret dependency or configure the secret in the hosting dashboard.
- App sleeps on free tier: mention cold-start behavior; do not describe it as always-on.

## Security
Never commit `.env`, API keys, database passwords, tokens, or private datasets. Use `.gitignore` and hosting secret settings. The MVP should operate without an LLM key.
