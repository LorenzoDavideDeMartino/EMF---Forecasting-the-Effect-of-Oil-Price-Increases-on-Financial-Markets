# Guide du notebook `emi_oil_market_ARv1.ipynb`

## Le projet en bref

Ce notebook est le livrable principal du projet de groupe EMIF (Econometrie des Marches et Instruments Financiers). La question du projet est :

> **Comment peut-on prevoir l'effet d'une hausse du prix du petrole sur les marches financiers ?**

Le projet combine les **Proposals 1 et 2** du brief :
- **Proposal 1** (VAR + Granger + IRF) : modelisation multivariee, causalite, reponses impulsionnelles (Classes 5-6)
- **Proposal 2** (Asymetrie + Regressions predictives) : decomposition offre/demande, prevision hors-echantillon (Classes 3-4)

L'idee centrale est simple : quand le petrole monte, est-ce parce que l'economie va bien (hausse de la **demande**) ou parce qu'il y a un choc d'offre (guerre, OPEP, geopolitique) ? Ces deux causes ont des effets opposes sur les marches :
- **Petrole monte par la demande** → l'economie tourne bien → les actions montent aussi → effet positif ou neutre
- **Petrole monte par l'offre** → cout en plus pour les entreprises sans croissance → les actions baissent, le credit se tend → effet negatif

Le notebook teste empiriquement cette hypothese sur la periode **1990-2026** avec des donnees Bloomberg.

---

## Donnees utilisees

| Source | Frequence | Variables | Usage |
|---|---|---|---|
| Excel "Daily" | Journalier (9443 obs, 1990-2026) | WTI, Brent, S&P 500, MSCI EM, US 10Y, US 2Y, HY yield, Gold | Prix de marche |
| Excel "Monthly" | Mensuel (435 obs) | CFNAI, ISM Manufacturing | Indicateurs macro d'activite |

Le CFNAI (Chicago Fed National Activity Index) est un composite de 85 indicateurs economiques — c'est notre proxy de la demande globale. L'ISM Manufacturing sert de proxy alternatif plus simple (au-dessus de 50 = expansion, en-dessous = contraction).

---

## Architecture du notebook (96 cellules)

Le notebook est **self-contained** : toutes les fonctions sont definies dans le notebook lui-meme (Cells 3-44), pas d'import depuis `src/`. Ca le rend reproductible par n'importe qui sans installation particuliere.

```
Cells 0-2:   Introduction + Imports
Cells 3-44:  Definition de TOUTES les fonctions (toolkit)
Cells 45-47: Chargement des donnees
Cells 48-49: Aggregation mensuelle
Cells 50-51: Construction des variables
Cells 52-60: Diagnostics statistiques
Cells 61-71: Decomposition du petrole
Cells 72-77: Regressions predictives
Cells 78-81: Tests de causalite
Cells 82-86: VAR + IRF + FEVD
Cells 87-90: Prevision hors-echantillon
Cells 91-93: Tests de robustesse
Cells 94-95: Conclusions
```

---

## Pourquoi cette structure ?

Le pipeline suit la logique standard d'un papier empirique en finance :

1. **D'abord comprendre les donnees** (Sections 4-7) — avant de modeliser, il faut savoir ce qu'on a : les series sont-elles stationnaires ? normales ? autocorrelees ? Sans cette etape, on risque de construire un modele sur des bases fragiles.

2. **Puis decomposer le petrole** (Section 8) — c'est le coeur du projet. On ne peut pas tester l'asymetrie demande/offre sans avoir d'abord construit les deux composantes.

3. **Ensuite tester les predictions** (Sections 9-12) — est-ce que la decomposition a une valeur predictive ? On teste d'abord in-sample (regressions), puis on valide out-of-sample (prevision).

4. **Enfin verifier la robustesse** (Section 13) — les resultats tiennent-ils avec d'autres mesures du petrole ? d'autres marches ? d'autres periodes ?

