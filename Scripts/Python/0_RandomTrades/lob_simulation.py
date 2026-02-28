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
    
    def sample_background_orders(self, lam=2.0, p_buy=0.5,
                             size_mean=200, size_std=0.8,
                             size_min=10, size_max=2000):
        """
        Returns a list of signed market-order quantities for this timestep.
        """
        k = np.random.poisson(lam)  # number of market orders this step
        orders = []
        for _ in range(k):
            is_buy = (self.rng.random() < p_buy)

            # lognormal-like size: many small, few big
            raw = np.random.lognormal(mean=np.log(size_mean), sigma=size_std)
            sz = int(max(size_min, min(size_max, round(raw))))

            orders.append(+sz if is_buy else -sz)
        return orders
        
        def snapshot(self, t):
            return {"t": t, "bids": list(self.bids), "asks": list(self.asks)}
    
    def apply_background_flow(self, lam=2.0, p_buy=0.5,
                          size_mean=200, size_std=0.8,
                          size_min=10, size_max=2000):
        orders = self.sample_background_orders(
            lam=lam, p_buy=p_buy,
            size_mean=size_mean, size_std=size_std,
            size_min=size_min, size_max=size_max
        )
        reports = []
        for q in orders:
            rep = self.execute_market_order(q)
            reports.append(rep)
        return orders, reports
    
    def snapshot(self, t):
        return {"t": t, "bids": list(self.bids), "asks": list(self.asks)}
    
    def step(self, t, trades=None,
         bg_lam=2.0, bg_p_buy=0.5,
         rho=0.3, decay=0.85, noise=0.05):

        if trades is None:
            trades = []

        bg_orders, bg_reports = self.apply_background_flow(lam=bg_lam, p_buy=bg_p_buy)

        trade_reports = []
        for q in trades:
            trade_reports.append(self.execute_market_order(q))

        self.refill_step(rho=rho, decay=decay, noise=noise)

        return {"t": t, "bg_orders": bg_orders, "bg_reports": bg_reports, "trade_reports": trade_reports}
    
    def run(self, n_steps, trade_schedule=None,
        bg_lam=2.0, bg_p_buy=0.5,
        rho=0.3, decay=0.85, noise=0.05):

        if trade_schedule is None:
            trade_schedule = {}

        history = [self.snapshot(0)]
        step_logs = {}

        for t in range(1, n_steps + 1):
            val = trade_schedule.get(t, None)
            # normalize: always make it a list of signed quantities
            if val is None:
                trades = []
            elif isinstance(val, (list, tuple)):
                trades = list(val)
            else:
                trades = [val]
            log = self.step(
                t,
                trades=trades,
                bg_lam=bg_lam, bg_p_buy=bg_p_buy,
                rho=rho, decay=decay, noise=noise
            )
            step_logs[t] = log
            history.append(self.snapshot(t))
        return history, step_logs

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

            levels.append((px, max(1, int(round(qty))))) # we have levels represented as a list inside a loop, in each loop we append a new level of volume of bid/ask orders into the list at a price px

        return levels # output of levels is something like [(px0, qty0), (px1, qty1), (px2, qty2), ...]

    def order_book_levels(self, execution_qty, decay=0.85, noise=0.10): # generate the levels in bid/ask sides in the lob
        best_bid, best_ask = self.best_bid_ask()
        buy_vol, sell_vol = self.total_side_volumes(execution_qty)

        # store targets for future refill steps
        self.target_buy_vol  = buy_vol
        self.target_sell_vol = sell_vol

        self.bids = self._build_side(best_bid, "bid", buy_vol,  decay=decay, noise=noise) # the bid side is generated from the best bid, and a decaying value from best bid, and the sum of volume of bid side is constrained with some noise
        self.asks = self._build_side(best_ask, "ask", sell_vol, decay=decay, noise=noise) # the ask side is generated from best ask, decaying value from best ask and ask side volume is contrained with some noise
        return self.bids, self.asks # self.bids and self.asks returns a tuple of (price, quantity) for each level respectively of the bid/ask spread i.e. [(px0, qty0), (px1, qty1), (px2, qty2), ...]

    def execute_market_order(self, qty_signed): # takes the input buy/sell quantity and executes them on the lob instantly
        """
        qty_signed < 0 : SELL -> consumes bids
        qty_signed > 0 : BUY  -> consumes asks

        Returns a fill report + mutates the book.
        """
        if qty_signed == 0:
            return {"filled_qty": 0, "remaining_qty": 0, "vwap": None, "fills": [], "notional": 0.0}

        remaining = abs(qty_signed) # how much of the order has been executed
        fills = [] # a tuple of (price, quantity)
        notional = 0.0  # signed (SELL -> negative); a value representing the price filled, i.e. price * quantity filled

        if qty_signed < 0: # we define the side of execution based on if quantity if < or > 0, than we execute on either self.bids or self.asks
            book = self.bids
            sign = -1
        else:
            book = self.asks
            sign = +1

        for i, (px, lvl_qty) in enumerate(book): # enumerate(book) returns (i, (price, quantity)), where i is the index for the position of the book; i.e. (0, (price, quantity)) of the bid side is the first level (i.e. best bid) of the bid side
            if remaining <= 0: # we loop through the levels of the book starting from i = 0 i.e. the top level, to i = len(book), if after i = 0, remaining -= take = 0 than that means our order is fully executed 
                break
            take = min(lvl_qty, remaining) # min() function returns the value that is smaller between lvl_qty and remaining, i.e. take = min(5,10), take = 5, in a lob level, if you order is 1000, and volume is 900 than min(900, 1000) = 900, so you take 900 of that level
            if take > 0:
                fills.append((px, sign * take)) # signed fill qty; price of order being filled is px, amount filled is take
                notional += px * (sign * take) # signed cashflow/notional; the total money received from buying or selling
                lvl_qty -= take # we subtract the amount executed from our order
                remaining -= take # and update the amount needed to be executed
                book[i] = (px, lvl_qty) # we update the lob level i of the bid/ask side with the new lvl_qty

        # Optional: remove empty levels
        if qty_signed < 0:
            self.bids = [(p, q) for (p, q) in self.bids if q > 0] # we overrides the list self.bids with a loop that states, add the tuple where only the second element is > 0, i.e. let (p, q) represents the tuple in self.bids, where q is the quantity in self.bids, the loop looks over each tuple in self.bids and chooses to accept only q > 0, thus removing a lob level if q < 0
        else:
            self.asks = [(p, q) for (p, q) in self.asks if q > 0] # same process as self.bids for for self.asks

        filled_qty = sum(q for _, q in fills)  # from the list fills, we have a tuple of (px, sign * take), when we say q for _, q we are looking at the second element sign * take, and we sum over all the second elements in the list to get total number of quantity filled
        remaining_qty = qty_signed - filled_qty # calculate the amount of quantity left of the order, it is calculated as, if qty_signed < 0, than sign = -1, therefore in the fills list, the quantity is (-1 * take); the remaining_qty would always be smaller than qty_signed

        filled_abs = abs(filled_qty) # take the positive values of filled_qty
        vwap = (abs(notional) / filled_abs) if filled_abs > 0 else None # value weighted average price, calculates the price of execution * quantity / quantity filled, i.e. (28.07 * 1000 + 28.06 * 1000)/ 2000 = 28.065; (28.07) * 2000/ 2000 = 28.07; here we see that vwap is higher if we don't walk the book 

        return {
            "requested_qty": qty_signed,
            "filled_qty": filled_qty,
            "remaining_qty": remaining_qty,
            "vwap": vwap,
            "fills": fills,
            "notional": notional,
        }
    
    def _pad_to_n_levels(self, side): # we want to get ride of the level that is empty, and if a order has deplited a level, we want to have it as a "permanent" impact on the lob, thus we generate a new level at the end of the lob
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

    def _refill_side(self, side, total_volume, rho=0.30, decay=0.85, noise=0.05): # we fill all the levels in a random way (including filling the new levels if best bid/ask is depleted)
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

    def refill_step(self, rho=0.30, decay=0.85, noise=0.05): # we refill the lob with the initial function: total_side_volume
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

