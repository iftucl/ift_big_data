import numpy as np
import matplotlib.pyplot as plt
import random
import math

class OrderBook:
    def __init__(self, reference_price, tick_size, n_levels=10, seed=None):
        self.reference_price = float(reference_price)
        self.tick_size = float(tick_size)
        self.n_levels = int(n_levels)
        self.rng = random.Random(seed)

        self.bids = []  # list of (price, qty)
        self.asks = []

    def round_to_tick(self, x, side=None):
        # side can be "down" for bids, "up" for asks
        ticks = x / self.tick_size # Given a reference price x = 24.108 and a tick size of self.tick_size = 0.01 than math.floor(2410.8) = 2410 and math.ceil(2410.8) = 2411
        if side == "down":
            return math.floor(ticks) * self.tick_size
        if side == "up":
            return math.ceil(ticks) * self.tick_size
        return round(ticks) * self.tick_size # if sides = None than round

    def generate_random_spread(self): # assume the spread between best_bid and best_ask if between 0.1% to 1% of the price
        lower = self.reference_price * 0.001  # 0.1%
        upper = self.reference_price * 0.01   # 1%
        return self.rng.uniform(lower, upper)

    def best_bid_ask(self):
        spread = self.generate_random_spread()
        mid = self.round_to_tick(self.reference_price)  # mid aligned to tick
        best_bid = self.round_to_tick(mid - spread/2, side="down")
        best_ask = self.round_to_tick(mid + spread/2, side="up")
        return best_bid, best_ask

    def total_side_volumes(self, execution_qty): # The volume of buy and sell should be between 50 to 100 times the size of our order each
        q = abs(execution_qty)
        mult = self.rng.uniform(5, 10)
        buy_volume  = mult * q
        sell_volume = buy_volume * self.rng.uniform(0.9, 1.1)
        return buy_volume, sell_volume

    def _decay_weights(self, decay):
        # weights: [1, decay, decay^2, ...]
        return [decay**i for i in range(self.n_levels)] # We want the volume of bid/ask to decrease farther away from the mid price

    def _build_side(self, best_price, side, total_volume,
                    decay = 0.85, noise = 0.10):
        """
        side: "bid" or "ask"
        total_volume: target total depth on that side (in shares/units)
        decay: how fast it decays (smaller -> faster decay)
        noise: multiplicative noise per level, e.g. 0.10 = ±10% ish
        """
        weights = self._decay_weights(decay)
        wsum = sum(weights)

        levels = []
        for i, w in enumerate(weights): # Assign a (index, item) pair to the list of elements in weights
            # price ladder
            if side == "bid":
                px = best_price - i * self.tick_size
                px = self.round_to_tick(px, side="down")
            else:
                px = best_price + i * self.tick_size
                px = self.round_to_tick(px, side="up")

            # allocate volume by normalized weight
            qty = total_volume * (w / wsum) # (w / wsum) < 1, thus the sum of total_volume * (w / wsum) is approx. total_volume

            # add noise (optional)
            eps = self.rng.uniform(-noise, noise) # we want the levels below/above the best bid/ask price to decay in volume
            qty = qty * (1.0 + eps)

            levels.append((px, max(1, int(round(qty)))))

        return levels

    def order_book_levels(self, execution_qty, decay=0.85, noise=0.10):
        best_bid, best_ask = self.best_bid_ask()
        buy_vol, sell_vol = self.total_side_volumes(execution_qty)

        # store targets for future refill steps
        self.target_buy_vol  = buy_vol
        self.target_sell_vol = sell_vol

        self.bids = self._build_side(best_bid, "bid", buy_vol,  decay=decay, noise=noise)
        self.asks = self._build_side(best_ask, "ask", sell_vol, decay=decay, noise=noise)
        return self.bids, self.asks

    def execute_market_order(self, qty_signed):
        """
        qty_signed < 0 : SELL -> consumes bids
        qty_signed > 0 : BUY  -> consumes asks

        Returns a fill report + mutates the book.
        """
        if qty_signed == 0:
            return {"filled_qty": 0, "remaining_qty": 0, "vwap": None, "fills": [], "notional": 0.0}

        remaining = abs(qty_signed)
        fills = []
        notional = 0.0  # signed (SELL -> negative)

        if qty_signed < 0:
            book = self.bids  # list of (price, qty), best first
            sign = -1
        else:
            book = self.asks
            sign = +1

        for i, (px, lvl_qty) in enumerate(book):
            if remaining <= 0:
                break
            take = min(lvl_qty, remaining) # min() function returns the value that is smaller between lvl_qty and remaining, i.e. take = min(5,10), take = 5
            if take > 0:
                fills.append((px, sign * take))          # signed fill qty; price of order being filled is px, amount filled is take
                notional += px * (sign * take)          # signed cashflow/notional; the total money received from buying or selling
                lvl_qty -= take
                remaining -= take
                book[i] = (px, lvl_qty)

        # Optional: remove empty levels
        if qty_signed < 0:
            self.bids = [(p, q) for (p, q) in self.bids if q > 0]
        else:
            self.asks = [(p, q) for (p, q) in self.asks if q > 0]

        filled_qty = sum(q for _, q in fills)  # signed
        remaining_qty = qty_signed - filled_qty

        filled_abs = abs(filled_qty)
        vwap = (abs(notional) / filled_abs) if filled_abs > 0 else None

        return {
            "requested_qty": qty_signed,
            "filled_qty": filled_qty,
            "remaining_qty": remaining_qty,
            "vwap": vwap,
            "fills": fills,
            "notional": notional,
        }

    def _pad_to_n_levels(self, side):
        levels = self.bids if side == "bid" else self.asks
        if not levels:
            return

        # truncate if too long
        if len(levels) > self.n_levels:
            del levels[self.n_levels:]

        # add new levels at worse prices only
        while len(levels) < self.n_levels:
            last_px = levels[-1][0]
            if side == "bid":
                new_px = self.round_to_tick(last_px - self.tick_size, side="down")
            else:
                new_px = self.round_to_tick(last_px + self.tick_size, side="up")
            levels.append((new_px, 0))

    def _refill_side(self, side, total_volume, rho=0.30, decay=0.85, noise=0.05):
        levels = self.bids if side == "bid" else self.asks
        weights = self._decay_weights(decay)
        wsum = sum(weights)

        new_levels = []
        for i, (px, q) in enumerate(levels):
            target_q = total_volume * (weights[i] / wsum)

            # move part-way toward target + small noise
            eps = self.rng.uniform(-noise, noise)
            q_new = q + rho * (target_q - q) + eps * target_q

            new_levels.append((px, max(0, int(round(q_new)))))

        if side == "bid":
            self.bids = new_levels
        else:
            self.asks = new_levels

    def refill_step(self, rho=0.30, decay=0.85, noise=0.05):
        # make sure we have targets
        if not hasattr(self, "target_buy_vol") or not hasattr(self, "target_sell_vol"):
            raise RuntimeError("Call order_book_levels(...) once first to set target volumes.")

        # ensure we have exactly n_levels (adding only worse prices)
        self._pad_to_n_levels("bid")
        self._pad_to_n_levels("ask")

        # refill quantities (no price improvement, prices unchanged)
        self._refill_side("bid", self.target_buy_vol,  rho=rho, decay=decay, noise=noise)
        self._refill_side("ask", self.target_sell_vol, rho=rho, decay=decay, noise=noise)

    def print_book(self, title="LOB Snapshot", max_levels=None):
        if max_levels is None:
            max_levels = self.n_levels

        print("\n" + "=" * 60)
        print(title)
        print("-" * 60)

        # Print top-of-book
        best_bid = self.bids[0] if self.bids else (None, None)
        best_ask = self.asks[0] if self.asks else (None, None)
        print(f"Best Ask: {best_ask[0]} x {best_ask[1]} | Best Bid: {best_bid[0]} x {best_bid[1]}")
        print("-" * 60)

        # Print ladder (asks above, bids below)
        print(f"{'ASKS':>24} | {'BIDS':<24}")
        print(f"{'price   qty':>24} | {'price   qty':<24}")
        print("-" * 60)

        for i in range(max_levels):
            ap = aq = bp = bq = ""
            if i < len(self.asks):
                ap, aq = self.asks[i]
                ap, aq = f"{ap:.2f}", f"{aq}"
            if i < len(self.bids):
                bp, bq = self.bids[i]
                bp, bq = f"{bp:.2f}", f"{bq}"

            left  = f"{ap:>7} {aq:>6}"
            right = f"{bp:<7} {bq:<6}"
            print(f"{left} | {right}")

        print("=" * 60)


    def print_execution_report(self, report, title="Execution Report"):
        print("\n" + "=" * 60)
        print(title)
        print("-" * 60)
        print(f"Requested Qty:  {report['requested_qty']}")
        print(f"Filled Qty:     {report['filled_qty']}")
        print(f"Remaining Qty:  {report['remaining_qty']}")
        print(f"VWAP:           {report['vwap']}")
        print(f"Notional:       {report['notional']}")
        print("-" * 60)
        print("Fills (price, signed_qty):")
        for px, q in report["fills"]:
            print(f"  {px:.2f}, {q}")
        print("=" * 60)

