# Antigravity Independent Review Prompt

Act as an independent senior reviewer. Do not trust status claims in the README or phase log without verifying evidence.

## Review tasks
1. Inspect the source tree and compare implementation against `PROJECT_REQUIREMENTS.md` and `QUICK_LAUNCH_PLAN.md`.
2. Run the documented test suite and report the actual command/output.
3. Verify that sample data is labeled and has documented provenance.
4. Inspect validation for missing columns, invalid dates, numeric coercion, negative values, duplicates, and empty input.
5. Inspect KPI formulas and ensure snapshot inventory value is not incorrectly summed across repeated snapshots.
6. Inspect forecasting for chronological split, same test window for model comparison, correct metric calculations, and a naïve baseline.
7. Check short-series and zero-demand handling.
8. Inspect inventory formula correctness and visible assumptions.
9. Search for hard-coded fake metrics, unsupported savings claims, secrets, absolute paths, unfinished placeholders, and broken links.
10. Run the app and test the primary journey with browser tooling if available.
11. Open the deployed URL and verify actual availability and key functionality.
12. Produce `RELEASE_REPORT.md` with PASS/FAIL/NOT VERIFIED per criterion, actual evidence, deployment URL, commit SHA, known limitations, and next steps.

## Severity
- **Blocker:** application cannot start/deploy, core workflow crashes, secrets exposed, forecast leakage, fabricated results.
- **Major:** key feature missing, incorrect formula, broken upload/filters, no test evidence.
- **Minor:** visual inconsistency, noncritical UX issue, missing optional polish.

Do not mark release as complete while any blocker remains. Do not start full-roadmap work until the quick-launch acceptance gate passes or the user explicitly reprioritizes.
