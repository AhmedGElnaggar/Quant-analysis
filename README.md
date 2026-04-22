# 📊 AE Quantitative Analysis Tool

A Bloomberg Terminal-inspired desktop application for analyzing financial markets, built with Python and Tkinter.

![Python](https://img.shields.io/badge/Python-3.8-blue?style=flat-square&logo=python) ![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange?style=flat-square) ![Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=flat-square)

---

## Features

- **Live Stock Charts** — real-time price data via YFinance with MA20/MA50 overlays, volume toggle, and hover price tooltip
- **ML Price Prediction** — choose between Linear Regression and Random Forest to forecast future prices with adjustable forecast window
- **Backtesting** — test trading strategies on historical data with Sharpe ratio, CAGR, total return, and max drawdown metrics
- **Portfolio Tracker** — add stocks with share counts, track live portfolio value and daily % change, persists between sessions
- **Bell Notifications** — alerts when a portfolio stock moves ±1% or more
- **Indicator Preferences** — MA20, MA50, and volume checkbox states saved between sessions

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI | Python 3.8, Tkinter, ttk |
| Data | YFinance, Pandas, NumPy |
| Charts | Matplotlib (TkAgg backend) |
| ML | Scikit-learn (LinearRegression, RandomForestRegressor) |
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
# Windows — double click run.bat
# Or from terminal:
python quant_app.py
```

---

## Concepts Explained

### Indicators

**MA20 (20-Day Moving Average)**
The average closing price over the last 20 days. Smooths out short-term noise to show the recent trend. When the price is above MA20, momentum is bullish.

**MA50 (50-Day Moving Average)**
Same idea but over 50 days — shows the longer-term trend. Slower to react to price changes than MA20.

---

### ML Models

**Linear Regression**
Uses the last 20 days of prices as input and finds the best straight-line relationship to predict the next price. Simple, fast, good baseline.

**Random Forest**
Builds 100 decision trees, each looking at the data slightly differently, then averages their predictions. Much better at capturing non-linear patterns than Linear Regression. Generally more accurate on volatile stocks.

Both models are trained on 80% of historical data and tested on the remaining 20%. MAE (Mean Absolute Error) and estimated accuracy are shown after each run.

---

### Backtest Strategies

**Buy & Hold**
The simplest strategy — buy the stock once and never sell regardless of price movements. Often hard to beat with more complex strategies on strong stocks like AAPL.

**MA Crossover**
Uses MA20 and MA50 to generate buy/sell signals:
- MA20 crosses **above** MA50 → Buy (short-term momentum building)
- MA20 crosses **below** MA50 → Sell (momentum fading)

Tries to catch trends early but can be slow to react and miss gains.

**RSI Mean Reversion**
RSI (Relative Strength Index) is a 0–100 indicator measuring if a stock is overbought or oversold:
- RSI below 30 → Oversold → likely to bounce back → **Buy**
- RSI above 70 → Overbought → likely to pull back → **Sell**

Based on the idea that prices always revert to their average over time.

### Backtest Metrics

| Metric | What it means |
|--------|--------------|
| Total Return | Overall % gain or loss over the period |
| CAGR | Annualized return rate — what % per year the strategy returned |
| Sharpe Ratio | Return relative to risk — higher is better, above 1.0 is considered good |
| Max Drawdown | Worst peak-to-trough loss — how far the portfolio dropped at its lowest point |

---

## Project Structure

```
quant-analysis/
├── quant_app.py       # Main application
├── run.bat            # Double-click to launch on Windows
├── portfolio.json     # Auto-generated portfolio data
├── prefs.json         # Auto-generated indicator preferences
└── README.md
```

---

## Author

**Ahmed Elnaggar** — [GitHub](https://github.com/AhmedGElnaggar)