Chaque section **necessite** que les precedentes soient faites. On ne peut pas faire la decomposition sans les variables, ni les regressions sans la decomposition, ni la robustesse sans les regressions. C'est un pipeline strictement lineaire.

---

## Section par section : pourquoi on passe de l'une a l'autre

### Section 1 — Introduction (Cell 0)

On pose la question de recherche et on precise le cadre : l'approche est en **forme reduite**. Ca veut dire qu'on ne pretend pas identifier structurellement les chocs d'offre et de demande (comme le fait Kilian 2009 avec un SVAR). On decompose statistiquement les rendements petroliers en une partie correlee a l'activite economique (demande) et un residu (tout le reste). C'est plus modeste mais plus transparent.

**→ On passe a la Section 2 parce qu'on a besoin de charger les outils avant de travailler.**

---

### Section 2 — Imports (Cells 1-2)

On charge toutes les librairies Python necessaires. Le notebook utilise :
- `pandas`/`numpy` pour la manipulation de donnees
- `statsmodels` pour les modeles econometriques (VAR, ADF, Granger, Ljung-Box)
- `scipy.stats` pour les tests statistiques (Jarque-Bera, chi2, Student)
- `scipy.optimize.minimize` pour l'estimation MLE du MA(1)
- `matplotlib` pour les graphiques

**→ On passe a la Section 3 pour definir les fonctions qui implementent toute la methodologie.**

---

### Section 3 — Fonctions helpers (Cells 3-44)

42 cellules qui definissent toutes les fonctions. On les definit **avant** de les utiliser pour deux raisons :
1. Le notebook est self-contained (pas de dependance externe)
2. Chaque fonction est dans sa propre cellule pour etre lisible independamment

Les fonctions sont organisees par theme :

| Sous-section | Cells | Fonctions | Lien avec le cours |
|---|---|---|---|
| Constantes | 4-5 | Noms de colonnes, indices Excel | — |
| Chargement donnees | 6-8 | `load_data_sheet()`, `aggregate_daily_to_monthly()` | — |
| Variables | 9-11 | `add_log_return()`, `build_project_variables()` | Classe 2 (rendements) |
| ADF | 12-13 | `run_adf_table()` | Classe 2 (stationnarite) |
| Ljung-Box + JB | 14-16 | `run_ljungbox_jb_table()`, `run_diagnostic_residuals()` | Classe 2 (p.20-35) |
| OLS from scratch | 17-19 | `ols_from_scratch()`, `ols_summary_df()` | Classe 3 (p.12-18) |
| MA(1) MLE | 20-25 | `estimate_ma1()`, `opg_standard_errors()` | Classe 4 (MLE, ARMA) |
| Decomposition | 26-29 | `decompose_oil_returns_scratch()`, `add_regime_variables()` | Classe 3 (OLS) |
| Regressions predictives | 30-33 | `fit_predictive_regression()`, `interpret_two_component_model()` | Classe 3 (p.38) |
| Rolling coefficients | 34-35 | `rolling_predictive_coefficients()` | Classe 3 |
| Granger | 36-37 | `granger_pvalue_table()` | Classe 5 (p.42-45) |
| Geweke | 38-39 | `geweke_causality()` | Classe 6 (p.14-22) |
| VAR + Forecast | 40-44 | `choose_var_lag()`, `fit_var_model()`, `rolling_forecast_comparison()` | Classe 5 (p.17-27) |

**→ On passe a la Section 4 parce que les outils sont prets, il faut maintenant charger les donnees.**

---

### Section 4 — Chargement des donnees (Cells 45-47)