# build
ob = OrderBook(reference_price=28.13, tick_size=0.01, n_levels=10, seed=7)

# generate book BEFORE
ob.order_book_levels(execution_qty=-7500, decay=0.85, noise=0.10)
ob.print_book("BEFORE: Synthetic LOB (decay=0.85)", max_levels=10)

# execute SELL market order
report = ob.execute_market_order(-7500)
ob.print_execution_report(report, "TRADE: SELL -7500")

# book AFTER
ob.print_book("AFTER: LOB after consuming bids", max_levels=10)

ob.print_book("AFTER trade")
ob.refill_step(rho=0.3, decay=0.85, noise=0.05)
ob.print_book("NEXT TIMESTEP after refill")

"""Here's how `enumerate()` works with an example:"""

my_list = ['apple', 'banana', 'cherry', 'date']

print("Using enumerate to get index and value:")
for index, value in enumerate(my_list):
    print(f"Index: {index}, Value: {value}")

print("\nUsing enumerate with a custom starting index:")
for index, value in enumerate(my_list, start=1):
    print(f"Item number: {index}, Fruit: {value}")

# You can also convert the enumerate object to a list of tuples:
enumerated_list = list(enumerate(my_list))
print(f"\nEnumerate object converted to list of tuples: {enumerated_list}")

