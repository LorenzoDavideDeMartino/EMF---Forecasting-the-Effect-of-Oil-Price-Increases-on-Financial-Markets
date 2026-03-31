from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import adfuller, grangercausalitytests


DEFAULT_DATA_PATH = Path("data/raw/data_hec_projet_1.xlsx")
if not DEFAULT_DATA_PATH.exists():
    DEFAULT_DATA_PATH = Path("../data/raw/data_hec_projet_1.xlsx")  # solution de secours si le script est lance depuis notebooks/

DAILY_COLUMNS = [
    "date",
    "wti",
    "brent",
    "sp500",
    "msci_em",
    "us10y",
    "us2y",
    "hy_ytw",
    "gold"]

MONTHLY_COLUMNS = [
    "date",
    "cfnai",
    "ism_mfg"]

SHEET_USECOLS = {
    "Daily": [0, 1, 2, 6, 8, 10, 11, 12, 13],
    "Monthly": [0, 2, 3],
}


def load_data_sheet(excel_path, sheet_name, columns):
    raw = pd.read_excel(
        excel_path,
        sheet_name=sheet_name,
        header=None,
        usecols=SHEET_USECOLS[sheet_name],
    )  # on charge seulement les colonnes utiles au projet
    data = raw.iloc[5:].copy()  # on garde seulement la partie ou la vraie table commence
    data.columns = columns  # on remplace les libelles Bloomberg par des noms courts utiles pour le projet

    first_value = str(data.iloc[0, 0]).strip().lower()  # on verifie si la premiere ligne restante est encore la ligne "Dates"
    if first_value == "dates":
        data = data.iloc[1:].copy()  # on la retire car c'est encore du metadata, pas une observation

    data["date"] = pd.to_datetime(data["date"])  # on convertit les dates avant le tri et les fusions

    for column in columns[1:]:
        data[column] = pd.to_numeric(data[column], errors="coerce")  # on force les series en numerique et on transforme les cellules invalides en NaN

    data = data.sort_values("date").reset_index(drop=True)  # on garde un echantillon proprement ordonne dans le temps
    return data
def aggregate_daily_to_monthly(daily_df):
    monthly_data = daily_df.resample("M", on="date").last().reset_index()  # on garde la derniere observation de chaque mois pour toutes les series de marche

    sp500_daily_returns = daily_df[["date", "sp500"]].copy()  # on isole le S&P 500 car il sert au calcul de la volatilite realisee
    sp500_daily_returns["sp500_daily_log_return"] = np.log(sp500_daily_returns["sp500"]).diff()  # on calcule les rendements journaliers en log

    monthly_volatility = (
        sp500_daily_returns.resample("M", on="date")["sp500_daily_log_return"]
        .std()  # l'ecart-type des rendements journaliers dans le mois sert de mesure simple de volatilite realisee
        .rename("sp500_realized_vol")
        .reset_index()
    )

    monthly_data = monthly_data.merge(monthly_volatility, on="date", how="left")  # on ajoute la volatilite mensuelle au jeu de donnees mensuel
    return monthly_data


def prepare_monthly_dataset(excel_path=DEFAULT_DATA_PATH):
    daily = load_data_sheet(excel_path, "Daily", DAILY_COLUMNS)  # on charge les series journalieres de marche
    monthly_macro = load_data_sheet(excel_path, "Monthly", MONTHLY_COLUMNS)  # on charge les series macro mensuelles

    print("Daily raw shape:", daily.shape)
    print("Monthly macro raw shape:", monthly_macro.shape)

    monthly_market_data = aggregate_daily_to_monthly(daily)  # on transforme les donnees de marche journalieres en donnees mensuelles
    print("Aggregated daily-to-monthly shape:", monthly_market_data.shape)

    merged = monthly_market_data.merge(monthly_macro, on="date", how="inner")  # on garde seulement les mois communs aux donnees de marche et macro
    merged = merged.sort_values("date").reset_index(drop=True)  # on garde un ordre chronologique propre pour les etapes suivantes

    print("Merged monthly dataset shape:", merged.shape)
    return daily, monthly_macro, merged


def add_log_return(df, price_column, new_column):
    df[new_column] = np.log(df[price_column] / df[price_column].shift(1))  # on utilise les rendements log car ils sont standards en finance empirique


def build_project_variables(monthly_df):
    df = monthly_df.copy()
    df = df.sort_values("date").reset_index(drop=True)  # on garde un ordre mensuel propre avant de creer rendements et retards

    add_log_return(df, "wti", "wti_return")  # rendement petrolier principal pour l'analyse de base
    add_log_return(df, "brent", "brent_return")  # proxy alternatif du petrole pour la robustesse
    add_log_return(df, "sp500", "sp500_return")  # rendement actions principal
    add_log_return(df, "msci_em", "msci_em_return")  # marche actions de robustesse
    add_log_return(df, "gold", "gold_return")  # controle classique de valeur refuge

    df["term_spread"] = df["us10y"] - df["us2y"]  # on garde la pente de la courbe des taux en difference de niveau
    df["hy_change"] = df["hy_ytw"].diff()  # on prend la variation mensuelle pour mesurer le resserrement ou l'assouplissement du credit

    print("\nCheck of expected columns after variable construction:")
    expected_columns = [
        "wti_return",
        "brent_return",
        "sp500_return",
        "msci_em_return",
        "gold_return",
        "term_spread",
        "hy_change",
        "sp500_realized_vol",
        "cfnai",
        "ism_mfg",
    ]
    for column in expected_columns:
        print(f"{column}: {'OK' if column in df.columns else 'MISSING'}")

    return df


