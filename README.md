# 📊 AE Quantitative Analysis Tool

A Bloomberg Terminal-inspired desktop application for analyzing financial markets, built with Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.8-blue?style=flat-square&logo=python) ![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange?style=flat-square) ![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=flat-square)

---

## Status

🚧 **In active development** — core scaffold complete, features being added incrementally.

### Done
- [x] Project structure and GitHub setup
- [x] Dark theme constants (Bloomberg-inspired)
- [x] Portfolio persistence (JSON load/save)

### In Progress
- [ ] Main Tkinter window and layout
- [ ] Stock price chart with MA indicators
- [ ] ML price prediction (Linear Regression)
- [ ] Backtesting engine (MA Crossover, RSI, Buy & Hold)
- [ ] Portfolio tracker with live prices

---

## Planned Features

- **Live Stock Charts** — real-time price data via YFinance with MA20/MA50 overlays and volume
- **ML Price Prediction** — Linear Regression forecasting with adjustable forecast window
- **Backtesting** — test MA Crossover, RSI Mean Reversion, and Buy & Hold strategies with Sharpe ratio, CAGR, and max drawdown metrics
- **Portfolio Tracker** — add stocks with share counts, track live portfolio value, persists between sessions

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI | Python 3.8, Tkinter, ttk |
| Data | YFinance, Pandas, NumPy |
| Charts | Matplotlib (TkAgg backend) |
| ML | Scikit-learn (LinearRegression, MinMaxScaler) |
| Persistence | JSON |

---

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
git clone https://github.com/AhmedGElnaggar/Quant-analysis.git
cd Quant-analysis

pip install yfinance scikit-learn matplotlib pandas numpy
```

### Run

```bash
python quant_app.py
```

---

## Project Structure

```
quant-analysis/
├── quant_app.py       # Main application
├── portfolio.json     # Auto-generated portfolio data
└── README.md
```

---

## Author

**Ahmed Elnaggar** — [GitHub](https://github.com/AhmedGElnaggar)