class OrderBook:

  def __init__(self, reference_price, volume, execution_quantity, tick_size):
    self.reference_price = reference_price
    self.volume = volume
    self.execution_quantity = execution_quantity
    self.tick_size = tick_size

  def generate_random_spread(self): # Randomly generates the upper and lower bounds of the spraed
    lower_bound = self.reference_price * 0.001 # 0.1% of price
    upper_bound = self.reference_price * 0.01  # 1% of price
    return random.uniform(lower_bound, upper_bound)

  def best_bid_ask(self):
    spread = generate_random_spread()
    best_bid = f"{round((self.reference_price - spread/2)/self.tick_size)*self.tick_size}"
    best_ask = f"{self.reference_price + spread/2}"
    return best_bid, best_ask

  def volume(self):
    total_buy_side_volume = random.uniform(50,100)
    total_sell_side_volume = total_buy_side_volume * random.uninform(0.9,1.1)
    return total_buy_side_volume, total_sell_side_volume

  def order_book_levels(self):

print(f"{round((23.18 - 0.02318/2)/0.01)*0.01}")

rng = np.random.default_rng(1)
print(np.array([23.12 - i*0.01 for i in range(10)]))
print(np.array([4000 * (0.85**i) for i in range(10)], dtype=float))
print(rng.normal(0.0, 0.15, size=10))

def initial_lob(reference_price=28.13, tick=0.01, initial_spread=2, L=10,
                  base_qty=4000, decay=0.85, noise=0.15, seed=1):
    rng = np.random.default_rng(seed)

    mid = reference_price
    best_bid = f"{mid - (initial_spread/2) * tick:.2f}"
    best_ask = f"{mid + (initial_spread/2) * tick:.2f}"

    bids_p = np.array([best_bid - i*tick for i in range(L)])
    asks_p = np.array([best_ask + i*tick for i in range(L)])

    def gen_qty():
        q = np.array([base_qty * (decay**i) for i in range(L)], dtype=float)
        eps = rng.normal(0.0, noise, size=L)
        q = q * np.clip(1.0 + eps, 0.2, 2.0)
        return np.maximum(1, q.astype(int))

    bids_q = gen_qty()
    asks_q = gen_qty()

    return {"mid": mid, "bids": list(zip(bids_p, bids_q)), "asks": list(zip(asks_p, asks_q))}

lob = initial_lob(reference_price=28.13, tick=0.01, spread_ticks=2, L=10, seed=7)

# Prepare data for plotting
bid_prices = np.array([p for p, q in lob["bids"]])
bid_qty    = np.array([q for p, q in lob["bids"]])
ask_prices = np.array([p for p, q in lob["asks"]])
ask_qty    = np.array([q for p, q in lob["asks"]])

fig, ax = plt.subplots(figsize=(7, 5))

# Plot bids as negative to show left side
ax.barh(bid_prices, -bid_qty, height=0.008)
ax.barh(ask_prices,  ask_qty, height=0.008)

ax.axhline(lob["mid"], linewidth=1)

ax.set_xlabel("Depth (shares)")
ax.set_ylabel("Price")
ax.set_title("Synthetic Limit Order Book Snapshot (10 levels)")
ax.set_yticks(np.concatenate([bid_prices[::-1], [lob["mid"]], ask_prices]))
ax.grid(True, axis="x", linewidth=0.5)

# Symmetric x-limits for readability
mx = max(bid_qty.max(), ask_qty.max())
ax.set_xlim(-mx*1.15, mx*1.15)

out_path = "/mnt/data/synth_lob.png"
plt.tight_layout()
plt.savefig(out_path, dpi=200)