# 1) Create + initialize the LOB at t=0
ob = OrderBook(reference_price=28.13, tick_size=0.01, n_levels=10, seed=7)
ob.order_book_levels(execution_qty=-7500, decay=0.85, noise=0.10)
ob.print_book("t=0 (init)")

# 2) Schedule your “large” orders at specific timesteps
# (one order per timestep version)
trade_schedule = {
    1: -7500,   # big sell at t=1
    5: -2000,   # smaller sell at t=5
}

# 3) Run the simulation for N steps
history, logs = ob.run(
    n_steps=10,
    trade_schedule=trade_schedule,
    bg_lam=3.0,        # avg 3 background market orders per step
    bg_p_buy=0.50,     # 50/50 buy vs sell background flow
    rho=0.30,          # refill speed
    decay=0.85,
    noise=0.05
)

# 4) Inspect specific timesteps
for t in [1, 2, 5, 6, 10]:
    snap = history[t]                 # history[0] is t=0
    ob.bids, ob.asks = snap["bids"], snap["asks"]
    ob.print_book(f"t={t} snapshot")

    # Print what happened at that timestep
    log = logs[t]
    print(f"\n--- t={t} events ---")
    print("Background orders:", log["bg_orders"])
    if t in trade_schedule:
        print("Scheduled trade report:")
        # Access the first report from the 'trade_reports' list
        ob.print_execution_report(log["trade_reports"][0], f"Scheduled trade at t={t}")