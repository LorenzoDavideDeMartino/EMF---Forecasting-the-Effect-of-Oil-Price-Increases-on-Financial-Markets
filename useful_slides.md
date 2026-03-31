# Useful Slides for Proposal 1 — VAR + Granger Causality + IRFs

---

## Step 1: Descriptive Statistics (Class 2)

| Pages | Topic | Key Content |
|-------|-------|-------------|
| 7–9 | Moments, Skewness, Kurtosis | Definitions, formulas (eq. 1–2) |
| 10 | Sample mean | Formula (eq. 3) |
| 12 | Variance / Std deviation | Unbiased & ML estimators (eq. 5) |
| 14–15 | Sample skewness & kurtosis | Estimator formulas (eq. 7), interpretation |
| 41–42 | Cross-correlation | Covariance & correlation formulas (eq. 30–32) |

## Step 2: Normality & Serial Correlation Tests (Class 2)

| Pages | Topic | Key Content |
|-------|-------|-------------|
| 20–22 | Jarque-Bera test | JB statistic formula (eq. 10), chi²(2) rejection rule |
| 30–33 | Autocorrelation function (ACF) | Definition (eq. 19), sample estimator (eq. 20), asymptotic distribution (eq. 21) |
| 34–35 | Box-Pierce & Ljung-Box tests | Q and Q' statistics (eq. 25–26), chi²(p) rejection rule |
| 36–39 | Serial correlation in volatility | Squared returns as proxy (eq. 27–29) |

## Step 3: OLS & Model Assessment (Class 3)

| Pages | Topic | Key Content |
|-------|-------|-------------|
| 12–15 | OLS in matrix form | beta = (X'X)⁻¹(X'R) (eq.), V[beta] = σ²(X'X)⁻¹ |
| 16–17 | Student test | t-stat = beta_hat / sigma_beta, rejection at 1.96 |
| 18 | R-squared | R² = 1 - RSS/TSS |
| 38 | Out-of-sample RMSE & MAE | Formulas for forecast evaluation |
| 39 | Fisher test | F = [R²/(1-R²)] × [(n-p-1)/p] |

## Step 4: VAR(p) Specification & Estimation (Class 5)

| Pages | Topic | Key Content |
|-------|-------|-------------|
| 3–5 | From AR to VAR | Motivation, matrix form (eq. 5) |
| 12 | VAR(1) definition | r_t = Phi_0 + Phi_1 r_{t-1} + epsilon_t (eq. 11–12) |
| 13–15 | VAR(1) stationarity & moments | Unconditional mean, Wold decomposition (eq. 15), eigenvalue condition |
| 16 | VAR(p) generalization | Lag polynomial notation (eq. 20–21) |
| 17–18 | OLS estimation of VAR | Phi_hat = (R'R)⁻¹R'r (eq. 25–26) |
| 19–21 | MLE estimation | Multivariate Gaussian log-likelihood (eq. 27–33) |
| 31–32 | Python code: constrained VAR | `ML_VAR` function with scipy BFGS |

## Step 5: Lag Order Selection (Class 5)

| Pages | Topic | Key Content |
|-------|-------|-------------|
| 26 | Likelihood ratio test | LR(p) formula, chi²(n²) distribution (eq. 35) |
| 27 | AIC & BIC | AIC(p) = log|Σ| + 2n²p/T, BIC with log(T) penalty |
| 28 | FPE & Hannan-Quinn | Additional criteria (eq. 36–37) |

## Step 6: Granger Causality — Geweke (1982) (Class 5 + Class 6)

### Class 5
| Pages | Topic | Key Content |
|-------|-------|-------------|
| 42 | Granger causality definition | MSE comparison (eq. 47–48) |
| 43 | Three representations | VAR, joint no-cross, marginal (eq. 49) |
| 44 | Test statistics | C_{Y→X}, C_{X→Y}, C_{X↔Y} formulas (eq. 50–52) |
| 45 | Total interdependence | Decomposition C = C_{Y→X} + C_{X→Y} + C_{X↔Y} (eq. 53–55) |

### Class 6
| Pages | Topic | Key Content |
|-------|-------|-------------|
| 14–17 | Same framework (repeated) | Cleaner presentation, same equations |
| 19–22 | **OIL APPLICATION** | WTI→SP500 Granger causality, full & subsample results |

## Step 7: Impulse Response Functions — Cholesky (Class 5 + Class 6)

### Class 5
| Pages | Topic | Key Content |
|-------|-------|-------------|
| 46–48 | IRF theory | Psi_s = ∂r_{t+s}/∂epsilon_t, VAR(1) case = Phi_1^s |
| 49–50 | Numerical example | 3-variable VAR(1) step-by-step |
| 51–60 | **Cholesky orthogonalization** | Σ=PP', Gamma_s = Psi_s × P, ordering matters (eq. 64–91) |
| 60 | Final IRF formula | h → Phi_1^h × P, bootstrap confidence intervals |

### Class 6
| Pages | Topic | Key Content |
|-------|-------|-------------|
| 24–28 | IRF definition & VAR(1) case | Wold decomposition, numerical example |
| 29–38 | **Cholesky full derivation** | Orthogonalized shocks, ordering implications, final formula |

## Step 8: Variance Decomposition & Spillovers (Class 5 + Class 6)

### Class 5
| Pages | Topic | Key Content |
|-------|-------|-------------|
| 68–70 | Variance decomposition | h-step FEVD formula (eq. 97–98), spillover measures (eq. 99–102) |
| 71–76 | Credit spread application | Spillover table, time-varying spillover chart |

### Class 6
| Pages | Topic | Key Content |
|-------|-------|-------------|
| 47–50 | FEVD & spillover formulas | Same framework, Diebold-Yilmaz style indices |
| 51–56 | Credit spread application | Full spillover table, crisis-annotated time series |

## Step 9: Practical VAR Applications (for inspiration)

### Class 5
| Pages | Topic |
|-------|-------|
| 61–67 | US Macro VAR (5 vars, 1980–2021): stationarity, Granger, lag selection, IRFs |
| 77–92 | Inflation shock VAR (3 vars): lag selection, IRFs, out-of-sample forecasting |

### Class 6
| Pages | Topic |
|-------|-------|
| 19–22 | **Oil volatility → equity transmission**: WTI vs SP500 Granger causality |
| 40–46 | US Macro VAR: full pipeline (stationarity → Granger → lag → estimation → IRFs) |
| 58–72 | Inflation/Fed/CapUtil VAR: Cholesky identification, IRFs, 2022 forecast exercise |

---

## Summary: Most Important Pages

| Priority | Class | Pages | Why |
|----------|-------|-------|-----|
| **Critical** | Class 5 | 42–45 | Granger causality formulas |
| **Critical** | Class 5 | 51–60 | Cholesky IRF derivation |
| **Critical** | Class 5 | 68–70 | Variance decomposition |
| **Critical** | Class 6 | 19–22 | Oil→equity application (your exact topic) |
| **Critical** | Class 5 | 17–18, 26–27 | VAR estimation + lag selection |
| High | Class 2 | 20–22, 34–35 | JB test + Ljung-Box |
| High | Class 6 | 40–46 | Full VAR pipeline example |
| High | Class 5 | 77–92 | Inflation VAR with forecasting |
| Medium | Class 2 | 7–15 | Descriptive stats formulas |
| Medium | Class 3 | 12–18 | OLS, R², Student test |
