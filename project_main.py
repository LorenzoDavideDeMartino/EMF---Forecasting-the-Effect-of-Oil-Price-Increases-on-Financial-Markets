from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, grangercausalitytests


DEFAULT_DATA_PATH = Path(
    r"C:\Users\loren\OneDrive\Documents\HEC Lausanne\_Second Semester\Empirical Methods in Finance\Group Project\data_hec_projet_1.xlsx"
)


DAILY_COLUMNS = [
    "date",
    "wti",
    "brent",
    "bcom_energy",
    "tft",
    "natgas",
    "sp500",
    "msci_world",
    "msci_em",
    "russell2000",
    "us10y",
    "us2y",
    "hy_ytw",
    "gold",
]

MONTHLY_COLUMNS = [
    "date",
    "ip",
    "cfnai",
    "ism_mfg",
    "ism_prices",
    "ism_services",
    "ism_services_prices",
    "retail_sales",
    "richmond_fed",
]


def load_bloomberg_sheet(excel_path, sheet_name, columns):
    raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    data = raw.iloc[5:].copy()
    data.columns = columns

    first_value = str(data.iloc[0, 0]).strip().lower()
    if first_value == "dates":
        data = data.iloc[1:].copy()

    data["date"] = pd.to_datetime(data["date"])

    for column in columns[1:]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.sort_values("date").reset_index(drop=True)
    return data


def show_missing_report(df, label):
    report = pd.DataFrame(
        {
            "missing_count": df.isna().sum(),
            "missing_share": df.isna().mean().round(4),
        }
    )
    print(f"\nMissing values report: {label}")
    print(report.to_string())
    return report


def aggregate_daily_to_monthly(daily_df):
    monthly_last = (
        daily_df.set_index("date")
        .resample("M")
        .last()
        .reset_index()
        .rename(columns={"date": "month_end"})
    )

    daily_returns = daily_df[["date", "sp500"]].copy()
    daily_returns["sp500_daily_log_return"] = np.log(daily_returns["sp500"]).diff()
    daily_returns["month_end"] = daily_returns["date"].dt.to_period("M").dt.to_timestamp("M")

    realized_vol = (
        daily_returns.groupby("month_end")["sp500_daily_log_return"]
        .std()
        .reset_index()
        .rename(columns={"sp500_daily_log_return": "sp500_realized_vol"})
    )

    monthly_last = monthly_last.merge(realized_vol, on="month_end", how="left")
    monthly_last = monthly_last.rename(columns={"month_end": "date"})
    return monthly_last


def prepare_monthly_dataset(excel_path=DEFAULT_DATA_PATH):
    daily = load_bloomberg_sheet(excel_path, "Daily", DAILY_COLUMNS)
    monthly_macro = load_bloomberg_sheet(excel_path, "Monthly", MONTHLY_COLUMNS)

    print("Daily raw shape:", daily.shape)
    print("Monthly macro raw shape:", monthly_macro.shape)

    daily_monthly = aggregate_daily_to_monthly(daily)
    print("Aggregated daily-to-monthly shape:", daily_monthly.shape)

    show_missing_report(daily_monthly, "Aggregated daily data before merge")
    show_missing_report(monthly_macro, "Monthly macro data before merge")

    merged = daily_monthly.merge(monthly_macro, on="date", how="inner")
    merged = merged.sort_values("date").reset_index(drop=True)

    print("Merged monthly dataset shape:", merged.shape)
    show_missing_report(merged, "Merged monthly data before variable construction")
    return daily, monthly_macro, merged


def add_log_return(df, price_column, new_column):
    df[new_column] = np.log(df[price_column] / df[price_column].shift(1))


def add_growth_rate(df, level_column, new_column):
    df[new_column] = np.log(df[level_column] / df[level_column].shift(1))


