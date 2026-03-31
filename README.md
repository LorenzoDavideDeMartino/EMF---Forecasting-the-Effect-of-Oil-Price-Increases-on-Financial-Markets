# EMF - Forecasting the Effect of Oil Price Increases on Financial Markets

This repository contains our Empirical Methods in Finance group project on whether oil price increases affect financial markets differently depending on the macroeconomic environment behind the oil move.

## Research question

Do oil price increases have the same effect on financial markets when they are associated with stronger demand conditions as when they come from residual non-demand-related movements? Can this distinction improve the prediction of equity returns and credit spreads?

## Project structure

```text
.
|-- data/
|   |-- raw/
|   |   `-- data_hec_projet_1.xlsx
|   `-- processed/
|-- notebooks/
|   `-- emif_oil_market_project.ipynb
|-- outputs/
|   |-- figures/
|   `-- tables/
|-- src/
|   `-- project_main.py
|-- .gitignore
`-- README.md
```

## Folder description

- `data/raw/`: original input data used in the project.
- `data/processed/`: cleaned or transformed datasets produced during the analysis.
- `notebooks/`: the main notebook used for the empirical analysis and interpretation.
- `outputs/figures/`: exported charts if we decide to save them outside the notebook.
- `outputs/tables/`: exported tables and regression outputs.
- `src/`: helper functions used by the notebook.

## Main files

- `notebooks/emif_oil_market_project.ipynb`: main project notebook.
- `src/project_main.py`: helper functions for loading data, cleaning, variable construction, regressions, Granger tests, VAR analysis, and forecasting.

## Notes

- The notebook is designed to stay readable and presentation-friendly.
- The core analysis is monthly.
- The decomposition of oil movements is reduced-form and is not presented as full structural identification.