def run_adf_table(df, columns):
    rows = []
    for column in columns:
        series = df[column].dropna()  # chaque test est fait sur l'echantillon effectivement disponible
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

        result = adfuller(series, autolag="AIC")  # on laisse le test choisir automatiquement le nombre de retards
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
    sample = df[[oil_return_col, activity_col]].dropna().copy()  # on garde seulement les mois ou petrole et activite sont observes
    X = sm.add_constant(sample[activity_col])  # on ajoute une constante car le rendement moyen du petrole n'est pas necessairement nul
    model = sm.OLS(sample[oil_return_col], X).fit()  # regression en forme reduite, pas identification structurelle

    fitted = pd.Series(index=sample.index, data=model.fittedvalues, name=f"{prefix}_oil_demand_component")  # partie ajustee = composante liee a la demande par construction
    residual = pd.Series(index=sample.index, data=model.resid, name=f"{prefix}_oil_supply_component")  # residu = composante non liee a la demande

    out = df.copy()
    out[fitted.name] = fitted
    out[residual.name] = residual
    return out, model


def add_regime_variables(df, oil_col="wti_return", ism_col="ism_mfg"):
    out = df.copy()
    out["expansion"] = np.where(out[ism_col] > 50, 1, 0)  # ISM au-dessus de 50 correspond a une regle simple d'expansion
    out["contraction"] = np.where(out[ism_col] <= 50, 1, 0)  # le complement donne le regime de contraction
    out["oil_expansion"] = out[oil_col] * out["expansion"]  # effet du petrole pendant les phases d'expansion
    out["oil_contraction"] = out[oil_col] * out["contraction"]  # effet du petrole pendant les phases de contraction
    return out


def fit_predictive_regression(df, dependent_col, predictor_cols, horizon=1, cov_type="HC1"):
    work = df.copy()
    work["y_next"] = work[dependent_col].shift(-horizon)  # on decale la variable a expliquer pour que X_t predise bien Y_{t+1}
    if dependent_col in predictor_cols:
        work = work.rename(columns={dependent_col: f"{dependent_col}_current"})  # on renomme la valeur courante pour eviter toute confusion avec la cible decalee
        predictor_cols = [
            f"{dependent_col}_current" if col == dependent_col else col for col in predictor_cols
        ]

    regression_columns = ["y_next"] + predictor_cols
    sample = work[regression_columns].dropna().copy()  # on ne retire les NaN qu'au dernier moment pour conserver le plus d'information possible

    y = sample["y_next"]
    X = sm.add_constant(sample[predictor_cols])  # on inclut une constante dans chaque regression predictive
    model = sm.OLS(y, X).fit(cov_type=cov_type)  # on utilise des erreurs standards robustes a l'heteroskedasticite
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
    return table.round(4)  # on arrondit pour garder des tableaux lisibles dans le notebook et le PDF


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
    sample = df[[effect_col, cause_col]].dropna().copy()  # on garde seulement l'echantillon bivariate utile pour ce test
    results = grangercausalitytests(sample[[effect_col, cause_col]], maxlag=max_lag, verbose=False)  # on teste un petit nombre de retards adapte aux donnees mensuelles

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
    lag_selection = model.select_order(maxlags=maxlags)  # on compare les criteres d'information avant d'estimer le VAR
    lag_table = pd.DataFrame([lag_selection.selected_orders]).rename(index={0: "selected_lag"})
    return lag_selection, lag_table


def fit_var_model(var_df, chosen_lag):
    model = VAR(var_df)
    results = model.fit(chosen_lag)  # on estime le VAR en forme reduite avec le nombre de retards choisi
    return results


def historical_mean_forecast(train_series):
    return train_series.mean()  # benchmark simple: predire le mois suivant avec la moyenne historique observee jusque-la


def rolling_forecast_comparison(df, target_col, raw_oil_col, demand_col, supply_col, controls, start_share=0.6):
    work = df.copy()
    work["target_next"] = work[target_col].shift(-1)  # on definit la cible de prevision un mois en avance
    required_cols = ["date", "target_next", target_col, raw_oil_col, demand_col, supply_col] + controls
    work = work[required_cols].dropna().copy()  # on garde seulement les colonnes necessaires a la comparaison de prevision

    start_index = max(int(len(work) * start_share), 36)  # on attend d'avoir une fenetre d'estimation suffisante
    forecasts = []

    for i in range(start_index, len(work)):
        train = work.iloc[:i].copy()  # on utilise uniquement l'information disponible jusqu'a la date t
        test = work.iloc[i : i + 1].copy()  # on predit seulement le mois suivant

        if len(test) == 0:
            continue

        benchmark_forecast = historical_mean_forecast(train["target_next"])  # benchmark naif

        raw_predictors = [target_col, raw_oil_col] + controls
        X_raw = sm.add_constant(train[raw_predictors])
        raw_model = sm.OLS(train["target_next"], X_raw).fit()  # modele qui traite le petrole comme une seule serie de rendement
        raw_forecast = raw_model.predict(sm.add_constant(test[raw_predictors], has_constant="add")).iloc[0]

        decomposition_predictors = [target_col, demand_col, supply_col] + controls
        X_decomp = sm.add_constant(train[decomposition_predictors])
        decomp_model = sm.OLS(train["target_next"], X_decomp).fit()  # modele qui distingue composante liee a la demande et composante residuelle
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

    forecast_df = pd.DataFrame(forecasts)  # on rassemble toutes les previsions recursives dans un seul tableau
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

    metrics_df = pd.DataFrame(metrics).round(4)  # RMSE et MAE gardent une comparaison courte et facile a expliquer
    return forecast_df, metrics_df


def split_sample(df, split_date):
    early = df[df["date"] < split_date].copy()  # premiere sous-periode
    late = df[df["date"] >= split_date].copy()  # seconde sous-periode
    return early, late
