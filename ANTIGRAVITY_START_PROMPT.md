# Antigravity Start Prompt — Execute the 24-Hour Quick Launch

You are the implementation agent for SupplyChain IQ. Read `AGENTS.md`, `README.md`, `PROJECT_REQUIREMENTS.md`, `ARCHITECTURE.md`, `DATA_AND_METRICS.md`, `FORECASTING_AND_ML.md`, `TESTING_AND_QUALITY.md`, `DEPLOYMENT.md`, and especially `QUICK_LAUNCH_PLAN.md`.

## Your task
Build, test, and deploy the MVP within the 24-hour deadline. Do not stop after writing a plan. Begin by inspecting the current repository and environment, then implement the smallest complete vertical slice.

## Required behavior
1. Follow the time boxes and acceptance gates in `QUICK_LAUNCH_PLAN.md`.
2. Create/update `DEVELOPMENT_CHECKLIST.md` and `PHASE_LOG.md`.
3. Use synthetic sample data unless a suitable public dataset is already available and its provenance/license is documented.
4. Deliver a working Streamlit app with CSV upload, data-quality reporting, KPI cards, interactive charts, demand forecast, chronological baseline comparison, MAE/RMSE, reorder-point recommendations, and an inventory scenario.
5. Add and run automated tests.
6. Deploy to a suitable public hosting platform if the user’s account access permits.
7. Use browser tooling to test both local and deployed versions where possible.
8. Record exact commands, test results, commit SHA, deployment URL, and browser results in `RELEASE_REPORT.md`.
9. If a task is blocked by a missing login or permission, complete everything else and write the exact user action required. Never invent access or claim success.
10. Do not begin the full roadmap until the quick-launch release gate passes.

## Constraints
- No fabricated scores, savings, or performance claims.
- No random shuffle for time-series evaluation.
- No LLM key, ERP/SAP integration, authentication, or unnecessary infrastructure in the MVP.
- Keep business logic testable outside the Streamlit UI.
- Show assumptions, data provenance, and limitations.
- Do not leave the main features as mockups or TODO placeholders.
- Avoid breaking a working version for nonessential polish.

Start with repository reconnaissance, then work through the phases in order. At each phase, report what changed, what you ran, actual results, blockers, and the next action. Continue autonomously until the release gate is met or a genuine external blocker requires user input.
