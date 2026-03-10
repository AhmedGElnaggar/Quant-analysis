import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error
import threading
import json
import os

# ─── THEME ───────────────────────────────────────────────────────────────────
BG       = "#0d0f14"
SURFACE  = "#151820"
SURFACE2 = "#1c2030"
BORDER   = "#252a38"
TEXT     = "#e8edf5"
MUTED    = "#4a5570"
ACCENT   = "#00d4ff"
GREEN    = "#00e676"
RED      = "#ff4444"
AMBER    = "#ffaa00"
FONT     = ("Courier New", 10)
FONT_SM  = ("Courier New", 8)
FONT_LG  = ("Courier New", 13, "bold")
FONT_XL  = ("Courier New", 18, "bold")

matplotlib.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "axes.edgecolor": BORDER,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "text.color": TEXT,
    "grid.color": BORDER,
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.5,
    "font.family": "monospace",
    "font.size": 8,
})

PORTFOLIO_FILE = "portfolio.json"
PREFS_FILE = "prefs.json"

def load_prefs():
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE) as f:
            return json.load(f)
    return {"show_volume": False, "show_ma20": True, "show_ma50": True}

def save_prefs(p):
    with open(PREFS_FILE, "w") as f:
        json.dump(p, f)

# ─── PORTFOLIO PERSISTENCE ───────────────────────────────────────────────────
def load_portfolio():
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            return json.load(f)
    return {}

def save_portfolio(p):
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(p, f)

