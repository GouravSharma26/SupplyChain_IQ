# Antigravity Agent Instructions

## Mission
Build SupplyChain IQ as a reliable, demonstrable supply-chain analytics project. The immediate deadline is 24 hours. Execute `QUICK_LAUNCH_PLAN.md` only until its release gates pass.

## Mandatory order
1. Inspect the repository, runtime, installed tools, and deployment constraints.
2. Read `README.md`, `PROJECT_REQUIREMENTS.md`, `ARCHITECTURE.md`, and `QUICK_LAUNCH_PLAN.md`.
3. Create/update `PHASE_LOG.md` and `DEVELOPMENT_CHECKLIST.md`.
4. Implement the smallest complete vertical slice first: data → validation → KPIs → forecast → inventory recommendation → dashboard.
5. Run tests and launch the app locally.
6. Use a browser to verify the user journey where browser tooling is available.
7. Deploy, then verify the deployed URL in a real browser.
8. Write evidence and remaining limitations to `RELEASE_REPORT.md`.
9. Stop. Do not begin `FULL_PROJECT_PLAN.md` until the quick-launch acceptance criteria pass or the user explicitly changes priority.

## Engineering rules
- Do not stop at planning or documentation; implement working code.
- Make small, coherent changes and keep the app runnable after each phase.
- Prefer clear, maintainable Python over premature abstraction.
- Pin dependencies with compatible versions in `requirements.txt`.
- Use `.env.example` for configuration and never commit secrets.
- Include useful error messages and empty-state handling.
- Validate uploaded files, required columns, date parsing, numeric fields, and nonnegative quantities where applicable.
- Avoid data leakage: forecasting validation must be chronological, never random-shuffled.
- Always compare the model to a naïve baseline.
- Metrics must be calculated from held-out observations, not training fit.
- If there is insufficient history for a statistical model, explain the fallback rather than crashing.
- Never hard-code fake metrics as if they were model outputs.
- Never silently discard malformed rows; report how many were rejected and why.
- If a database is not available within the deadline, use a documented local/sample-data fallback and log PostgreSQL as a full-roadmap task. Do not claim PostgreSQL integration exists unless verified.
- Do not add an LLM API key requirement to the quick release.
- No real-world orders, purchasing, supplier communication, or financial transactions are performed; this is decision support only.
- Use deterministic sample data generation or bundle a dataset with clear provenance and license.
- Do not copy another repository's implementation. References are for learning only.
- Avoid overengineering, authentication, microservices, Kubernetes, or cloud infrastructure that does not improve the 24-hour deliverable.

## Required evidence
Record actual commands, test counts/results, build/run results, deployment URL, and browser checks. Mark unverified items as NOT VERIFIED. Never fabricate completion.
