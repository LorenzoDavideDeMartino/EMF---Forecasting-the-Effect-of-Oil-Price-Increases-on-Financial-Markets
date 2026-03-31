# Guide du notebook `emi_oil_market_ARv1.ipynb`

## Question de recherche

Est-ce que les hausses du prix du petrole ont des effets differents sur les marches financiers selon qu'elles sont liees a la **demande** (activite economique) ou a un facteur **residuel** (offre, geopolitique, speculation) ?

L'idee centrale : si le petrole monte parce que l'economie va bien (demande), l'effet sur les actions est different de quand le petrole monte a cause d'un choc d'offre (guerre, OPEP, etc.).

---

## Vue d'ensemble

Le notebook suit un pipeline lineaire en 14 etapes. Chaque section depend de la precedente :

```
Donnees brutes (Excel)
  -> Nettoyage + aggregation mensuelle
    -> Construction de variables (log-rendements, spreads)
      -> Diagnostics statistiques
        -> Decomposition du petrole (demande vs offre)
          -> Regressions predictives
          -> Tests de causalite
          -> Modele VAR + reponses impulsionnelles
          -> Prevision hors-echantillon
          -> Tests de robustesse
            -> Conclusions
```

---

## Section 1 — Introduction (Cell 0)

**But** : Poser la question et le cadre methodologique.

**Pourquoi c'est important** : On precise d'emblee que l'approche est en **forme reduite** (on ne pretend pas identifier structurellement l'offre et la demande, on decompose statistiquement). Ca fixe les attentes pour toute la suite.

---

## Section 2 — Imports (Cells 1-2)

**Ce qu'on charge** :
- `pandas` / `numpy` : manipulation de donnees
- `statsmodels` : VAR, tests ADF, Granger, Ljung-Box
- `scipy.stats` : Jarque-Bera, distribution chi2, distribution t de Student
- `scipy.optimize.minimize` : optimisation numerique pour le MA(1)
- `matplotlib` : graphiques