# ─── MAIN APP ─────────────────────────────────────────────────────────────────
class QuantApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AE Quantitative Analysis")
        self.geometry("1400x820")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.portfolio = load_portfolio()
        self.prefs = load_prefs()
        self.portfolio_prev_prices = {}
        self.notifications = []
        self.current_ticker = tk.StringVar(value="AAPL")
        self.current_period = tk.StringVar(value="6mo")
        self.current_data = None
        self.current_company_name = ""
        self._build_ui()
        self.after(100, lambda: self.load_ticker())
        if self.portfolio:
            self.after(500, lambda: threading.Thread(target=self._update_portfolio_prices, daemon=True).start())

    def _build_ui(self):
        # ── TOP BAR
        topbar = tk.Frame(self, bg=SURFACE, height=52)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="▣ AE QUANT", font=FONT_LG, bg=SURFACE,
                 fg=ACCENT).pack(side="left", padx=16)

        # Ticker search
        search_frame = tk.Frame(topbar, bg=SURFACE2, bd=0)
        search_frame.pack(side="left", padx=8, pady=10)
        tk.Label(search_frame, text="TICKER", font=FONT_SM, bg=SURFACE2,
                 fg=MUTED).pack(side="left", padx=(8,2))
        self.ticker_entry = tk.Entry(search_frame, textvariable=self.current_ticker,
                                     font=("Courier New", 11, "bold"), bg=SURFACE2,
                                     fg=ACCENT, insertbackground=ACCENT,
                                     relief="flat", width=8)
        self.ticker_entry.pack(side="left", padx=4)
        self.ticker_entry.bind("<Return>", lambda e: self.load_ticker())

        tk.Button(search_frame, text="LOAD", font=FONT_SM, bg=ACCENT,
                  fg=BG, relief="flat", padx=8, cursor="hand2",
                  command=self.load_ticker).pack(side="left", padx=4, pady=4)

        # Period buttons
        period_frame = tk.Frame(topbar, bg=SURFACE)
        period_frame.pack(side="left", padx=16)
        for p in ["1mo", "3mo", "6mo", "1y", "2y", "5y"]:
            btn = tk.Button(period_frame, text=p.upper(), font=FONT_SM,
                            bg=SURFACE2, fg=TEXT, relief="flat", padx=8, pady=4,
                            cursor="hand2",
                            command=lambda x=p: self._set_period(x))
            btn.pack(side="left", padx=2)

        # Bell notification button
        self.bell_count_var = tk.StringVar(value="")
        bell_frame = tk.Frame(topbar, bg=SURFACE)
        bell_frame.pack(side="right", padx=4)
        self.bell_btn = tk.Button(bell_frame, text="🔔", font=("Courier New", 13),
                                   bg=SURFACE, fg=MUTED, relief="flat",
                                   cursor="hand2", command=self._show_notifications)
        self.bell_btn.pack(side="left")
        self.bell_badge = tk.Label(bell_frame, textvariable=self.bell_count_var,
                                    font=FONT_SM, bg=RED, fg=TEXT,
                                    width=2, relief="flat")
        self.bell_badge.pack(side="left")
        self.bell_badge.pack_forget()  # hidden until there are notifications

        # Live price display
        self.price_var = tk.StringVar(value="---")
        self.change_var = tk.StringVar(value="")
        price_frame = tk.Frame(topbar, bg=SURFACE)
        price_frame.pack(side="right", padx=16)
        tk.Label(price_frame, textvariable=self.price_var, font=FONT_XL,
                 bg=SURFACE, fg=GREEN).pack(side="left")
        tk.Label(price_frame, textvariable=self.change_var, font=FONT,
                 bg=SURFACE, fg=GREEN).pack(side="left", padx=8)

        # ── MAIN LAYOUT
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True)

        # Left sidebar - portfolio
        self._build_sidebar(main)

        # Right content - tabs
        content = tk.Frame(main, bg=BG)
        content.pack(side="left", fill="both", expand=True)

        # Tabs
        tab_bar = tk.Frame(content, bg=SURFACE, height=36)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        self.tab_frames = {}
        self.tab_buttons = {}
        self.active_tab = tk.StringVar(value="chart")

        tab_container = tk.Frame(content, bg=BG)
        tab_container.pack(fill="both", expand=True)

        tabs = [("chart", "📈 Chart"), ("ml", "🤖 ML Predict"), ("backtest", "⚙ Backtest")]
        for key, label in tabs:
            frame = tk.Frame(tab_container, bg=BG)
            self.tab_frames[key] = frame
            btn = tk.Button(tab_bar, text=label, font=FONT_SM,
                            bg=SURFACE, fg=MUTED, relief="flat",
                            padx=16, pady=8, cursor="hand2",
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left")
            self.tab_buttons[key] = btn

        self._build_chart_tab(self.tab_frames["chart"])
        self._build_ml_tab(self.tab_frames["ml"])
        self._build_backtest_tab(self.tab_frames["backtest"])
        self._switch_tab("chart")

        # Status bar
        self.status_var = tk.StringVar(value="Ready — enter a ticker and press LOAD")
        tk.Label(self, textvariable=self.status_var, font=FONT_SM,
                 bg=SURFACE, fg=MUTED, anchor="w").pack(fill="x", side="bottom", padx=8)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=SURFACE, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="PORTFOLIO", font=FONT_SM, bg=SURFACE,
                 fg=MUTED).pack(anchor="w", padx=12, pady=(12,4))

        # Add stock
        add_frame = tk.Frame(sidebar, bg=SURFACE2)
        add_frame.pack(fill="x", padx=8, pady=4)
        self.port_ticker = tk.Entry(add_frame, font=FONT_SM, bg=SURFACE2,
                                    fg=ACCENT, insertbackground=ACCENT,
                                    relief="flat", width=6)
        self.port_ticker.pack(side="left", padx=6, pady=6)
        self.port_ticker.insert(0, "AAPL")
        self.port_shares = tk.Entry(add_frame, font=FONT_SM, bg=SURFACE2,
                                    fg=TEXT, insertbackground=TEXT,
                                    relief="flat", width=5)
        self.port_shares.pack(side="left", padx=2)
        self.port_shares.insert(0, "10")
        tk.Button(add_frame, text="+", font=FONT_SM, bg=GREEN, fg=BG,
                  relief="flat", padx=6, cursor="hand2",
                  command=self.add_to_portfolio).pack(side="left", padx=4, pady=4)

        # Portfolio list frame
        self.port_frame = tk.Frame(sidebar, bg=SURFACE)
        self.port_frame.pack(fill="both", expand=True, padx=8)

        # Total value
        self.total_var = tk.StringVar(value="Total: $0.00")
        tk.Label(sidebar, textvariable=self.total_var, font=FONT_SM,
                 bg=SURFACE, fg=GREEN).pack(anchor="w", padx=12, pady=4)

        self._refresh_portfolio_ui()

    def _build_chart_tab(self, parent):
        self.chart_fig = Figure(figsize=(10, 5), facecolor=SURFACE)
        self.chart_canvas = FigureCanvasTkAgg(self.chart_fig, parent)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

        # Hover tooltip
        self._hover_annotation = None
        self._hover_vline = None
        self.chart_canvas.mpl_connect("motion_notify_event", self._on_chart_hover)
        self.chart_canvas.mpl_connect("axes_leave_event", self._on_chart_leave)

        # Indicators bar
        ind_bar = tk.Frame(parent, bg=SURFACE2)
        ind_bar.pack(fill="x", padx=8, pady=(0,8))
        tk.Label(ind_bar, text="INDICATORS:", font=FONT_SM, bg=SURFACE2, fg=MUTED).pack(side="left", padx=8)
        self.show_ma20 = tk.BooleanVar(value=self.prefs.get("show_ma20", True))
        self.show_ma50 = tk.BooleanVar(value=self.prefs.get("show_ma50", True))
        self.show_volume = tk.BooleanVar(value=self.prefs.get("show_volume", False))
        for label, var in [("MA20", self.show_ma20), ("MA50", self.show_ma50), ("Volume", self.show_volume)]:
            tk.Checkbutton(ind_bar, text=label, variable=var, font=FONT_SM,
                           bg=SURFACE2, fg=TEXT, selectcolor=SURFACE2,
                           activebackground=SURFACE2, activeforeground=ACCENT,
                           command=self._redraw_chart).pack(side="left", padx=6)

    def _on_chart_hover(self, event):
        if event.inaxes is None or self.current_data is None:
            return
        data = self.current_data
        close = data["Close"].squeeze()
        dates = data.index
        # Find nearest date index
        if not hasattr(event, 'xdata') or event.xdata is None:
            return
        try:
            import matplotlib.dates as mdates
            hover_date = mdates.num2date(event.xdata).replace(tzinfo=None)
            idx = (pd.to_datetime(dates).tz_localize(None) - hover_date).abs().argmin()
            price = float(close.iloc[idx])
            date_str = pd.to_datetime(dates[idx]).strftime("%b %d, %Y")
            ax = self.chart_fig.axes[0]
            # Remove old annotation
            if self._hover_annotation:
                self._hover_annotation.remove()
            if self._hover_vline:
                self._hover_vline.remove()
            # Draw vertical line
            self._hover_vline = ax.axvline(x=dates[idx], color=MUTED, linewidth=0.8, linestyle=":")
            # Draw annotation box
            self._hover_annotation = ax.annotate(
                f"  {date_str}\n  ${price:,.2f}  ",
                xy=(dates[idx], price),
                xytext=(12, 12), textcoords="offset points",
                fontsize=8, color=TEXT,
                bbox=dict(boxstyle="round,pad=0.4", facecolor=SURFACE2, edgecolor=ACCENT, linewidth=1),
                fontfamily="monospace"
            )
            self.chart_canvas.draw_idle()
        except Exception:
            pass

    def _on_chart_leave(self, event):
        if self._hover_annotation:
            self._hover_annotation.remove()
            self._hover_annotation = None
        if self._hover_vline:
            self._hover_vline.remove()
            self._hover_vline = None
        self.chart_canvas.draw_idle()

    def _build_ml_tab(self, parent):
        ctrl = tk.Frame(parent, bg=SURFACE2)
        ctrl.pack(fill="x", padx=8, pady=8)
        tk.Label(ctrl, text="FORECAST DAYS:", font=FONT_SM, bg=SURFACE2, fg=MUTED).pack(side="left", padx=8)
        self.forecast_days = tk.IntVar(value=30)
        tk.Spinbox(ctrl, from_=7, to=90, textvariable=self.forecast_days,
                   font=FONT_SM, bg=SURFACE2, fg=ACCENT, width=5,
                   relief="flat", buttonbackground=SURFACE2).pack(side="left", padx=4)
        tk.Button(ctrl, text="RUN PREDICTION", font=FONT_SM, bg=ACCENT,
                  fg=BG, relief="flat", padx=12, cursor="hand2",
                  command=lambda: threading.Thread(target=self.run_ml, daemon=True).start()
                  ).pack(side="left", padx=8)
        self.ml_accuracy_var = tk.StringVar(value="")
        tk.Label(ctrl, textvariable=self.ml_accuracy_var, font=FONT_SM,
                 bg=SURFACE2, fg=GREEN).pack(side="left", padx=8)

        self.ml_fig = Figure(figsize=(10, 5), facecolor=SURFACE)
        self.ml_canvas = FigureCanvasTkAgg(self.ml_fig, parent)
        self.ml_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0,8))

    def _build_backtest_tab(self, parent):
        ctrl = tk.Frame(parent, bg=SURFACE2)
        ctrl.pack(fill="x", padx=8, pady=8)

        tk.Label(ctrl, text="STRATEGY:", font=FONT_SM, bg=SURFACE2, fg=MUTED).pack(side="left", padx=8)
        self.strategy_var = tk.StringVar(value="MA Crossover")
        strat_menu = ttk.Combobox(ctrl, textvariable=self.strategy_var,
                                   values=["MA Crossover", "RSI Mean Reversion", "Buy & Hold"],
                                   font=FONT_SM, width=18, state="readonly")
        strat_menu.pack(side="left", padx=4)

        tk.Label(ctrl, text="CAPITAL $:", font=FONT_SM, bg=SURFACE2, fg=MUTED).pack(side="left", padx=8)
        self.capital_var = tk.StringVar(value="10000")
        tk.Entry(ctrl, textvariable=self.capital_var, font=FONT_SM,
                 bg=SURFACE2, fg=ACCENT, relief="flat", width=8).pack(side="left", padx=4)

        tk.Button(ctrl, text="RUN BACKTEST", font=FONT_SM, bg=AMBER,
                  fg=BG, relief="flat", padx=12, cursor="hand2",
                  command=lambda: threading.Thread(target=self.run_backtest, daemon=True).start()
                  ).pack(side="left", padx=8)

        # Results
        res_frame = tk.Frame(parent, bg=BG)
        res_frame.pack(fill="x", padx=8, pady=(0,4))
        self.bt_results = {}
        for key, label in [("return", "Total Return"), ("cagr", "CAGR"), ("sharpe", "Sharpe Ratio"), ("maxdd", "Max Drawdown")]:
            f = tk.Frame(res_frame, bg=SURFACE2)
            f.pack(side="left", padx=4, pady=4, ipadx=12, ipady=6)
            var = tk.StringVar(value="---")
            self.bt_results[key] = var
            tk.Label(f, text=label.upper(), font=FONT_SM, bg=SURFACE2, fg=MUTED).pack()
            tk.Label(f, textvariable=var, font=("Courier New", 12, "bold"), bg=SURFACE2, fg=AMBER).pack()

        self.bt_fig = Figure(figsize=(10, 4), facecolor=SURFACE)
        self.bt_canvas = FigureCanvasTkAgg(self.bt_fig, parent)
        self.bt_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0,8))

    def _switch_tab(self, key):
        for k, f in self.tab_frames.items():
            f.pack_forget()
        self.tab_frames[key].pack(fill="both", expand=True)
        for k, b in self.tab_buttons.items():
            b.config(bg=SURFACE if k != key else SURFACE2, fg=MUTED if k != key else ACCENT)
        self.active_tab.set(key)

    def _set_period(self, p):
        self.current_period.set(p)
        self.load_ticker()

    def load_ticker(self):
        ticker = self.current_ticker.get().strip().upper()
        if not ticker:
            return
        self.status_var.set(f"Loading {ticker}...")
        threading.Thread(target=self._fetch_data, args=(ticker,), daemon=True).start()

    def _fetch_data(self, ticker):
        try:
            data = yf.download(ticker, period=self.current_period.get(), progress=False, auto_adjust=True)
            if data.empty:
                self.after(0, lambda: self.status_var.set(f"No data for {ticker}"))
                return
            self.current_data = data
            info = yf.Ticker(ticker).fast_info
            price = round(float(info.last_price), 2)
            prev = round(float(info.previous_close), 2)
            chg = round(price - prev, 2)
            pct = round((chg / prev) * 100, 2)
            color = GREEN if chg >= 0 else RED
            arrow = "▲" if chg >= 0 else "▼"
            # Get company name
            try:
                company_name = yf.Ticker(ticker).info.get("shortName", ticker)
            except:
                company_name = ticker
            self.current_company_name = company_name
            self.after(0, lambda: self.price_var.set(f"${price:,.2f}"))
            self.after(0, lambda: self.change_var.set(f"{arrow} {chg:+.2f} ({pct:+.2f}%)"))
            self.after(0, lambda: self._update_price_color(color))
            self.after(0, self._redraw_chart)
            self.after(0, lambda: self.status_var.set(f"{ticker} loaded — {len(data)} trading days"))
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {e}"))

    def _update_price_color(self, color):
        for w in self.winfo_children()[0].winfo_children():
            if isinstance(w, tk.Label) and w.cget("textvariable") in [str(self.price_var), str(self.change_var)]:
                w.config(fg=color)

    def _redraw_chart(self):
        save_prefs({"show_ma20": self.show_ma20.get(), "show_ma50": self.show_ma50.get(), "show_volume": self.show_volume.get()})
        if self.current_data is None:
            return
        data = self.current_data.copy()
        self.chart_fig.clear()

        if self.show_volume.get():
            ax1 = self.chart_fig.add_subplot(211)
            ax2 = self.chart_fig.add_subplot(212, sharex=ax1)
        else:
            ax1 = self.chart_fig.add_subplot(111)
            ax2 = None

        close = data["Close"].squeeze()
        dates = data.index

        # Candlestick-style color
        color = GREEN if float(close.iloc[-1]) >= float(close.iloc[0]) else RED
        ax1.plot(dates, close, color=color, linewidth=1.5, label="Price")
        ax1.fill_between(dates, close, float(close.min()), alpha=0.08, color=color)

        if self.show_ma20.get() and len(close) >= 20:
            ma20 = close.rolling(20).mean()
            ax1.plot(dates, ma20, color=ACCENT, linewidth=1, linestyle="--", label="MA20", alpha=0.8)

        if self.show_ma50.get() and len(close) >= 50:
            ma50 = close.rolling(50).mean()
            ax1.plot(dates, ma50, color=AMBER, linewidth=1, linestyle="--", label="MA50", alpha=0.8)

        ax1.set_ylabel("Price (USD)")
        ax1.legend(loc="upper left", fontsize=7)
        ax1.grid(True, alpha=0.3)
        ticker = self.current_ticker.get().upper()
        name = self.current_company_name if self.current_company_name else ticker
        ax1.set_title(f"{name} — {self.current_period.get().upper()}", color=TEXT, fontsize=10)

        if ax2 is not None and "Volume" in data.columns:
            vol = data["Volume"].squeeze()
            vol_colors = [GREEN if float(close.iloc[i]) >= float(close.iloc[i-1]) else RED
                          for i in range(len(close))]
            ax2.bar(dates, vol, color=vol_colors, alpha=0.6, width=0.8)
            ax2.set_ylabel("Volume")
            ax2.grid(True, alpha=0.2)

        self.chart_fig.tight_layout()
        self.chart_canvas.draw()

    def run_ml(self):
        if self.current_data is None:
            self.after(0, lambda: messagebox.showwarning("No Data", "Load a ticker first"))
            return
        self.after(0, lambda: self.status_var.set("Running ML prediction..."))
        try:
            data = self.current_data.copy()
            close = data["Close"].squeeze().values.reshape(-1, 1)
            scaler = MinMaxScaler()
            scaled = scaler.fit_transform(close)

            # Features: use lag windows
            window = 20
            X, y = [], []
            for i in range(window, len(scaled)):
                X.append(scaled[i-window:i].flatten())
                y.append(scaled[i][0])
            X, y = np.array(X), np.array(y)

            split = int(len(X) * 0.8)
            X_train, X_test = X[:split], X[split:]
            y_train, y_test = y[:split], y[split:]

            model = LinearRegression()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            mae = mean_absolute_error(y_test, y_pred)
            actual_prices = scaler.inverse_transform(y_test.reshape(-1,1)).flatten()
            pred_prices = scaler.inverse_transform(y_pred.reshape(-1,1)).flatten()
            mae_price = mean_absolute_error(actual_prices, pred_prices)

            # Future forecast
            days = self.forecast_days.get()
            last_window = scaled[-window:].flatten()
            future = []
            for _ in range(days):
                pred = model.predict([last_window])[0]
                future.append(pred)
                last_window = np.append(last_window[1:], pred)
            future_prices = scaler.inverse_transform(np.array(future).reshape(-1,1)).flatten()
            last_date = data.index[-1]
            future_dates = pd.date_range(last_date, periods=days+1, freq="B")[1:]

            accuracy = max(0, round((1 - mae_price / actual_prices.mean()) * 100, 1))
            self.after(0, lambda: self.ml_accuracy_var.set(f"MAE: ${mae_price:.2f} | Est. Accuracy: {accuracy}%"))

            self.after(0, lambda: self._draw_ml(data, actual_prices, pred_prices, future_prices, future_dates, split, window))
            self.after(0, lambda: self.status_var.set(f"ML prediction complete — {days} day forecast generated"))
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"ML error: {e}"))

    def _draw_ml(self, data, actual, pred, future, future_dates, split, window):
        self.ml_fig.clear()
        ax = self.ml_fig.add_subplot(111)
        close = data["Close"].squeeze()
        dates = data.index

        ax.plot(dates, close, color=MUTED, linewidth=1, label="Historical", alpha=0.6)
        test_dates = dates[split + window:]
        ax.plot(test_dates, actual, color=GREEN, linewidth=1.5, label="Actual")
        ax.plot(test_dates, pred, color=ACCENT, linewidth=1.5, linestyle="--", label="Predicted")
        ax.plot(future_dates, future, color=AMBER, linewidth=2, linestyle="--", label=f"{len(future)}-day Forecast")
        ax.fill_between(future_dates, future * 0.97, future * 1.03, alpha=0.1, color=AMBER)
        ax.axvline(x=dates[-1], color=MUTED, linewidth=0.8, linestyle=":")
        ax.set_title(f"ML Price Prediction — {self.current_ticker.get().upper()}", color=TEXT)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        self.ml_fig.tight_layout()
        self.ml_canvas.draw()

    def run_backtest(self):
        if self.current_data is None:
            self.after(0, lambda: messagebox.showwarning("No Data", "Load a ticker first"))
            return
        self.after(0, lambda: self.status_var.set("Running backtest..."))
        try:
            data = self.current_data.copy()
            close = data["Close"].squeeze()
            capital = float(self.capital_var.get())
            strategy = self.strategy_var.get()

            if strategy == "MA Crossover":
                signals = self._strategy_ma_crossover(close)
            elif strategy == "RSI Mean Reversion":
                signals = self._strategy_rsi(close)
            else:
                signals = pd.Series(1, index=close.index)

            # Simulate portfolio value
            returns = close.pct_change().fillna(0)
            strat_returns = returns * signals.shift(1).fillna(0)
            portfolio = (1 + strat_returns).cumprod() * capital
            bh_portfolio = (1 + returns).cumprod() * capital

            total_return = round((portfolio.iloc[-1] / capital - 1) * 100, 2)
            years = len(close) / 252
            cagr = round((((portfolio.iloc[-1] / capital) ** (1/years)) - 1) * 100, 2)
            sharpe = round(strat_returns.mean() / strat_returns.std() * np.sqrt(252), 2) if strat_returns.std() > 0 else 0
            roll_max = portfolio.cummax()
            drawdown = (portfolio - roll_max) / roll_max
            max_dd = round(drawdown.min() * 100, 2)

            color_ret = GREEN if total_return > 0 else RED
            self.after(0, lambda: self.bt_results["return"].set(f"{total_return:+.2f}%"))
            self.after(0, lambda: self.bt_results["cagr"].set(f"{cagr:+.2f}%"))
            self.after(0, lambda: self.bt_results["sharpe"].set(f"{sharpe:.2f}"))
            self.after(0, lambda: self.bt_results["maxdd"].set(f"{max_dd:.2f}%"))
            self.after(0, lambda: self._draw_backtest(portfolio, bh_portfolio, drawdown, data.index))
            self.after(0, lambda: self.status_var.set(f"Backtest complete — {strategy} | Return: {total_return:+.2f}%"))
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Backtest error: {e}"))

    def _strategy_ma_crossover(self, close):
        ma_fast = close.rolling(20).mean()
        ma_slow = close.rolling(50).mean()
        signal = pd.Series(0, index=close.index)
        signal[ma_fast > ma_slow] = 1
        return signal

    def _strategy_rsi(self, close, period=14):
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        signal = pd.Series(0, index=close.index)
        signal[rsi < 30] = 1
        signal[rsi > 70] = -1
        return signal.replace(0, method="ffill").fillna(0)

    def _draw_backtest(self, portfolio, bh, drawdown, dates):
        self.bt_fig.clear()
        ax1 = self.bt_fig.add_subplot(211)
        ax2 = self.bt_fig.add_subplot(212, sharex=ax1)

        ax1.plot(dates, portfolio, color=GREEN, linewidth=1.5, label=f"{self.strategy_var.get()}")
        ax1.plot(dates, bh, color=MUTED, linewidth=1, linestyle="--", label="Buy & Hold", alpha=0.7)
        ax1.set_ylabel("Portfolio Value ($)")
        ax1.legend(fontsize=7)
        ax1.grid(True, alpha=0.3)
        ax1.set_title(f"Backtest: {self.strategy_var.get()} — {self.current_ticker.get().upper()}", color=TEXT)

        ax2.fill_between(dates, drawdown * 100, 0, color=RED, alpha=0.4)
        ax2.plot(dates, drawdown * 100, color=RED, linewidth=0.8)
        ax2.set_ylabel("Drawdown (%)")
        ax2.grid(True, alpha=0.2)

        self.bt_fig.tight_layout()
        self.bt_canvas.draw()

    def add_to_portfolio(self):
        ticker = self.port_ticker.get().strip().upper()
        try:
            shares = float(self.port_shares.get())
        except:
            return
        if not ticker:
            return
        self.portfolio[ticker] = self.portfolio.get(ticker, 0) + shares
        save_portfolio(self.portfolio)
        self._refresh_portfolio_ui()
        threading.Thread(target=self._update_portfolio_prices, daemon=True).start()

    def _refresh_portfolio_ui(self):
        for w in self.port_frame.winfo_children():
            w.destroy()
        for ticker, shares in self.portfolio.items():
            row = tk.Frame(self.port_frame, bg=SURFACE2, cursor="hand2")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=ticker, font=("Courier New", 9, "bold"),
                     bg=SURFACE2, fg=ACCENT, width=6, anchor="w").pack(side="left", padx=6, pady=4)
            tk.Label(row, text=f"{shares:.0f} sh", font=FONT_SM,
                     bg=SURFACE2, fg=MUTED).pack(side="left")
            val_var = tk.StringVar(value="---")
            tk.Label(row, textvariable=val_var, font=FONT_SM,
                     bg=SURFACE2, fg=TEXT).pack(side="right", padx=4)
            row._val_var = val_var
            row._ticker = ticker
            row.bind("<Button-1>", lambda e, t=ticker: self._load_from_portfolio(t))
            tk.Button(row, text="✕", font=FONT_SM, bg=SURFACE2, fg=RED,
                      relief="flat", cursor="hand2",
                      command=lambda t=ticker: self._remove_from_portfolio(t)).pack(side="right")

    def _load_from_portfolio(self, ticker):
        self.current_ticker.set(ticker)
        self.load_ticker()

    def _remove_from_portfolio(self, ticker):
        if ticker in self.portfolio:
            del self.portfolio[ticker]
            save_portfolio(self.portfolio)
            self._refresh_portfolio_ui()
            if not self.portfolio:
                self.total_var.set("Total: $0.00")
            else:
                threading.Thread(target=self._update_portfolio_prices, daemon=True).start()

    def _update_portfolio_prices(self):
        total = 0
        rows = self.port_frame.winfo_children()
        for row in rows:
            if hasattr(row, "_ticker"):
                try:
                    info = yf.Ticker(row._ticker).fast_info
                    price = float(info.last_price)
                    prev_close = float(info.previous_close)
                    shares = self.portfolio.get(row._ticker, 0)
                    val = price * shares
                    total += val
                    chg = price - prev_close
                    pct = (chg / prev_close) * 100
                    arrow = "▲" if chg >= 0 else "▼"
                    color = GREEN if chg >= 0 else RED
                    display = f"${val:,.0f} {arrow}{abs(pct):.1f}%"
                    row._val_var.set(display)
                    self.after(0, lambda r=row, c=color: self._set_row_color(r, c))

                    # Generate notification if price changed significantly
                    prev = self.portfolio_prev_prices.get(row._ticker)
                    if prev is not None and abs(pct) >= 1.0:
                        direction = "up" if chg >= 0 else "down"
                        msg = f"{row._ticker} is {direction} {abs(pct):.1f}% today  (${price:.2f})"
                        if msg not in self.notifications:
                            self.notifications.append(msg)
                            self.after(0, self._update_bell_badge)
                    self.portfolio_prev_prices[row._ticker] = price
                except:
                    pass
        self.after(0, lambda: self.total_var.set(f"Total: ${total:,.2f}"))

    def _set_row_color(self, row, color):
        for w in row.winfo_children():
            if isinstance(w, tk.Label) and w.cget("text") not in ["✕"]:
                try:
                    if "sh" in str(w.cget("text")) or "$" in str(w.cget("textvariable")):
                        w.config(fg=color)
                except:
                    pass

    def _update_bell_badge(self):
        count = len(self.notifications)
        if count > 0:
            self.bell_count_var.set(str(count))
            self.bell_badge.pack(side="left")
            self.bell_btn.config(fg=AMBER)
        else:
            self.bell_badge.pack_forget()
            self.bell_btn.config(fg=MUTED)

    def _show_notifications(self):
        popup = tk.Toplevel(self)
        popup.title("Notifications")
        popup.configure(bg=SURFACE)
        popup.geometry("340x400")
        popup.resizable(False, False)

        tk.Label(popup, text="🔔  NOTIFICATIONS", font=FONT_LG,
                 bg=SURFACE, fg=ACCENT).pack(anchor="w", padx=16, pady=(12,4))

        frame = tk.Frame(popup, bg=SURFACE)
        frame.pack(fill="both", expand=True, padx=12, pady=4)

        if not self.notifications:
            tk.Label(frame, text="No notifications yet.\nPrices update when you open the app.",
                     font=FONT_SM, bg=SURFACE, fg=MUTED, justify="left").pack(anchor="w", pady=8)
        else:
            for msg in reversed(self.notifications):
                color = GREEN if " up " in msg else RED
                row = tk.Frame(frame, bg=SURFACE2)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=("▲" if " up " in msg else "▼"),
                         font=FONT_SM, bg=SURFACE2, fg=color).pack(side="left", padx=8, pady=6)
                tk.Label(row, text=msg, font=FONT_SM, bg=SURFACE2,
                         fg=TEXT, anchor="w").pack(side="left", pady=6)

        def clear_all():
            self.notifications.clear()
            self._update_bell_badge()
            popup.destroy()

        tk.Button(popup, text="CLEAR ALL", font=FONT_SM, bg=SURFACE2,
                  fg=MUTED, relief="flat", padx=12, cursor="hand2",
                  command=clear_all).pack(pady=8)

if __name__ == "__main__":
    app = QuantApp()
    app.mainloop()