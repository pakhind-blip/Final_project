#Pakhin Daonan
#6810545859

import tkinter as tk
from tkinter import ttk
import threading, time, json, requests, websocket


import tkinter as tk
from tkinter import ttk
import threading, time, json, requests, websocket


# การ์ดราคา 1 เหรียญ ต่อ ws แล้วอัปเดตตัวเลข
class TickerCard:
    def __init__(self, parent, pair_ws, title):
        self.parent = parent
        self.pair_ws = pair_ws.lower()
        self.title = title
        self.running = False
        self.ws = None

        self.frame = ttk.Frame(parent, padding=16, style="Card.TFrame")
        ttk.Label(self.frame, text=self.title, style="Title.TLabel").pack(pady=(0, 8))
        self.price_label = tk.Label(
            self.frame, text="--,---",
            font=("Segoe UI", 30, "bold"),
            fg="#f5f5f5", bg="#1b1f27"
        )
        self.price_label.pack()

        self.change_label = ttk.Label(self.frame, text="-- (--)", style="CardMuted.TLabel")
        self.change_label.pack()

        self.vol_label = ttk.Label(self.frame, text="Vol 24h: --", style="CardMuted.TLabel")
        self.vol_label.pack(pady=(4, 0))

    def start(self):
        if self.running:
            return
        self.running = True
        url = f"wss://stream.binance.com:9443/ws/{self.pair_ws}@ticker"
        self.ws = websocket.WebSocketApp(url, on_message=self._on_msg)
        threading.Thread(target=self.ws.run_forever, daemon=True).start()

    def stop(self):
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
        self.ws = None

    def _on_msg(self, ws, message):
        if not self.running:
            return
        try:
            d = json.loads(message)
            price = float(d["c"])
            change = float(d["p"])
            pct = float(d["P"])
            vol = float(d["v"])
            self.parent.after(0, self.update_ui, price, change, pct, vol)
        except Exception:
            pass

    def update_ui(self, price, change, pct, vol):
        if not self.running:
            return
        col = "#22c55e" if change >= 0 else "#ef4444"
        s = "+" if change >= 0 else ""
        self.price_label.config(text=f"{price:,.2f}", fg=col)
        self.change_label.config(text=f"{s}{change:,.2f} ({s}{pct:.2f}%)", foreground=col)
        self.vol_label.config(text=f"Vol 24h: {vol:,.0f}")

    def pack(self, **kw):
        self.frame.pack(**kw)

    def hide(self):
        self.frame.pack_forget()