def build_project_variables(monthly_df):
    df = monthly_df.copy()
    df = df.sort_values("date").reset_index(drop=True)

    add_log_return(df, "wti", "wti_return")
    add_log_return(df, "brent", "brent_return")
    add_log_return(df, "sp500", "sp500_return")
    add_log_return(df, "msci_em", "msci_em_return")
    add_log_return(df, "msci_world", "msci_world_return")
    add_log_return(df, "russell2000", "russell2000_return")
    add_log_return(df, "gold", "gold_return")

    df["term_spread"] = df["us10y"] - df["us2y"]
    df["hy_change"] = df["hy_ytw"].diff()
    df["us10y_change"] = df["us10y"].diff()

    add_growth_rate(df, "ip", "ip_growth")
    add_growth_rate(df, "retail_sales", "retail_sales_growth")

    print("\nCheck of expected columns after variable construction:")
    expected_columns = [
        "wti_return",
        "brent_return",
        "sp500_return",
        "msci_em_return",
        "msci_world_return",
        "russell2000_return",
        "gold_return",
        "term_spread",
        "hy_change",
        "sp500_realized_vol",
        "cfnai",
        "ism_mfg",
        "ip_growth",
        "retail_sales_growth",
    ]
    for column in expected_columns:
        print(f"{column}: {'OK' if column in df.columns else 'MISSING'}")

    show_missing_report(df[["date"] + expected_columns], "Main variables after construction")
    return df


def make_summary_statistics(df, columns):
    summary = df[columns].describe().T
    summary["skew"] = df[columns].skew()
    summary["kurtosis"] = df[columns].kurtosis()
    return summary[
        ["count", "mean", "std", "min", "25%", "50%", "75%", "max", "skew", "kurtosis"]
    ].round(4)


def run_adf_table(df, columns):
    rows = []
    for column in columns:
        series = df[column].dropna()
        if len(series) < 20:
            rows.append(
                {
                    "variable": column,
                    "n_obs": len(series),
                    "adf_stat": np.nan,
                    "p_value": np.nan,
                    "stationary_5pct": np.nan,
                }
            )
            continue

        result = adfuller(series, autolag="AIC")
        rows.append(
            {
                "variable": column,
                "n_obs": len(series),
                "adf_stat": round(result[0], 4),
                "p_value": round(result[1], 4),
                "stationary_5pct": result[1] < 0.05,
            }
        )

    return pd.DataFrame(rows)


def decompose_oil_returns(df, oil_return_col="wti_return", activity_col="cfnai", prefix="baseline"):
    sample = df[[oil_return_col, activity_col]].dropna().copy()
    X = sm.add_constant(sample[activity_col])
    model = sm.OLS(sample[oil_return_col], X).fit()

    fitted = pd.Series(index=sample.index, data=model.fittedvalues, name=f"{prefix}_oil_demand_component")
    residual = pd.Series(index=sample.index, data=model.resid, name=f"{prefix}_oil_supply_component")

    out = df.copy()
    out[fitted.name] = fitted
    out[residual.name] = residual
    return out, model


def add_regime_variables(df, oil_col="wti_return", ism_col="ism_mfg"):
    out = df.copy()
    out["expansion"] = np.where(out[ism_col] > 50, 1, 0)
    out["contraction"] = np.where(out[ism_col] <= 50, 1, 0)
    out["oil_expansion"] = out[oil_col] * out["expansion"]
    out["oil_contraction"] = out[oil_col] * out["contraction"]
    return out


def fit_predictive_regression(df, dependent_col, predictor_cols, horizon=1, cov_type="HC1"):
    work = df.copy()
    work["y_next"] = work[dependent_col].shift(-horizon)
    if dependent_col in predictor_cols:
        work = work.rename(columns={dependent_col: f"{dependent_col}_current"})
        predictor_cols = [
            f"{dependent_col}_current" if col == dependent_col else col for col in predictor_cols
        ]

    regression_columns = ["y_next"] + predictor_cols
    sample = work[regression_columns].dropna().copy()

    y = sample["y_next"]
    X = sm.add_constant(sample[predictor_cols])
    model = sm.OLS(y, X).fit(cov_type=cov_type)
    return model, sample


def regression_results_table(model):
    table = pd.DataFrame(
        {
            "coef": model.params,
            "std_err": model.bse,
            "t_stat": model.tvalues,
            "p_value": model.pvalues,
        }
    )
    return table.round(4)


