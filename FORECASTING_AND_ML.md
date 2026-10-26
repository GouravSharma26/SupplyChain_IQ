# Forecasting and Machine Learning Protocol

## MVP forecasting
1. Filter to a product or aggregate according to the UI selection.
2. Convert dates and aggregate units sold to a consistent daily or weekly frequency.
3. Fill missing time periods with zero only if the domain assumption is defensible; otherwise flag gaps and choose a documented handling strategy.
4. Use a chronological holdout. Never shuffle time-series rows randomly.
5. Compare a naïve baseline (for example, each future period equals the last observed period or training mean; specify which one) against Exponential Smoothing where enough history exists.
6. Evaluate both methods over the exact same test dates.
7. Fit the chosen model to available history only after evaluation, then generate the requested horizon.
8. Show model name, train/test date ranges, forecast horizon, MAE, RMSE, and warnings.

## Metrics
- MAE = mean absolute difference between actual and predicted values.
- RMSE = square root of mean squared difference.
- Optional WAPE = sum(abs(actual − forecast)) / sum(abs(actual)); define behavior if denominator is zero.
- Avoid relying on MAPE where actual values can be zero or close to zero.
- Lower MAE/RMSE is better only when comparing the same target, units, and test window.

## Minimum history and fallbacks
- Define and test a minimum history threshold for each model.
- If there is insufficient data, show baseline/fallback only and explain why.
- If a model fails to fit, preserve the baseline result and show a nontechnical warning.
- Do not display made-up scores or treat in-sample fit as test performance.

## Full-plan model evaluation
- Use rolling-origin/expanding-window backtesting.
- Include seasonal-naïve where enough seasonal cycles exist.
- Compare statistical models only when frequency and data volume support them.
- Evaluate per product and aggregate; avoid hiding poor product-level performance behind aggregate scores.
- Track model parameters and experiment configuration.
- For regression/classification, verify labels and exclude target leakage features before training.
- Use a simple baseline and held-out evaluation for every predictive model.

## Regression and delay prediction
- Regression is appropriate for continuous outcomes (e.g., demand or delivery duration) when valid labels and features exist.
- Classification is appropriate for a late-delivery target only when a trustworthy binary label can be constructed.
- Do not create a fake target from the same features used to predict it.
- Use MAE/RMSE/R² for regression; use precision, recall, PR-AUC, and confusion matrix for imbalanced classification where applicable.
- Feature importance is descriptive, not proof of causality.

## Reporting
Every model result should include: target, data range, split method, baseline, metrics, selected model, limitations, and reproducibility instructions.
