> This file mirrors `.github/copilot-instructions.md`; keep both in sync when either changes.

# CLAUDE.md — JPM Volatility Modeling with GARCH and VaR

## Purpose
GARCH-based volatility modeling and Value at Risk backtesting on JPMorgan equity returns

## Tech stack
- Python; dependencies in `requirements.txt`
- Key libraries: `numpy`, `pandas`, `matplotlib`, `yfinance`, `arch`

## Folder structure
- `images/` (3 files)
- `README.md`
- `garch_var_model.py`
- `requirements.txt`

## Setup, run, test
Commands documented in README.md (referenced files exist):
```bash
pip install -r requirements.txt
python garch_var_model.py
```
- No automated tests exist yet; if adding them, use pytest under `tests/`.

## Conventions observed
- Public data sources referenced: yfinance.
- Write paths relative to the repo root (no absolute local paths).

## Output artifacts
- Charts are generated with matplotlib.

## Guardrails
- Never commit secrets, API keys, tokens, or `.env` files.
- Do not commit large raw datasets or binaries; keep data fetched or documented with its source.
- Keep analysis source-backed: cite data sources and assumptions; label scenario/forecast outputs as model estimates, not facts.
- Preserve reproducibility: no unseeded randomness, no hidden manual steps.