def interpret_two_component_model(model, demand_name, supply_name):
    lines = []
    for variable, label in [(demand_name, "Demand-related oil component"), (supply_name, "Supply-related oil component")]:
        if variable not in model.params.index:
            continue
        coef = model.params[variable]
        p_value = model.pvalues[variable]
        sign = "positive" if coef > 0 else "negative"
        strength = "statistically significant" if p_value < 0.05 else "not statistically significant"
        lines.append(
            f"{label}: coefficient is {sign} ({coef:.4f}) and {strength} at the 5% level (p-value = {p_value:.4f})."
        )
    return lines


def granger_pvalue_table(df, cause_col, effect_col, max_lag=3):
    sample = df[[effect_col, cause_col]].dropna().copy()
    results = grangercausalitytests(sample[[effect_col, cause_col]], maxlag=max_lag, verbose=False)

    rows = []
    for lag in range(1, max_lag + 1):
        p_value = results[lag][0]["ssr_ftest"][1]
        rows.append({"lag": lag, "p_value": round(p_value, 4)})

    out = pd.DataFrame(rows)
    out["cause"] = cause_col
    out["effect"] = effect_col
    return out[["cause", "effect", "lag", "p_value"]]


def choose_var_lag(var_df, maxlags=6):
    model = VAR(var_df)
    lag_selection = model.select_order(maxlags=maxlags)
    lag_table = pd.DataFrame([lag_selection.selected_orders]).rename(index={0: "selected_lag"})
    return lag_selection, lag_table


def fit_var_model(var_df, chosen_lag):
    model = VAR(var_df)
    results = model.fit(chosen_lag)
    return results


def historical_mean_forecast(train_series):
    return train_series.mean()


def rolling_forecast_comparison(df, target_col, raw_oil_col, demand_col, supply_col, controls, start_share=0.6):
    work = df.copy()
    work["target_next"] = work[target_col].shift(-1)
    required_cols = ["date", "target_next", target_col, raw_oil_col, demand_col, supply_col] + controls
    work = work[required_cols].dropna().copy()

    start_index = max(int(len(work) * start_share), 36)
    forecasts = []

    for i in range(start_index, len(work)):
        train = work.iloc[:i].copy()
        test = work.iloc[i : i + 1].copy()

        if len(test) == 0:
            continue

        benchmark_forecast = historical_mean_forecast(train["target_next"])

        raw_predictors = [target_col, raw_oil_col] + controls
        X_raw = sm.add_constant(train[raw_predictors])
        raw_model = sm.OLS(train["target_next"], X_raw).fit()
        raw_forecast = raw_model.predict(sm.add_constant(test[raw_predictors], has_constant="add")).iloc[0]

        decomposition_predictors = [target_col, demand_col, supply_col] + controls
        X_decomp = sm.add_constant(train[decomposition_predictors])
        decomp_model = sm.OLS(train["target_next"], X_decomp).fit()
        decomp_forecast = decomp_model.predict(
            sm.add_constant(test[decomposition_predictors], has_constant="add")
        ).iloc[0]

        forecasts.append(
            {
                "date": test["date"].iloc[0],
                "actual": test["target_next"].iloc[0],
                "benchmark": benchmark_forecast,
                "raw_oil_model": raw_forecast,
                "decomposition_model": decomp_forecast,
            }
        )

    forecast_df = pd.DataFrame(forecasts)
    metrics = []
    for model_name in ["benchmark", "raw_oil_model", "decomposition_model"]:
        errors = forecast_df[model_name] - forecast_df["actual"]
        metrics.append(
            {
                "model": model_name,
                "rmse": np.sqrt(np.mean(errors**2)),
                "mae": np.mean(np.abs(errors)),
            }
        )

    metrics_df = pd.DataFrame(metrics).round(4)
    return forecast_df, metrics_df


def split_sample(df, split_date):
    early = df[df["date"] < split_date].copy()
    late = df[df["date"] >= split_date].copy()
    return early, late


def normality_check(series):
    series = series.dropna()
    if len(series) < 8:
        return {"statistic": np.nan, "p_value": np.nan}

    statistic, p_value = stats.jarque_bera(series)
    return {"statistic": round(statistic, 4), "p_value": round(p_value, 4)}


def plot_time_series(df, columns, title, figsize=(12, 8)):
    ax = df.set_index("date")[columns].plot(subplots=True, figsize=figsize, sharex=True, title=title)
    plt.tight_layout()
    return ax
