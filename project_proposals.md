# EMIF Group Project — Proposals

**Question:** How can we forecast the effect of an increase in oil prices on financial markets?
**Deadline:** Sunday, April 5, 2026, 11:59 PM

---

## Available Data Summary

| Frequency | Period | Variables |
|-----------|--------|-----------|
| **Daily** | 1990–2026 (~9400 obs) | WTI, Brent, BCOM Energy, TFT futures, Nat Gas, S&P500, MSCI World, MSCI EM, Russell 2000, US 10Y, US 2Y, HY yield, Gold |
| **Monthly** | 1990–2026 (~435 obs) | Industrial Production, CFNAI, ISM Manufacturing (+ Prices Paid), ISM Services (+ Prices Paid), Retail Sales, Richmond Fed |
| **Quarterly** | 1990–2026 (~147 obs) | US GDP + components (Consumption, Goods, Durables, Non-durables, Services, Investment) |

---

## Proposal 1 — VAR + Granger Causality + IRFs (Recommended)

**Research question:** Does an oil price shock Granger-cause significant responses in US equity and bond markets, and how do these responses differ across asset classes?

**Why this is the best fit:**
- Directly uses Classes 5–6 (VAR, Granger causality, IRFs, variance decomposition)
- Also uses Classes 2–3 (descriptive stats, OLS, normality tests)
- Strong academic literature (Hamilton 1983, Kilian 2009, Kilian & Park 2009)
- Rich economic interpretation possible

**Empirical strategy:**
1. **Data:** Daily frequency — WTI returns, S&P500 returns, US 10Y rate changes, HY yield spread changes, Gold returns
2. **Descriptive analysis:** Moments, correlation matrix, normality tests (JB), serial correlation (Ljung-Box)
3. **VAR(p) estimation:** Select lag order via AIC/BIC, estimate by OLS
4. **Granger causality tests:** Geweke (1982) framework — test if WTI Granger-causes equity/bond variables
5. **Impulse Response Functions:** Cholesky-orthogonalized IRFs — shock to oil, trace response in equities, rates, credit, gold
6. **Variance decomposition:** What share of S&P500 / bond variance is explained by oil shocks?
7. **Robustness:** Sub-sample analysis (pre/post-2008, pre/post-COVID), different orderings in Cholesky

**Key literature:** Hamilton (1983), Kilian (2009), Kilian & Park (2009), Barsky & Kilian (2004)

**Pros:** Perfectly aligned with course content, rich results, straightforward to implement
**Cons:** Common approach — differentiation comes from variable selection and economic interpretation

---

## Proposal 2 — Oil Price Asymmetry + Predictive Regressions

**Research question:** Do oil price increases and decreases have asymmetric effects on equity market returns, and can we exploit this asymmetry to forecast market performance?

**Why this works:**
- Uses Classes 3–4 (OLS, MLE, ARMA, model assessment, out-of-sample RMSE/MAE)
- Builds on the asymmetry concept from Class 2 (volatility asymmetry)
- Original angle: Hamilton's (1996) net oil price increase concept

**Empirical strategy:**
1. **Data:** Daily — WTI, S&P500, MSCI EM, Russell 2000; Monthly — ISM, Industrial Production
2. **Construct asymmetric oil variables:** Mork (1989) decomposition into positive/negative changes; Hamilton (1996) Net Oil Price Increase (NOPI)
3. **Predictive regressions:** Regress future equity returns on lagged oil shocks (positive vs. negative)
4. **Out-of-sample forecasting:** Rolling window, evaluate with RMSE, MAE, R²_OOS
5. **Add macro controls:** ISM, Industrial Production as additional predictors
6. **Compare models:** AR(1) baseline vs. oil-augmented models via information criteria

**Key literature:** Mork (1989), Hamilton (1996, 2003), Jones & Kaul (1996), Driesprong et al. (2008)

**Pros:** More original angle, strong forecasting dimension, directly answers "can we forecast?"
**Cons:** Less multivariate, doesn't showcase VAR/IRF skills from Classes 5–6

---

## Proposal 3 — Full Macro-Finance Pipeline: Oil → Macro → Markets

**Research question:** Does the effect of oil price shocks on equity markets operate through macroeconomic channels (GDP, industrial production, inflation expectations), and can a two-stage approach improve forecasting?

**Why this works:**
- Uses ALL three data frequencies (daily, monthly, quarterly)
- Combines virtually everything from the course (descriptive stats, OLS, ARMA, VAR, Granger causality, IRFs)
- Ambitious — but that's what gets top marks

**Empirical strategy:**
1. **Stage 1 — Oil → Macro (monthly/quarterly VAR):** VAR with WTI (aggregated to monthly), Industrial Production, ISM, GDP growth. Test Granger causality, compute IRFs
2. **Stage 2 — Macro → Markets (monthly predictive regressions):** Use macro variables (potentially instrumented by oil) to forecast monthly S&P500, HY spread, bond yields
3. **Stage 3 — Direct channel (daily VAR):** VAR with WTI, S&P500, 10Y rate, Gold at daily frequency. Compare direct vs. macro-mediated effects
4. **Synthesis:** Decompose oil's effect into direct (financial channel) and indirect (macro channel)

**Key literature:** Kilian (2009), Kilian & Park (2009), Hamilton (1983, 2003), Barsky & Kilian (2004), Bernanke et al. (1997)

**Pros:** Most comprehensive, uses all data, strong narrative, highest grade potential
**Cons:** Most complex, risk of being too ambitious if not well-executed

---

## Recommendation

- **Proposal 1** — Safest high-quality result, maps perfectly to Classes 5–6
- **Proposal 2** — More original, strong forecasting angle (matches the project question wording)
- **Proposal 3** — Highest grade potential but most complex

Elements can be combined: e.g., Proposal 1 as core + asymmetric oil variable from Proposal 2 as robustness check.