**Cell 46** : On localise le fichier Excel (le chemin change selon qu'on lance le notebook depuis `notebooks/` ou depuis la racine du repo).

**Cell 47** : On charge les deux feuilles :
- `daily_raw` → 9443 lignes × 9 colonnes (prix journaliers de jan 1990 a mars 2026)
- `monthly_raw` → 435 lignes × 3 colonnes (CFNAI et ISM mensuels)

La fonction `load_data_sheet()` fait le menage : elle saute les 5 premieres lignes de metadata Bloomberg, renomme les colonnes, convertit les types, et trie par date.

**→ On passe a la Section 5 parce qu'on a deux DataFrames a des frequences differentes (journalier vs mensuel) et il faut les unifier avant de pouvoir travailler.**

---

### Section 5 — Aggregation mensuelle (Cell 48-49)

**Le probleme** : Les donnees macro (CFNAI, ISM) n'existent qu'en mensuel. Les prix de marche sont journaliers. On ne peut pas les combiner directement.

**La solution** : `aggregate_daily_to_monthly()` convertit les prix journaliers en mensuels en prenant la **derniere observation de chaque mois** (standard en finance — c'est le prix de cloture de fin de mois qui sert a calculer les rendements mensuels).

En plus, on calcule la **volatilite realisee du S&P 500** = ecart-type des log-rendements journaliers dans le mois. C'est une mesure de risque qu'on utilisera comme variable de controle dans les regressions (une volatilite elevee peut affecter les rendements futurs independamment du petrole).

Ensuite on fait un **inner join** entre les donnees de marche mensualisees et les donnees macro. Inner join = on ne garde que les mois ou on a les deux. Resultat : `monthly_merged` (434 mois × 12 colonnes).

**→ On passe a la Section 6 parce qu'on a les prix mensuels bruts mais les regressions necessitent des rendements et des spreads, pas des niveaux de prix.**

---

### Section 6 — Construction des variables (Cells 50-51)

**Pourquoi transformer les prix en rendements** : Les prix sont non-stationnaires (ils ont une tendance). Les rendements sont (generalement) stationnaires. Toute l'econometrie qui suit (OLS, VAR, Granger) suppose la stationnarite.

`build_project_variables()` cree :

| Variable | Formule | Interpretation |
|---|---|---|
| `wti_return` | `ln(WTI_t / WTI_{t-1})` | Rendement mensuel du petrole WTI |
| `brent_return` | `ln(Brent_t / Brent_{t-1})` | Idem pour le Brent (robustesse) |
| `sp500_return` | `ln(SP500_t / SP500_{t-1})` | Rendement mensuel des actions US |
| `msci_em_return` | `ln(MSCI_EM_t / MSCI_EM_{t-1})` | Rendement actions emergentes (robustesse) |
| `gold_return` | `ln(Gold_t / Gold_{t-1})` | Rendement de l'or (controle valeur refuge) |
| `term_spread` | `US10Y - US2Y` | Pente de la courbe des taux (indicateur du cycle) |
| `hy_change` | `HY_t - HY_{t-1}` | Variation du yield high-yield (risque credit) |

**Pourquoi ces variables** : Elles couvrent les 3 dimensions du projet :
- **Petrole** : WTI (+ Brent pour robustesse) — la variable qu'on decompose
- **Marches** : S&P 500, HY, MSCI EM — les variables qu'on essaie de predire
- **Controles** : term spread, gold, volatilite — des facteurs qui affectent les marches independamment du petrole

Resultat : `project_df` (434 × 19).

**→ On passe a la Section 7 parce qu'avant de modeliser, il faut verifier que les donnees sont "propres" : stationnaires, sans autocorrelation parasite, et comprendre leur distribution.**

---

### Section 7 — Diagnostics statistiques (Cells 52-60)

C'est une etape obligatoire en econometrie. On ne modele jamais sans avoir d'abord explore les donnees.

**Cell 53 — Stats descriptives (Table 1)** :
On calcule les 4 premiers moments (moyenne, ecart-type, skewness, kurtosis) de chaque variable. Ce qu'on cherche :
- La kurtosis du WTI est de ~10 (les queues sont tres epaisses — il y a des chocs extremes). Ca justifie l'utilisation d'erreurs robustes HC1 plus tard.
- Le CFNAI a une kurtosis de ~168 (domination par quelques mois extremes comme la crise COVID). Il faut en etre conscient pour interpreter la decomposition.

**→ Cell 53 vers Cell 54** : Apres avoir vu les proprietes univariees, on regarde les relations bivariees.

**Cell 54 — Correlations (Table 2)** :
La matrice de correlation montre les liens bruts entre variables. Par exemple, si WTI et S&P 500 sont tres correles positivement, l'histoire "demande" est plausible. Si la correlation est faible ou negative, l'histoire "offre" domine.

**→ Cell 54 vers Cell 55** : Les correlations sont des chiffres, les graphiques permettent de voir les patterns temporels.

**Cell 55 — Graphiques temporels (Figures 1-3)** :
On visualise WTI return, S&P 500 return, et HY change sur toute la periode. On repere visuellement :
- Les periodes de crise (2008, COVID)
- Les clusters de volatilite
- Les eventuels breaks structurels

**→ Cell 55 vers Cell 56** : Les graphiques suggerent des series stationnaires, mais il faut le confirmer formellement.

**Cell 56 — Tests ADF (Table 3a)** :
Le test Augmented Dickey-Fuller teste l'hypothese nulle d'une racine unitaire. Si p < 0.05, la serie est stationnaire. C'est un **prerequis** pour toute la suite : si une serie n'est pas stationnaire, les regressions OLS et le VAR donnent des resultats fallacieux (spurious regression).

**→ Cell 56 vers Cell 57** : La stationnarite est confirmee. Maintenant on teste la normalite et l'autocorrelation.

**Cell 57 — Ljung-Box + Jarque-Bera (Table 3b)** :
- **Ljung-Box** : teste si les valeurs passees d'une serie predisent ses valeurs futures (autocorrelation). Si oui, ca signifie qu'on peut potentiellement exploiter cette persistance dans un modele.
- **Jarque-Bera** : teste si les donnees sont normales. Resultat : aucune serie n'est normale (p < 0.05 pour toutes). Ca justifie l'utilisation d'erreurs robustes HC1 dans les regressions.

**→ Cell 57 vers Cells 59-60** : On a detecte de la non-normalite. Un des faits stylises des donnees financieres est le "volatility clustering" (les periodes agitees sont suivies de periodes agitees). On le teste formellement.

**Cells 59-60 — Volatility clustering (Figure 4)** :
On calcule l'ACF des rendements **au carre** (proxy de la volatilite). Si l'ACF est significative aux premiers lags, il y a du clustering. Le test Ljung-Box sur les carres confirme. C'est un fait stylise classique — pas un probleme a corriger, mais un element a garder en tete pour l'interpretation.

**→ On passe a la Section 8 parce que les diagnostics confirment que les donnees sont exploitables : stationnaires, avec des proprietes bien comprises. On peut maintenant decomposer le petrole.**

---

### Section 8 — Decomposition petroliere (Cells 61-71)

**C'est la piece maitresse du projet.** Tout ce qui suit depend de cette decomposition.

**Cell 62 — OLS from scratch (Table 4)** :
On estime la regression :
```
r_wti = alpha + beta * CFNAI + epsilon
```
- **Fitted values** (alpha + beta × CFNAI) = **composante demande** → la partie du rendement petrolier expliquee par l'activite economique
- **Residus** (epsilon) = **composante offre** → tout ce qui n'est pas lie a la demande (chocs d'offre, geopolitique, speculation)

Le R2 est faible (~4%) — le CFNAI n'explique qu'une petite partie du petrole. C'est normal : le marche petrolier est domine par l'offre (OPEP, guerres). Mais meme 4% suffit pour creer une decomposition utile.

**→ Cell 62 vers Cell 63** : On a un modele. Il faut maintenant verifier que ses residus sont "propres".

**Cell 63 — Diagnostics des residus** :
Le Ljung-Box montre de l'autocorrelation significative dans les residus. Ca veut dire que le modele OLS est mal specifie — les erreurs standards sont biaisees. Il faut corriger.

**→ Cell 63 vers Cell 64** : On visualise l'autocorrelation pour comprendre sa structure.

**Cell 64 — ACF des residus (Figure 5)** :
Le barplot ACF montre quels lags sont significatifs. Ca guide le choix de la correction.

**→ Cell 64 vers Cells 66-69** : L'autocorrelation est detectee, on corrige avec un modele MA(1).

**Cells 66-69 — Correction MA(1)** :
On estime le meme modele mais avec des erreurs MA(1) par maximum de vraisemblance. L'idee : si `epsilon_t = innovation_t + theta * innovation_{t-1}`, l'OLS ignore cette structure et biaise les erreurs standards.

**Cell 66** (Table 5) montre la comparaison OLS vs MLE cote a cote.
**Cell 67** : Le beta du CFNAI passe de 0.0184 (OLS) a 0.0154 (MLE) — tres proche. La decomposition est **robuste** a la correction MA(1). C'est rassurant.
**Cell 68** : Les diagnostics des innovations MA(1) montrent moins d'autocorrelation.
**Cell 69** (Figure 6) : Comparaison visuelle des ACF avant/apres correction.

**→ Cells 66-69 vers Cell 70** : La decomposition OLS est validee. On ajoute maintenant l'approche alternative par regimes.

**Cell 70 — Regimes ISM** :
On cree des variables d'interaction : `oil_expansion` (rendement WTI quand ISM > 50) et `oil_contraction` (quand ISM ≤ 50). C'est une approche differente de l'OLS : au lieu d'une relation lineaire continue, on fait une distinction binaire.

**→ Cell 70 vers Cell 71** : On visualise les composantes pour verifier leur coherence economique.

**Cell 71 — Graphiques (Figures 7-8)** :
- Figure 7 : WTI return superpose avec la composante demande → on voit que la demande lisse le signal
- Figure 8 : La composante offre seule → on voit les gros chocs (2008, 2014-15, 2020)

**→ On passe a la Section 9 parce qu'on a maintenant les deux composantes (demande + offre). La question suivante est : est-ce que ces composantes predisent differemment les marches ?**

---

### Section 9 — Regressions predictives (Cells 72-77)

**Cell 73 — Modele decomposition** :
Pour chaque cible (S&P 500, HY spread), on estime :
```
y_{t+1} = alpha + beta_1 * demande_t + beta_2 * offre_t + controles_t + epsilon
```

Le `shift(-1)` est **crucial** : on predit le rendement du mois **suivant** avec les informations du mois **courant**. Sans ce decalage, ce serait juste une correlation contemporaine, pas une prevision.

Les erreurs robustes HC1 corrigent l'heteroscedasticite (la variance change dans le temps — typique en finance).

Apres chaque regression, on fait des diagnostics de residus (`run_diagnostic_residuals`) pour verifier que le modele est bien specifie.

**→ Cell 73 vers Cell 74** : On a teste l'approche decomposition. On teste maintenant l'approche regime pour comparer.

**Cell 74 — Modele regime** :
Meme exercice mais avec `oil_expansion` et `oil_contraction` au lieu de demande/offre. Si les deux approches pointent dans la meme direction, les conclusions sont plus solides.

**→ Cell 74 vers Cells 76-77** : Les coefficients sont estimes sur l'echantillon complet. Mais sont-ils stables dans le temps ?

**Cells 76-77 — Coefficients rolling (Figure 9)** :
On estime la regression sur une fenetre glissante de 60 mois et on trace l'evolution des coefficients. Si le beta de la composante offre change de signe ou disparait a certaines periodes, le resultat n'est pas fiable. Les bandes ±2 erreurs standards montrent l'incertitude.

**→ On passe a la Section 10 parce que les regressions montrent des coefficients, mais on veut tester plus formellement si c'est de la "causalite" au sens statistique (Granger).**

---

### Section 10 — Tests de causalite (Cells 78-81)

**Cell 79 — Granger F-tests (Table 6)** :
On teste 4 paires : {demande, offre} × {S&P 500, HY}. A chaque fois, la question est : est-ce que les **lags** de la composante petrole aident a predire le marche, au-dela de ce que les lags du marche lui-meme predisent deja ?

C'est un test plus formel que la regression de la Section 9 : ici on compare explicitement un modele avec et sans les lags de la variable "cause".

**→ Cell 79 vers Cell 80** : Granger est bivariate et se limite a la precedence temporelle. Geweke est plus riche.

**Cell 80 — Geweke global (Table 7)** :
On change de perspective : au lieu de travailler sur les rendements mensuels, on utilise les **variances rolling journalieres** (fenetre de 60 jours). C'est l'approche de la Classe 6 (p.19-22) appliquee a notre question.

Geweke decompose la dependance totale en :
- **Causalite directionnelle** WTI → S&P et S&P → WTI
- **Dependance instantanee** (correlation contemporaine)
- **Total** = somme des trois

Ca permet de quantifier la **taille** de la causalite (pas juste un oui/non comme Granger) et de voir si c'est bidirectionnel.

**→ Cell 80 vers Cell 81** : La causalite est-elle constante ou change-t-elle dans le temps ?

**Cell 81 — Geweke par sous-periodes (Table 8)** :
On decoupe en blocs de 5 ans (2000-2004, 2005-2009, ...) et on recalcule Geweke sur chaque bloc. Ca revele si la transmission petrole → actions s'est renforcee ou affaiblie au fil du temps.

**→ On passe a la Section 11 parce que les tests de causalite sont bivaries (2 variables a la fois). Le VAR permet d'analyser le systeme complet (6 variables simultanement) et de voir comment un choc se propage.**

---

### Section 11 — VAR et reponses impulsionnelles (Cells 82-86)

**Cell 83 — Selection du lag (Table 9)** :
On compare les criteres d'information (AIC, BIC, HQ, FPE) pour choisir le nombre de retards du VAR. Le BIC favorise la parcimonie (moins de parametres) — c'est le choix par defaut. Si BIC dit 0, on prend AIC.

Le VAR inclut 6 variables : `wti_return`, `sp500_return`, `hy_change`, `term_spread`, `gold_return`, `ism_mfg`. C'est le systeme complet qu'on etudie.

**→ Cell 83 vers Cell 84** : Le lag est choisi, on peut estimer le modele.

**Cell 84 — Estimation + diagnostics (Table 10)** :
On estime le VAR et on verifie deux choses :
1. **Stabilite** : toutes les valeurs propres de la matrice compagnon sont dans le cercle unite. Si ce n'est pas le cas, le VAR est explosif et inutilisable.
2. **Ljung-Box sur les residus** : les residus de chaque equation du VAR ne doivent pas etre autocorreles. Si oui, le lag est insuffisant.

**→ Cell 84 vers Cell 85** : Le VAR est stable et bien specifie. On peut maintenant simuler des chocs.

**Cell 85 — IRF (Figures 10-11)** :
Les Impulse Response Functions repondent a la question : "si le petrole subit un choc de 1 ecart-type aujourd'hui, comment reagissent le S&P 500 et le HY spread sur les 24 mois suivants ?"

On utilise l'orthogonalisation de **Cholesky** (Classe 5, p.51-60) : on decompose la matrice de variance-covariance des residus en Sigma = P × P' et on regarde les chocs orthogonalises. L'ordre des variables dans le VAR compte — WTI est en premier, ce qui lui donne la priorite dans l'identification.

Les bandes de confiance sont calculees par **Monte Carlo** (300 replications) : on resimule le VAR avec des residus bootstrappes et on calcule les IRF a chaque fois pour avoir un intervalle.

**→ Cell 85 vers Cell 86** : Les IRF montrent la dynamique du choc. La FEVD repond a une question complementaire.

**Cell 86 — FEVD (Table 11)** :
La Forecast Error Variance Decomposition repond a : "quelle part de l'incertitude de prevision du S&P 500 a horizon 12 mois est expliquee par les chocs petroliers ?" Si c'est 5%, le petrole est un facteur mineur. Si c'est 30%, c'est un facteur dominant.

**→ On passe a la Section 12 parce que tout ce qui precede est "in-sample" (on utilise toutes les donnees pour estimer et evaluer). Le vrai test est la prevision hors-echantillon.**

---

### Section 12 — Prevision hors-echantillon (Cells 87-90)

**Cell 88 — Comparaison rolling OLS (Table 12)** :
On compare 3 modeles en prevision recursive :
1. **Benchmark** : moyenne historique (tres difficile a battre en finance — c'est le test acide)
2. **Modele brut** : WTI return comme seul predicteur petrolier
3. **Modele decompose** : composantes demande + offre separees

On utilise 60% des donnees pour la premiere estimation, puis on avance mois par mois en reestimant a chaque pas. Le RMSE et le MAE mesurent la qualite de prevision.

Si le modele decompose ne bat pas le benchmark, la decomposition a une valeur explicative (on comprend mieux) mais pas predictive (on ne prevoit pas mieux).

**→ Cell 88 vers Cells 89-90** : On a teste les modeles OLS. On teste maintenant le VAR en prevision.

**Cells 89-90 — Prevision VAR (Table 13, Figures 12-13)** :
On coupe l'echantillon en deux : train (avant 2020) et test (apres 2020). On entraine le VAR sur le train et on prevoit 12 mois. La periode post-2020 inclut le COVID — c'est un vrai test de stress.

Le RMSE du VAR est compare aux realisations. Les graphiques (Figures 12-13) montrent visuellement si le VAR capture la dynamique post-COVID.

**→ On passe a la Section 13 parce que les resultats sont la. La question est : sont-ils robustes ou fragiles ?**

---

### Section 13 — Robustesse (Cells 91-93)

**Cell 92 — Brent + MSCI EM (Table 14)** :
Deux tests :
1. **Brent au lieu de WTI** : Si les resultats disparaissent en changeant le benchmark petrolier, ils sont specifiques au WTI et pas generalises au marche petrolier.
2. **MSCI EM au lieu de S&P 500** : Est-ce que l'effet petrole est specifique aux actions US ou affecte aussi les marches emergents ?

On regarde si les coefficients demande/offre gardent le meme signe et la meme significativite.

**→ Cell 92 vers Cell 93** : Les resultats tiennent-ils sur differentes periodes historiques ?

**Cell 93 — Sous-periodes (Table 15)** :
On decoupe en 3 periodes :
- **1990-2007** : avant la crise, marche petrolier "classique" domine par l'OPEP
- **2008-2014** : crise financiere + revolution du shale americain
- **2015-2026** : post-shale, accord OPEP+, COVID, guerre en Ukraine

Si le coefficient de la composante offre est significatif dans une periode mais pas dans les autres, le resultat n'est pas robuste — il est driven par une periode specifique.

**→ On passe a la Section 14 pour resumer les conclusions.**

---

### Section 14 — Conclusions (Cells 94-95)

`interpret_two_component_model()` resume automatiquement les resultats pour chaque cible :
- **S&P 500** : ni la demande ni l'offre ne sont significatives au seuil 5%
- **HY spread** : la composante offre est significative (p = 0.019, coef = +0.88)

**Message central** : Les chocs d'offre petroliers affectent surtout le marche du **credit** (HY spread), pas directement les **actions** (S&P 500). Quand le petrole monte pour des raisons non liees a la demande, le spread de credit s'elargit le mois suivant — ce qui signifie que le marche percoit un risque accru pour les entreprises les plus fragiles.

---

## Resume des methodes et leur lien avec le cours

| Methode | Section | Classe du cours | Reference dans les slides |
|---|---|---|---|
| Moments (mean, std, skew, kurtosis) | 7 | Classe 2 | p.7-15 |
| Jarque-Bera | 7 | Classe 2 | p.20-22 |
| ACF + Ljung-Box | 7, 8, 9 | Classe 2 | p.30-35 |
| Volatility clustering (ACF des carres) | 7 | Classe 2 | p.36-39 |
| ADF (stationnarite) | 7 | Classe 2 | — |
| OLS from scratch (beta = (X'X)^-1 X'y) | 8 | Classe 3 | p.12-18 |
| Erreurs robustes HC1 | 9 | Classe 3 | — |
| Out-of-sample RMSE / MAE | 12 | Classe 3 | p.38 |
| MA(1) MLE + OPG standard errors | 8 | Classe 4 | — |
| VAR estimation + lag selection (BIC) | 11 | Classe 5 | p.17-18, 26-27 |
| Granger causality (F-test) | 10 | Classe 5 | p.42-45 |
| Geweke causality measures | 10 | Classe 6 | p.14-22 |
| IRF Cholesky orthogonalisees | 11 | Classe 5 | p.51-60 |
| FEVD (variance decomposition) | 11 | Classe 5 | p.68-70 |
| Application petrole → actions | 10, 11 | Classe 6 | p.19-22 (exactement notre sujet) |

---

## Glossaire

| Terme | Definition |
|---|---|
| **WTI** | West Texas Intermediate — prix de reference du petrole americain |
| **Brent** | Prix de reference du petrole europeen/mondial |
| **CFNAI** | Chicago Fed National Activity Index — composite de 85 indicateurs d'activite US |
| **ISM** | Institute for Supply Management Manufacturing Index — au-dessus de 50 = expansion |
| **HY** | High Yield — obligations a haut rendement (junk bonds) |
| **Term spread** | US 10Y - US 2Y — pente de la courbe des taux, indicateur de recession si negatif |
| **Log-rendement** | `ln(P_t / P_{t-1})` — standard en finance, additif dans le temps |
| **ADF** | Augmented Dickey-Fuller — test de racine unitaire (stationnarite) |
| **Ljung-Box** | Test d'autocorrelation jointe sur plusieurs lags |
| **Jarque-Bera** | Test de normalite base sur skewness + kurtosis |
| **HC1** | Heteroskedasticity-Consistent standard errors (White 1980) |
| **MA(1)** | Moving Average d'ordre 1 : epsilon_t = innovation_t + theta × innovation_{t-1} |
| **MLE** | Maximum Likelihood Estimation — estimation par vraisemblance |
| **OPG** | Outer Product of Gradients — methode pour calculer les erreurs standards du MLE |
| **VAR** | Vector AutoRegression — chaque variable est regressee sur les lags de toutes les variables |
| **IRF** | Impulse Response Function — reponse d'une variable a un choc sur une autre |
| **FEVD** | Forecast Error Variance Decomposition — part de l'incertitude expliquee par chaque choc |
| **Cholesky** | Decomposition matricielle Sigma = P × P' pour orthogonaliser les chocs du VAR |
| **Granger causality** | X "Granger-cause" Y si les lags de X aident a predire Y |
| **Geweke (1982)** | Decomposition de la dependance en directionnelle + instantanee + totale |
| **RMSE** | Root Mean Squared Error — metrique de prevision, penalise les grosses erreurs |
| **MAE** | Mean Absolute Error — metrique de prevision, plus robuste aux outliers |
| **In-sample** | Evaluation sur les memes donnees qui ont servi a estimer le modele |
| **Out-of-sample** | Evaluation sur des donnees que le modele n'a jamais vues |