# แผงขวา ดึง volume / orderbook / trades แบบวนๆ
class RightPanel:
    def __init__(self, parent, start_display, start_symbol):
        self.parent = parent
        self.display = start_display
        self.symbol = start_symbol
        self.running = False

        self.frame = ttk.Frame(parent, style="App.TFrame")
        self.frame.pack(fill="both", expand=True)

        self.vol_box = ttk.Frame(self.frame, padding=14, style="Card.TFrame")
        self.vol_box.pack(fill="x", pady=(0, 8))
        self.vol_title = ttk.Label(self.vol_box, text=f"{self.display} 24h Volume", style="Title.TLabel")
        self.vol_title.pack(anchor="w", pady=(0, 6))
        self.vol_value = ttk.Label(self.vol_box, text="Loading...", style="CardMuted.TLabel")
        self.vol_value.pack(anchor="w")

        self.ob_box = ttk.Frame(self.frame, padding=14, style="Card.TFrame")
        self.ob_box.pack(fill="both", pady=(0, 8))
        self.ob_title = ttk.Label(self.ob_box, text=f"{self.symbol} Order Book (Top 10)", style="Title.TLabel")
        self.ob_title.pack(anchor="w", pady=(0, 6))
        self.ob_text = tk.Text(self.ob_box, height=10, width=40, bg="#1b1f27", fg="#f5f5f5",
                               font=("Consolas", 9), bd=0, relief="flat")
        self.ob_text.pack(fill="both", expand=True)
        self.ob_text.configure(state="disabled")

        self.tr_box = ttk.Frame(self.frame, padding=14, style="Card.TFrame")
        self.tr_box.pack(fill="both")
        self.tr_title = ttk.Label(self.tr_box, text=f"{self.symbol} Recent Trades", style="Title.TLabel")
        self.tr_title.pack(anchor="w", pady=(0, 6))
        self.tr_text = tk.Text(self.tr_box, height=10, width=40, bg="#1b1f27", fg="#f5f5f5",
                               font=("Consolas", 9), bd=0, relief="flat")
        self.tr_text.pack(fill="both", expand=True)
        self.tr_text.configure(state="disabled")

    def set_symbol(self, display, symbol):
        self.display = display
        self.symbol = symbol.upper()
        self.vol_title.config(text=f"{self.display} 24h Volume")
        self.ob_title.config(text=f"{self.symbol} Order Book (Top 10)")
        self.tr_title.config(text=f"{self.symbol} Recent Trades")
        self.vol_value.config(text="Loading...")
        self._set_text(self.ob_text, "Loading order book...")
        self._set_text(self.tr_text, "Loading trades...")

    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._loop_volume, daemon=True).start()
        threading.Thread(target=self._loop_orderbook, daemon=True).start()
        threading.Thread(target=self._loop_trades, daemon=True).start()

    def stop(self):
        self.running = False

    def _set_text(self, widget, text):
        if not widget.winfo_exists():
            return
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state="disabled")

    def _loop_volume(self):
        url = "https://api.binance.com/api/v3/ticker/24hr"
        while self.running:
            try:
                r = requests.get(url, params={"symbol": self.symbol}, timeout=5)
                d = r.json()
                vol = float(d["volume"])
                qv = float(d.get("quoteVolume", 0.0))
                base = self.display.split("/")[0]
                txt = f"{vol:,.0f} {base}  (~{qv:,.0f} USDT)"
                self.parent.after(0, self.vol_value.config, {"text": txt})
            except Exception:
                pass
            time.sleep(5)

    def _loop_orderbook(self):
        url = "https://api.binance.com/api/v3/depth"
        while self.running:
            try:
                r = requests.get(url, params={"symbol": self.symbol, "limit": 10}, timeout=5)
                d = r.json()
                bids = d.get("bids", [])
                asks = d.get("asks", [])

                lines = ["BIDS"]
                for p, q in bids:
                    lines.append(f"{float(p):>12,.2f}  {float(q):>10.4f}")
                lines.append("")
                lines.append("ASKS")
                for p, q in asks:
                    lines.append(f"{float(p):>12,.2f}  {float(q):>10.4f}")

                self.parent.after(0, self._set_text, self.ob_text, "\n".join(lines))
            except Exception:
                pass
            time.sleep(3)

    def _loop_trades(self):
        url = "https://api.binance.com/api/v3/trades"
        while self.running:
            try:
                r = requests.get(url, params={"symbol": self.symbol, "limit": 12}, timeout=5)
                data = r.json()
                lines = []
                for tr in data:
                    side = "SELL" if tr.get("isBuyerMaker", False) else "BUY "
                    price = float(tr["price"])
                    qty = float(tr["qty"])
                    lines.append(f"{side:4}  {price:>11,.2f}  {qty:>10.4f}")
                self.parent.after(0, self._set_text, self.tr_text, "\n".join(lines))
            except Exception:
                pass
            time.sleep(3)