**Pourquoi tout charger en une fois** : Le notebook est self-contained (pas d'import depuis `src/`). Tout est defini dans le notebook lui-meme pour que n'importe qui puisse le lire et le reproduire sans avoir besoin du reste du repo.

---

## Section 3 — Fonctions helpers (Cells 3-44)

C'est le coeur technique. **42 cellules** qui definissent toutes les fonctions avant de les utiliser. Chaque fonction a sa propre cellule pour pouvoir etre lue et comprise independamment.

### 3a. Constantes (Cells 4-5)

```python
DAILY_COLUMNS = ["date", "wti", "brent", "sp500", "msci_em", "us10y", "us2y", "hy_ytw", "gold"]
MONTHLY_COLUMNS = ["date", "cfnai", "ism_mfg"]
SHEET_USECOLS = {"Daily": [0, 1, 2, 6, 8, 10, 11, 12, 13], "Monthly": [0, 2, 3]}
```

**Pourquoi** : Le fichier Excel contient beaucoup plus de colonnes que ce dont on a besoin. `SHEET_USECOLS` selectionne uniquement les colonnes utiles au projet. Les noms courts (`wti`, `sp500`...) remplacent les libelles Bloomberg longs et compliques.

---

### 3b. Chargement des donnees (Cells 6-8)

**`load_data_sheet()`** : Lit une feuille Excel, nettoie les en-tetes Bloomberg (les 5 premieres lignes sont du metadata), convertit les dates et les chiffres.

**`aggregate_daily_to_monthly()`** : Transforme les donnees journalieres en mensuelles.

**Pourquoi passer au mensuel** : Les donnees macro (CFNAI, ISM) ne sont disponibles qu'en mensuel. Pour pouvoir les utiliser comme regresseurs, il faut que tout soit a la meme frequence.

**Comment** :
- On prend la **derniere observation du mois** pour les prix (WTI, S&P 500, etc.)
- On calcule la **volatilite realisee** du S&P 500 = ecart-type des log-rendements journaliers dans le mois. C'est une mesure de risque qu'on utilisera comme variable de controle plus tard.

**Pourquoi la derniere obs et pas la moyenne** : En finance, on utilise le dernier prix du mois pour calculer les rendements mensuels (c'est le standard). La moyenne lisserait trop et introduirait un biais.

---

### 3c. Construction des variables (Cells 9-11)

**`add_log_return()`** : Calcule `ln(P_t / P_{t-1})` — le log-rendement.

**Pourquoi des log-rendements** : 
1. Ils sont additifs dans le temps (le rendement sur 2 mois = somme des rendements mensuels)
2. Ils sont approximativement normaux pour de petites variations
3. C'est le standard en finance empirique et en econometrie financiere

**`build_project_variables()`** : Cree toutes les variables a partir des prix bruts :
- **Log-rendements** : WTI, Brent, S&P 500, MSCI EM, Gold
- **Term spread** : US 10Y - US 2Y (pente de la courbe des taux, indicateur du cycle economique)
- **HY change** : variation mensuelle du yield high-yield (mesure le resserrement/assouplissement du credit)

**Pourquoi ces variables** : Elles couvrent les 3 dimensions du marche financier pertinentes pour notre question :
- **Actions** (S&P 500, MSCI EM) — est-ce que le petrole predit les rendements boursiers ?
- **Credit** (HY spread) — est-ce que le petrole affecte le risque de credit ?
- **Controles** (term spread, gold, volatilite) — pour isoler l'effet propre du petrole

---

### 3d. Test ADF de stationnarite (Cell 12-13)

**`run_adf_table()`** : Applique le test Augmented Dickey-Fuller a chaque serie.

**Pourquoi tester la stationnarite** : Toute la suite (regressions, VAR, Granger) suppose que les series sont stationnaires. Si une serie a une racine unitaire (tendance stochastique), les t-stats classiques sont invalides et les regressions peuvent etre fallacieuses (spurious regression).

**Methode** : `adfuller(series, autolag="AIC")` — le nombre de retards est choisi automatiquement par le critere AIC.

**Ce qu'on espere** : p-value < 0.05 pour toutes les series → on peut les utiliser telles quelles.

---

### 3e. Ljung-Box et Jarque-Bera (Cells 14-16)

**`run_ljungbox_jb_table()`** : Deux tests complementaires :

1. **Ljung-Box** : Teste si les donnees sont autocorrelees (est-ce que la valeur d'aujourd'hui depend des valeurs passees ?). On teste aux lags 6 et 12.
   - **Pourquoi c'est important** : Si les residus d'un modele sont autocorreles, les erreurs standards sont biaisees et les tests d'hypothese ne sont pas fiables.

2. **Jarque-Bera** : Teste si les donnees suivent une loi normale (basee sur la skewness et la kurtosis).
   - **Pourquoi** : Beaucoup de procedures statistiques supposent la normalite. Si les donnees ne sont pas normales, il faut utiliser des erreurs standards robustes (ce qu'on fait avec HC1 plus tard).

**`run_diagnostic_residuals()`** : Meme logique mais appliquee aux residus d'un modele (utilisee apres chaque regression pour verifier que le modele est bien specifie).

---

### 3f. OLS from scratch (Cells 17-19)

**`ols_from_scratch()`** : Regression OLS implementee a la main.

**Pourquoi ne pas juste utiliser statsmodels** : C'est pedagogique — on montre exactement ce qui se passe :

```
beta = (X'X)^{-1} X'y        ← estimateur OLS
sigma2 = SSR / (T - k - 1)   ← variance des residus
var(beta) = sigma2 * (X'X)^{-1}  ← matrice de variance-covariance
se = sqrt(diag(var(beta)))    ← erreurs standards
t = beta / se                 ← statistiques de test
p = 2 * P(|t| > |t_obs|)     ← p-values bilaterales
```

**`ols_summary_df()`** : Formate les resultats en DataFrame propre.

---

### 3g. MA(1) MLE (Cells 20-25)

C'est la partie la plus technique. **Pourquoi en a-t-on besoin** : Quand on fait la decomposition OLS du petrole (Section 8), les residus montrent de l'autocorrelation. Ca veut dire que le modele OLS simple est mal specifie. La correction MA(1) resout ce probleme.

**`ma_innovations(u, theta)`** : Inversion recursive du processus MA(1).
- Si les erreurs suivent `u_t = epsilon_t + theta * epsilon_{t-1}`, on retrouve les innovations `epsilon_t` par :
  ```
  epsilon_0 = u_0
  epsilon_t = u_t - theta * epsilon_{t-1}
  ```

**`_loglik_contributions()`** : Calcule la log-vraisemblance de chaque observation (necessaire pour les erreurs standards OPG).

**`_negloglik_concentrated()`** : Log-vraisemblance negative totale a minimiser. "Concentree" car sigma2 est estime analytiquement a chaque evaluation.

**`opg_standard_errors()`** : Erreurs standards OPG (Outer Product of Gradients).
- **Pourquoi OPG et pas Hessienne** : L'OPG ne necessite que le gradient (premiere derivee), pas la Hessienne (seconde derivee). On les calcule par differences finies numeriques. C'est plus simple et suffisamment precis pour notre usage.

**`estimate_ma1()`** : Orchestre tout :
1. Fait d'abord un OLS classique pour avoir un point de depart
2. Optimise la vraisemblance avec Nelder-Mead (algorithme sans gradient, robuste)
3. Calcule les erreurs standards OPG au point optimal

**`ma1_comparison_table()`** : Met cote a cote les resultats OLS et MLE pour comparer.

---

### 3h. Decomposition petroliere (Cells 26-29)

**C'est la piece maitresse du projet.**

**Approche A — OLS** : `decompose_oil_returns_scratch()`
```
r_wti = alpha + beta * CFNAI + epsilon
```
- **Fitted values** (`alpha + beta * CFNAI`) = composante **demande**
  - Interpretation : la partie du rendement petrolier qui est expliquee par l'activite economique
- **Residus** (`epsilon`) = composante **offre/residuelle**
  - Interpretation : tout ce qui n'est pas lie a la demande (chocs d'offre, geopolitique, speculation)

**Pourquoi le CFNAI** : Le Chicago Fed National Activity Index est un indice composite de 85 indicateurs d'activite economique. C'est un proxy large et reconnu de la demande globale.

**`decompose_oil_returns()`** : Meme chose mais avec `statsmodels` au lieu de from scratch. Utile pour les tests de robustesse.

**Approche B — Regimes ISM** : `add_regime_variables()`
- Si ISM > 50 → **expansion** (l'economie croit)
- Si ISM <= 50 → **contraction** (l'economie decroit)
- On cree : `oil_expansion` = rendement petrolier × dummy expansion
- Et : `oil_contraction` = rendement petrolier × dummy contraction

**Pourquoi deux approches** : Ca montre que les resultats ne dependent pas d'un choix methodologique unique. Si les deux approches pointent dans la meme direction, les conclusions sont plus robustes.

---

### 3i. Regressions predictives (Cells 30-33)

**`fit_predictive_regression()`** :
```
y_{t+1} = alpha + beta_1 * demand_t + beta_2 * supply_t + controles_t + epsilon
```

**Le decalage `shift(-1)` est crucial** : On predit le rendement du mois **suivant** avec les variables du mois **courant**. Sans ce decalage, on aurait une regression contemporaine (correlation) et pas une regression predictive (causalite au sens de Granger).

**Erreurs robustes HC1** : Comme les donnees financieres sont heteroscedastiques (la variance change dans le temps), les erreurs standards classiques sont biaisees. HC1 corrige ca.

**`interpret_two_component_model()`** : Resume automatiquement si chaque composante est significative et dans quel sens.

---

### 3j. Coefficients rolling (Cells 34-35)

**`rolling_predictive_coefficients(window=60)`** : Estime la regression predictive sur une fenetre glissante de 60 mois.

**Pourquoi** : Pour verifier que la relation demande/offre est **stable dans le temps**. Si le coefficient change de signe ou disparait a certaines periodes, la relation n'est pas fiable.

---

### 3k. Granger causality (Cells 36-37)

**`granger_pvalue_table()`** : Test de Granger — est-ce que les valeurs passees de X aident a predire Y au-dela de ce que les valeurs passees de Y predisent deja ?

**Methode** : On compare deux modeles :
- Restreint : `Y_t = f(Y_{t-1}, ..., Y_{t-p})`
- Non-restreint : `Y_t = f(Y_{t-1}, ..., Y_{t-p}, X_{t-1}, ..., X_{t-p})`
- F-test sur la difference de SSR

**Ce qu'on teste** : Est-ce que la composante demande ou offre du petrole "Granger-cause" les rendements actions ou le spread HY ?

---

### 3l. Mesures de Geweke (Cells 38-39)

**`geweke_causality()`** : Approche plus riche que Granger — decompose la dependance totale en 3 parties :

1. **C_{2→1}** : Causalite de var2 vers var1 (est-ce que les lags de WTI aident a predire S&P ?)
2. **C_{1→2}** : Causalite de var1 vers var2 (l'inverse)
3. **C_inst** : Dependance instantanee (correlation contemporaine non expliquee par les lags)
4. **C_total** = C_{2→1} + C_{1→2} + C_inst

**Pourquoi Geweke en plus de Granger** : Geweke permet de quantifier la **taille** de la causalite (pas juste un oui/non), et de decomposer en directionnelle + instantanee.

**Test** : `T * C ~ chi2(df)` — test asymptotique.

---

### 3m. VAR et prevision (Cells 40-44)

**`choose_var_lag()`** : Selection du nombre de retards via BIC (critere d'information bayesien — favorise la parcimonie).

**`fit_var_model()`** : Estime un VAR en forme reduite (chaque variable est regressee sur les lags de toutes les variables).

**`rolling_forecast_comparison()`** : Compare 3 modeles en prevision hors-echantillon :
1. **Benchmark** : moyenne historique (difficile a battre en finance)
2. **Modele brut** : WTI comme seul predicteur petrolier
3. **Modele decompose** : composantes demande + offre separees

**Pourquoi cette comparaison** : Si le modele decompose ne bat pas le benchmark, la decomposition n'a pas de valeur ajoutee pratique pour la prevision (meme si les coefficients sont significatifs in-sample).

---

## Section 4 — Chargement des donnees (Cells 45-47)

**Pourquoi on en est la** : Toutes les fonctions sont definies, on peut maintenant les appliquer.

On charge le fichier Excel et on obtient :
- `daily_raw` : 9443 observations journalieres (jan 1990 - mars 2026)
- `monthly_raw` : 435 observations mensuelles (CFNAI + ISM)

---

## Section 5 — Aggregation mensuelle (Cells 48-49)

**Transition Cell 47 → 49** : On a des donnees journalieres et des donnees mensuelles. Il faut les fusionner. Donc on convertit d'abord le journalier en mensuel, puis on fait un merge.

**Output** : `monthly_merged` (434 lignes, 12 colonnes) — un seul DataFrame mensuel unifie.

**Pourquoi inner join** : On ne garde que les mois ou on a a la fois les donnees de marche ET les donnees macro. Pas de donnees manquantes dans les regresseurs.

---

## Section 6 — Construction des variables (Cells 50-51)

**Transition Cell 49 → 51** : On a les prix mensuels, mais les regressions necessitent des rendements et des spreads (pas des niveaux). Il faut donc transformer.

**Output** : `project_df` (434 lignes, 19 colonnes) avec toutes les variables pretes pour l'analyse.

---

## Section 7 — Diagnostics (Cells 52-60)

**Transition Cell 51 → 53** : Avant de modeliser, il faut comprendre les donnees. C'est une etape standard en econometrie.

**Pourquoi dans cet ordre** :
1. **Stats descriptives** (Cell 53) : On verifie les ordres de grandeur, la dispersion, la skewness (asymetrie) et la kurtosis (queues epaisses). Les donnees financieres ont typiquement une kurtosis elevee (gros chocs rares).

2. **Correlations** (Cell 54) : On repere les relations bivariees avant de passer aux regressions multivariees. Si deux variables sont tres correlees, il faudra faire attention a la multicolinearite.

3. **Graphiques temporels** (Cell 55) : On visualise les series pour reperer les breaks structurels, les outliers, les periodes de crise.

4. **Tests ADF** (Cell 56) : On verifie la stationnarite — prerequis pour tout le reste.

5. **Ljung-Box + Jarque-Bera** (Cell 57) : On documente l'autocorrelation et la non-normalite. Ca justifie l'utilisation d'erreurs robustes plus tard.

6. **Volatility clustering** (Cells 59-60) : L'ACF des rendements au carre montre si la volatilite est persistante. C'est un fait stylise classique en finance (les periodes de forte volatilite sont suivies de periodes de forte volatilite).

---

## Section 8 — Decomposition petroliere (Cells 61-71)

**Transition Cell 60 → 62** : Les diagnostics confirment que les series sont stationnaires. On peut maintenant faire la decomposition.

**Pourquoi dans cet ordre** :

1. **OLS from scratch** (Cell 62) : On decompose `r_wti = alpha + beta*CFNAI + epsilon`. On obtient la composante demande (fitted) et offre (residus).

2. **Diagnostics des residus** (Cells 63-64) : On verifie si les residus OLS sont bien "propres" (pas d'autocorrelation). **Resultat** : il y a de l'autocorrelation significative → le modele OLS est mal specifie.

3. **Correction MA(1)** (Cells 66-69) : Puisque les residus OLS sont autocorreles, on estime un modele avec erreurs MA(1) par MLE. On compare : si le beta CFNAI est similaire entre OLS et MLE, la decomposition est robuste malgre le probleme d'autocorrelation.

4. **Regimes ISM** (Cell 70) : Approche alternative qui ne suppose pas une relation lineaire continue entre petrole et activite, mais juste une distinction binaire expansion/contraction.

5. **Graphiques** (Cell 71) : On visualise les deux composantes pour verifier qu'elles ont une interpretation economique sensee.

---

## Section 9 — Regressions predictives (Cells 72-77)

**Transition Cell 71 → 73** : On a maintenant les composantes demande et offre. La question centrale est : est-ce qu'elles predisent differemment les marches ?

1. **Modele decomposition** (Cell 73) : On regresse le rendement du S&P 500 du mois suivant sur les composantes demande/offre + controles. On fait pareil pour le HY spread. 
   - **Question cle** : est-ce que beta_demande ≠ beta_offre ?

2. **Modele regime** (Cell 74) : Meme exercice avec l'approche ISM.
   - **Pourquoi les deux** : Si les deux approches donnent des resultats coherents, c'est plus convaincant.

3. **Coefficients rolling** (Cells 76-77) : On verifie la stabilite dans le temps.
   - **Pourquoi c'est crucial** : Si le coefficient de la composante offre est significatif sur l'echantillon complet mais change de signe a certaines periodes, le resultat n'est pas fiable.

---

## Section 10 — Tests de causalite (Cells 78-81)

**Transition Cell 77 → 79** : Les regressions predictives montrent des coefficients, mais est-ce que c'est vraiment de la "causalite" (au sens statistique) ? Les tests de Granger et Geweke repondent a cette question plus formellement.

1. **Granger** (Cell 79) : Test classique — est-ce que les lags des composantes petrolieres aident a predire S&P / HY ?

2. **Geweke global** (Cell 80) : On travaille ici sur les **variances rolling journalieres** (pas les rendements mensuels). C'est une perspective differente : est-ce que la volatilite du petrole cause la volatilite des actions ?

3. **Geweke par sous-periodes** (Cell 81) : On decoupe en blocs de 5 ans pour voir si la causalite varie dans le temps.

---

## Section 11 — VAR et IRF (Cells 82-86)

**Transition Cell 81 → 83** : Les tests de causalite sont bivaries (2 variables a la fois). Le VAR permet d'analyser le systeme complet (6 variables simultanement).

1. **Selection du lag** (Cell 83) : On choisit le nombre de retards par BIC. Trop peu = on rate de la dynamique. Trop = surparametrisation.

2. **Estimation + diagnostics** (Cell 84) : On estime le VAR et on verifie :
   - **Stabilite** : toutes les racines sont dans le cercle unite ?
   - **Ljung-Box sur les residus** : les residus du VAR sont-ils propres ?

3. **IRF — Impulse Response Functions** (Cell 85) : On simule un choc de 1 ecart-type sur le WTI et on regarde comment le S&P 500 et le HY spread reagissent sur 24 mois. Les bandes de confiance sont calculees par Monte Carlo (300 replications).
   - **Pourquoi orthogonalise** : On utilise la decomposition de Cholesky pour isoler les chocs orthogonaux. L'ordre des variables compte.

4. **FEVD** (Cell 86) : Quelle part de la variance de prevision du S&P 500 est expliquee par les chocs petroliers a horizon 12 mois ?

---

## Section 12 — Prevision hors-echantillon (Cells 87-90)

**Transition Cell 86 → 88** : Tout ce qui precede est **in-sample** (on utilise toutes les donnees pour estimer et evaluer). La prevision OOS est le test ultime : est-ce que le modele predit bien sur des donnees qu'il n'a jamais vues ?

1. **Comparaison rolling OLS** (Cell 88) : 3 modeles en competition. On utilise 60% des donnees pour la premiere estimation, puis on avance mois par mois.
   - **RMSE** (Root Mean Squared Error) : penalise les grosses erreurs
   - **MAE** (Mean Absolute Error) : plus robuste aux outliers

2. **Prevision VAR** (Cells 89-90) : On entraine le VAR sur les donnees avant 2020 et on prevoit les 12 mois suivants. 
   - **Pourquoi 2020** : Ca inclut le COVID — un vrai test de stress pour le modele.

---

## Section 13 — Robustesse (Cells 91-93)

**Transition Cell 90 → 92** : On a des resultats. Mais sont-ils fragiles ? On teste 3 variations :

1. **Brent au lieu de WTI** : Si les resultats disparaissent en changeant le benchmark petrolier, ils ne sont pas robustes.

2. **MSCI EM au lieu de S&P 500** : Est-ce que l'effet petrole est specifique aux US ou generalise aux emergents ?

3. **Sous-periodes** (Cell 93) :
   - **1990-2007** : periode pre-crise, marche petrolier "classique"
   - **2008-2014** : crise financiere + revolution du shale
   - **2015-2026** : post-shale, COVID, guerre en Ukraine

---

## Section 14 — Conclusions (Cells 94-95)

**Transition Cell 93 → 95** : On resume les resultats principaux automatiquement.

**Message central** : La composante offre/residuelle du petrole est significative pour predire les changements du spread HY (credit), mais pas les rendements du S&P 500. La composante demande n'est significative pour aucune des deux cibles. Cela suggere que ce sont les chocs d'offre petroliers qui affectent le plus le marche du credit.

---

## Resume des methodes statistiques utilisees

| Methode | Ou dans le notebook | Pourquoi |
|---|---|---|
| Log-rendements | Section 6 | Standard en finance, additivite temporelle |
| ADF | Section 7 | Verifier la stationnarite avant de modeliser |
| Ljung-Box | Sections 7, 8, 9 | Detecter l'autocorrelation dans les series et les residus |
| Jarque-Bera | Section 7 | Tester la normalite |
| OLS from scratch | Section 8 | Decomposition petrole = demande + offre |
| MA(1) MLE | Section 8 | Corriger l'autocorrelation des residus OLS |
| OPG standard errors | Section 8 | Erreurs standards pour le MLE sans Hessienne |
| Regressions predictives HC1 | Section 9 | Tester si les composantes predisent les marches |
| Rolling coefficients | Section 9 | Verifier la stabilite temporelle |
| Granger causality | Section 10 | Test formel de precedence temporelle |
| Geweke causality | Section 10 | Decomposition directionnelle + instantanee |
| VAR | Section 11 | Modelisation multivariee du systeme complet |
| IRF + FEVD | Section 11 | Propagation des chocs + decomposition de variance |
| Rolling OOS forecasts | Section 12 | Validation predictive hors-echantillon |
| Robustesse | Section 13 | Sensibilite aux choix methodologiques |

---

## Glossaire rapide

- **CFNAI** : Chicago Fed National Activity Index — composite de 85 indicateurs d'activite economique US
- **ISM** : Institute for Supply Management Manufacturing Index — au-dessus de 50 = expansion
- **HY** : High Yield — obligations a haut rendement (junk bonds), le spread mesure le risque de credit
- **Term spread** : Difference entre taux long (10 ans) et court (2 ans) — indicateur de recession quand negatif
- **HC1** : Heteroskedasticity-Consistent standard errors (White, 1980) — corrige les erreurs standards quand la variance des residus n'est pas constante
- **ADF** : Augmented Dickey-Fuller — teste si une serie a une racine unitaire
- **IRF** : Impulse Response Function — comment une variable reagit a un choc sur une autre
- **FEVD** : Forecast Error Variance Decomposition — quelle part de l'incertitude de prevision vient de quel choc
- **OPG** : Outer Product of Gradients — methode d'estimation de la matrice de variance-covariance des parametres MLE