# ตัวหลัก จัดหน้าจอ ปุ่ม toggle แล้วคุม start/stop
class DashboardApp:
    def __init__(self, root):
        self.root = root
        root.title("Crypto Dashboard (01219114 / 01219115)")
        root.configure(bg="#111317")
        root.geometry("1350x700")

        self._style()

        outer = ttk.Frame(root, style="App.TFrame", padding=16)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Cryptocurrency Dashboard", style="Header.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Real-time Tickers (BTC • ETH • SOL)", style="Muted.TLabel").pack(anchor="w", pady=(2, 10))

        self.controls = ttk.Frame(outer, style="App.TFrame")
        self.controls.pack(fill="x", pady=6)

        body = ttk.Frame(outer, style="App.TFrame")
        body.pack(fill="both", expand=True, pady=10)

        left = ttk.Frame(body, style="App.TFrame")
        left.pack(side="left", fill="both", expand=True)

        self.ticker_area = ttk.Frame(left, style="App.TFrame")
        self.ticker_area.pack(fill="both", expand=True)

        right = ttk.Frame(body, style="App.TFrame")
        right.pack(side="right", fill="y", padx=(10, 0))

        top = ttk.Frame(right, style="App.TFrame")
        top.pack(fill="x", pady=(0, 8))

        self.right_label = ttk.Label(top, text="Right panel: BTC/USDT", style="Muted.TLabel")
        self.right_label.pack(side="left")

        btns = ttk.Frame(top, style="App.TFrame")
        btns.pack(side="right")

        ttk.Button(btns, text="BTC", style="AccentSmall.TButton", width=6,
                   command=lambda: self.change_right("BTC/USDT", "BTCUSDT")).pack(side="left", padx=4)
        ttk.Button(btns, text="ETH", style="AccentSmall.TButton", width=6,
                   command=lambda: self.change_right("ETH/USDT", "ETHUSDT")).pack(side="left", padx=4)
        ttk.Button(btns, text="SOL", style="AccentSmall.TButton", width=6,
                   command=lambda: self.change_right("SOL/USDT", "SOLUSDT")).pack(side="left", padx=4)

        self.btc = TickerCard(self.ticker_area, "btcusdt", "BTC/USDT")
        self.eth = TickerCard(self.ticker_area, "ethusdt", "ETH/USDT")
        self.sol = TickerCard(self.ticker_area, "solusdt", "SOL/USDT")

        self.show_btc = True
        self.show_eth = True
        self.show_sol = True

        self.btc.pack(side="left", expand=True, fill="both", padx=8, pady=8)
        self.eth.pack(side="left", expand=True, fill="both", padx=8, pady=8)
        self.sol.pack(side="left", expand=True, fill="both", padx=8, pady=8)
        self.btc.start()
        self.eth.start()
        self.sol.start()

        self.right_panel = RightPanel(right, "BTC/USDT", "BTCUSDT")
        self.right_panel.start()

        self._make_toggle("BTC", lambda: self.toggle("btc"))
        self._make_toggle("ETH", lambda: self.toggle("eth"))
        self._make_toggle("SOL", lambda: self.toggle("sol"))

        root.protocol("WM_DELETE_WINDOW", self.close)

    def _make_toggle(self, name, cmd):
        f = ttk.Frame(self.controls, style="App.TFrame")
        f.pack(side="left", padx=12)
        b = ttk.Button(f, text=f"Hide {name}", style="Accent.TButton", width=12, command=cmd)
        b.pack(anchor="w")
        st = ttk.Label(f, text=f"{name}: visible", style="Muted.TLabel")
        st.pack(anchor="w")
        setattr(self, f"{name.lower()}_btn", b)
        setattr(self, f"{name.lower()}_st", st)

    def toggle(self, which):
        if which == "btc":
            self._toggle_one("btc", self.btc, "BTC")
        elif which == "eth":
            self._toggle_one("eth", self.eth, "ETH")
        else:
            self._toggle_one("sol", self.sol, "SOL")

    def _toggle_one(self, attr, obj, name):
        show = getattr(self, f"show_{attr}")
        b = getattr(self, f"{attr}_btn")
        st = getattr(self, f"{attr}_st")

        if show:
            obj.stop()
            obj.hide()
            b.config(text=f"Show {name}")
            st.config(text=f"{name}: hidden")
        else:
            obj.pack(side="left", expand=True, fill="both", padx=8, pady=8)
            obj.start()
            b.config(text=f"Hide {name}")
            st.config(text=f"{name}: visible")

        setattr(self, f"show_{attr}", not show)

    def change_right(self, display, symbol):
        self.right_label.config(text=f"Right panel: {display}")
        self.right_panel.stop()
        self.right_panel.set_symbol(display, symbol)
        self.right_panel.start()

    def _style(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("App.TFrame", background="#111317")
        s.configure("Card.TFrame", background="#1b1f27", relief="ridge")
        s.configure("Header.TLabel", background="#111317", foreground="#f5f5f5", font=("Segoe UI", 20, "bold"))
        s.configure("Title.TLabel", background="#1b1f27", foreground="#f5f5f5", font=("Segoe UI", 13, "bold"))
        s.configure("Muted.TLabel", background="#111317", foreground="#a0a4b1")
        s.configure("CardMuted.TLabel", background="#1b1f27", foreground="#a0a4b1")

        base = {
            "background": "#1E2129", "foreground": "white",
            "borderwidth": 2, "relief": "solid",
            "bordercolor": "#f5f5f5", "focusthickness": 1, "focuscolor": "#f5f5f5"
        }
        s.configure("Accent.TButton", **base, padding=(8, 4), font=("Segoe UI", 10, "bold"))
        s.configure("AccentSmall.TButton", **base, padding=(4, 2), font=("Segoe UI", 9, "bold"))
        s.map("Accent.TButton", background=[("active", "#262A33"), ("pressed", "#171921")])
        s.map("AccentSmall.TButton", background=[("active", "#262A33"), ("pressed", "#171921")])

    def close(self):
        try:
            self.btc.stop()
            self.eth.stop()
            self.sol.stop()
            self.right_panel.stop()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    websocket.enableTrace(False)
    root = tk.Tk()
    DashboardApp(root)
    root.mainloop()
