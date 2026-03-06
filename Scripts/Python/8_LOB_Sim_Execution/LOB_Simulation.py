import math
import random
import numpy as np

class OrderBook:
    def __init__(self, reference_price, tick_size, n_levels=10, seed=None):
        self.reference_price = float(reference_price)
        self.tick_size = float(tick_size)
        self.n_levels = int(n_levels)

        # we create a random number generator and define a seed which allows for reproducibility,
        # if seed = None than produce a random number between 0 and 1; we call on the class random.Random([seed])
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        self.bids = [] # list of (price, qty)
        self.asks = []

        self.target_buy_vol = None
        self.target_sell_vol = None

        self.last_exhausted_best_bid = None  # price of last fully depleted best bid
        self.last_exhausted_best_ask = None  # price of last fully depleted best ask

        # market maker parameters (set these from outside to control MM behavior)
        self.mm_p_restore = 1
        self.mm_vol_frac = 0.10
        self.mm_min_qty = 1

    # ---------- utilities ----------
    def round_to_tick(self, x, side=None):
      # side can be "down" for bids, "up" for asks
        # NOTE: using integer tick rounding avoids float issues that can create duplicate levels
        # e.g. 28.16 stored as 28.160000000000004 -> ceil could push it to 28.17
        inv = 1.0 / self.tick_size
        ticks = x * inv # Given a reference price x = 24.108 and a tick size of self.tick_size = 0.01 than math.floor(2410.8) = 2410 and math.ceil(2410.8) = 2411

        eps = 1e-9
        if side == "down":
            return math.floor(ticks + eps) / inv
        if side == "up":
            return math.ceil(ticks - eps) / inv
        return round(ticks) / inv # if sides = None than round

    def _ladder_price(self, best_price, i, side):
        # Build ladder prices in integer ticks to avoid float rounding duplicates
        best_ticks = int(round(best_price / self.tick_size))
        if side == "bid":
            return (best_ticks - i) * self.tick_size
        else:
            return (best_ticks + i) * self.tick_size

    def _merge_levels(self, levels, side):
        # Merge quantities at the same price level (guardrail against collisions)
        agg = {}
        for p, q in levels:
            agg[p] = agg.get(p, 0) + q
        merged = list(agg.items())
        merged.sort(key=lambda x: x[0], reverse=(side == "bid"))
        return merged

    # ---------- init book ----------
    def generate_random_spread(self): # assume the spread between best_bid and best_ask if between 0.1% to 1% of the price
        lower = self.reference_price * 0.001
        upper = self.reference_price * 0.002
        return self.rng.uniform(lower, upper)

    def best_bid_ask(self):
        spread = self.generate_random_spread()
        mid = self.round_to_tick(self.reference_price)  # mid aligned to tick
        best_bid = self.round_to_tick(mid - spread / 2, side="down")
        best_ask = self.round_to_tick(mid + spread / 2, side="up")
        return best_bid, best_ask

    def total_side_volumes(self, execution_qty, mult_low=5.0, mult_high=10.0): # The volume of buy and sell should be between 50 to 100 times the size of our order each
        q = abs(execution_qty)
        mult = self.rng.uniform(mult_low, mult_high)
        buy_volume = mult * q
        sell_volume = buy_volume * self.rng.uniform(0.9, 1.1)
        return buy_volume, sell_volume

    def _hump_weights(self, hump_center=3, hump_sigma=1.5, tail_decay=0.20, top_dip=0.40):
        """
        Hump-shaped weights over levels i = 0..n_levels-1.

        - i=0 (at spread/top-of-book) is damped by top_dip (<1) to represent low volume there.
        - Peak is around hump_center (few ticks deep).
        - tail_decay controls how fast depth falls off far from the price.
        """
        idx = np.arange(self.n_levels, dtype=float)

        hump = np.exp(-0.5 * ((idx - float(hump_center)) / float(hump_sigma))**2)
        tail = np.exp(-float(tail_decay) * idx)

        w = hump * tail
        w[0] *= float(top_dip)   # low volume at the spread/top level

        # avoid exactly-zero weights
        w = np.maximum(w, 1e-12)
        return w.tolist()

    def _build_side(self, best_price, side, total_volume,
                hump_center=3, hump_sigma=1.5, tail_decay=0.20, top_dip=0.40,
                noise=0.10):
        """
        Builds one side of the book using a hump-shaped depth profile.
        """
        weights = self._hump_weights(
            hump_center=hump_center,
            hump_sigma=hump_sigma,
            tail_decay=tail_decay,
            top_dip=top_dip
        )
        wsum = sum(weights)

        levels = []
        for i, w in enumerate(weights): # Assign a (index, item) pair to the list of elements in weights
            # price ladder
            px = self._ladder_price(best_price, i, side)

            # allocate volume by normalized weight
            qty = total_volume * (w / wsum) # (w / wsum) < 1, thus the sum of total_volume * (w / wsum) is approx. total_volume

            # small multiplicative noise
            eps = self.rng.uniform(-noise, noise) # we want the levels below/above the best bid/ask price to decay in volume
            qty = qty * (1.0 + eps)

            levels.append((px, max(1, int(round(qty))))) # we have levels represented as a list inside a loop, in each loop we append a new level of volume of bid/ask orders into the list at a price px


        return levels # output of levels is something like [(px0, qty0), (px1, qty1), (px2, qty2), ...]

    def order_book_levels(self, execution_qty,
                      noise=0.10, mult_low=5.0, mult_high=10.0,
                      hump_center=3, hump_sigma=1.5, tail_decay=0.20, top_dip=0.40): # generate the levels in bid/ask sides in the lob
        best_bid, best_ask = self.best_bid_ask()
        buy_vol, sell_vol = self.total_side_volumes(execution_qty, mult_low=mult_low, mult_high=mult_high)

        # store targets for future refill steps
        self.target_buy_vol = buy_vol
        self.target_sell_vol = sell_vol

        self.shape_params = dict(
            hump_center=hump_center,
            hump_sigma=hump_sigma,
            tail_decay=tail_decay,
            top_dip=top_dip
        )

        self.bids = self._build_side(best_bid, "bid", buy_vol,
                                    hump_center=hump_center, hump_sigma=hump_sigma,
                                    tail_decay=tail_decay, top_dip=top_dip,
                                    noise=noise)
        self.asks = self._build_side(best_ask, "ask", sell_vol,
                                    hump_center=hump_center, hump_sigma=hump_sigma,
                                    tail_decay=tail_decay, top_dip=top_dip,
                                    noise=noise)

        # guardrail: ensure no duplicate price levels
        self.bids = self._merge_levels(self.bids, "bid")
        self.asks = self._merge_levels(self.asks, "ask")
        return self.bids, self.asks

    # ---------- execution with nonlinear temporary impact ----------
    def execute_market_order(self, qty_signed,
                             impact_eta_ticks=0.0,
                             impact_gamma=1.5,
                             impact_scale=None,
                             impact_use_cum=True): # takes the input buy/sell quantity and executes them on the lob instantly
        if qty_signed == 0:
            return {
                "requested_qty": 0,
                "filled_qty": 0,
                "remaining_qty": 0,
                "vwap": None,
                "fills": [],
                "fills_raw": [],
                "notional": 0.0,
            }

        remaining = abs(qty_signed) # how much of the order has been executed
        fills = [] # a tuple of (price, quantity)
        fills_raw = [] # (book_level_price, effective_price, signed_qty, dP)
        notional = 0.0 # signed (SELL -> negative); a value representing the price filled, i.e. price * quantity filled

        # Choose which side we consume
        if qty_signed < 0: # we define the side of execution based on if quantity if < or > 0, than we execute on either self.bids or self.asks
            book = self.bids
            sign = -1
            round_side = "down" # sells: worse price is lower
        else:
            book = self.asks
            sign = +1
            round_side = "up" # buys: worse price is higher

        # Choose impact scale if not provided
        if impact_scale is None:
            top_qty = book[0][1] if len(book) > 0 else 1.0
            impact_scale = max(1.0, float(top_qty))

        cum_filled_abs = 0.0

        for i, (px, lvl_qty) in enumerate(book): # enumerate(book) returns (i, (price, quantity)), where i is the index for the position of the book; i.e. (0, (price, quantity)) of the bid side is the first level (i.e. best bid) of the bid side
            if remaining <= 0: # we loop through the levels of the book starting from i = 0 i.e. the top level, to i = len(book), if after i = 0, remaining -= take = 0 than that means our order is fully executed
                break

            orig_qty = lvl_qty
            take = min(lvl_qty, remaining) # min() function returns the value that is smaller between lvl_qty and remaining, i.e. take = min(5,10), take = 5, in a lob level, if you order is 1000, and volume is 900 than min(900, 1000) = 900, so you take 900 of that level
            if take <= 0:
                continue

            # if we fully deplete THIS level, it means this price level is removed after the trade
            # (and since we walk from best outward, it's a "best-at-the-time" level)
            # NOTE: we only record the ORIGINAL best level (i == 0) for this order.
            if i == 0 and take == orig_qty:
                if qty_signed < 0:   # SELL consumes bids
                    self.last_exhausted_best_bid = px
                else:                # BUY consumes asks
                    self.last_exhausted_best_ask = px

            # nonlinear impact
            cum_filled_abs += take
            x = cum_filled_abs if impact_use_cum else take

            dP = self.tick_size * float(impact_eta_ticks) * ((float(x) / float(impact_scale)) ** float(impact_gamma))

            # keep effective price on tick grid in the "worse" direction
            px_eff = self.round_to_tick(px + sign * dP, side=round_side)

            fills.append((px_eff, sign * take)) # signed fill qty; price of order being filled is px, amount filled is take
            fills_raw.append((px, px_eff, sign * take, dP))
            notional += px_eff * (sign * take) # signed cashflow/notional; the total money received from buying or selling

            # update level
            lvl_qty -= take # we subtract the amount executed from our order
            remaining -= take # and update the amount needed to be executed
            book[i] = (px, lvl_qty) # we update the lob level i of the bid/ask side with the new lvl_qty

        # remove empty levels
        if qty_signed < 0:
            self.bids = [(p, q) for (p, q) in self.bids if q > 0] # we overrides the list self.bids with a loop that states, add the tuple where only the second element is > 0, i.e. let (p, q) represents the tuple in self.bids, where q is the quantity in self.bids, the loop looks over each tuple in self.bids and chooses to accept only q > 0, thus removing a lob level if q < 0
        else:
            self.asks = [(p, q) for (p, q) in self.asks if q > 0] # same process as self.bids for for self.asks

        filled_qty = sum(q for _, q in fills) # from the list fills, we have a tuple of (px, sign * take), when we say q for _, q we are looking at the second element sign * take, and we sum over all the second elements in the list to get total number of quantity filled
        remaining_qty = qty_signed - filled_qty # calculate the amount of quantity left of the order, it is calculated as, if qty_signed < 0, than sign = -1, therefore in the fills list, the quantity is (-1 * take); the remaining_qty would always be smaller than qty_signed

        filled_abs = abs(filled_qty) # from the list fills, we have a tuple of (px, sign * take), when we say q for _, q we are looking at the second element sign * take, and we sum over all the second elements in the list to get total number of quantity filled
        vwap = (abs(notional) / filled_abs) if filled_abs > 0 else None # value weighted average price, calculates the price of execution * quantity / quantity filled, i.e. (28.07 * 1000 + 28.06 * 1000)/ 2000 = 28.065; (28.07) * 2000/ 2000 = 28.07; here we see that vwap is higher if we don't walk the book

        return {
            "requested_qty": qty_signed,
            "filled_qty": filled_qty,
            "remaining_qty": remaining_qty,
            "vwap": vwap,
            "fills": fills,
            "fills_raw": fills_raw,
            "notional": notional,
            "impact_params": {
                "eta_ticks": impact_eta_ticks,
                "gamma": impact_gamma,
                "scale": impact_scale,
                "use_cum": impact_use_cum,
            }
        }

    # ---------- permanent impact helper ----------
    def shift_book_prices(self, delta_p):
        if delta_p == 0:
            return
        # round in the direction of the shift so it actually moves
        rside = "up" if delta_p > 0 else "down"
        self.bids = [(self.round_to_tick(p + delta_p, side=rside), q) for p, q in self.bids]
        self.asks = [(self.round_to_tick(p + delta_p, side=rside), q) for p, q in self.asks]

        # guardrail: merge duplicates (can happen if multiple levels collapse onto same tick)
        self.bids = self._merge_levels(self.bids, "bid")
        self.asks = self._merge_levels(self.asks, "ask")

    # ---------- refill (no price improvement) ----------
    def _pad_to_n_levels(self, side): # we want to get ride of the level that is empty, and if a order has deplited a level, we want to have it as a "permanent" impact on the lob, thus we generate a new level at the end of the lob
        levels = self.bids if side == "bid" else self.asks
        if not levels:
            return

        # Regrid the book onto a contiguous tick ladder anchored at the current best price.
        # This prevents gaps like 28.09 -> 28.06 when intermediate levels were removed.
        best_px = levels[0][0]
        best_ticks = int(round(best_px / self.tick_size))

        # aggregate any existing quantities by tick (in case duplicates exist)
        qty_by_tick = {}
        for p, q in levels:
            t = int(round(p / self.tick_size))
            qty_by_tick[t] = qty_by_tick.get(t, 0) + q

        new_levels = []
        for i in range(self.n_levels):
            if side == "bid":
                t = best_ticks - i
                px = t * self.tick_size
            else:
                t = best_ticks + i
                px = t * self.tick_size

            new_levels.append((px, qty_by_tick.get(t, 0)))

        if side == "bid":
            self.bids = new_levels
        else:
            self.asks = new_levels

    def _refill_side(self, side, total_volume, rho=0.30, noise=0.05): # we fill all the levels in a random way (including filling the new levels if best bid/ask is depleted)
        levels = self.bids if side == "bid" else self.asks
        weights = self._hump_weights(**self.shape_params)
        wsum = sum(weights)

        new_levels = []
        for i, (px, q) in enumerate(levels):
            target_q = total_volume * (weights[i] / wsum)
            eps = self.rng.uniform(-noise, noise)
            q_new = q + rho * (target_q - q) + eps * target_q
            new_levels.append((px, max(0, int(round(q_new)))))

        if side == "bid":
            self.bids = new_levels
        else:
            self.asks = new_levels

        # guardrail: merge duplicates if any
        if side == "bid":
            self.bids = self._merge_levels(self.bids, "bid")
        else:
            self.asks = self._merge_levels(self.asks, "ask")

    def refill_step(self, rho=0.30, noise=0.05): # we refill the lob with the initial function: total_side_volume
        if self.target_buy_vol is None or self.target_sell_vol is None:
            raise RuntimeError("Call order_book_levels(...) first to set target volumes.")

        self._pad_to_n_levels("bid")
        self._pad_to_n_levels("ask")
        self._refill_side("bid", self.target_buy_vol, rho=rho, noise=noise)
        self._refill_side("ask", self.target_sell_vol, rho=rho, noise=noise)

    # ---------- background flow ----------
    def sample_background_orders(self, lam=2.0, p_buy=0.5,
                                 size_mean=200, size_std=0.8,
                                 size_min=10, size_max=2000): # generate a random list of orders to act as background orders between main orders
        k = int(self.np_rng.poisson(lam)) # poisson process with mean around lam, generate a random number following the poisson distribution
        orders = []
        for _ in range(k): # if poisson dist. gives 4 than take range(4) and loop it
            is_buy = (self.rng.random() < p_buy) # self.rng.random(), we are calling a function .random() in the class ranomd.Random() (check doc: https://docs.python.org/3/library/random.html#random.Random), which generates a random value between 0 and 1, if less than p_buy than is_buy is true else false
            raw = float(self.np_rng.lognormal(mean=math.log(size_mean), sigma=size_std)) # generates many small orders and some big ones folloing a lognormal dist.
            sz = int(max(size_min, min(size_max, round(raw)))) # the number of trades per background trade, we set max(size_min, _) so that if _ is < size_min than we do size_min number of order in this background trade, else we choose min(size_max, round(raw))
            orders.append(+sz if is_buy else -sz) # add sz back into the order list based on if is_buy is true or false
        return orders # a full loop is exp: k = 4 (4 loops), is_buy = true, raw = 500, sz = 500 (10 < sz < 2000) than orders = [+500], next loop, is_buy = false, raw = 200, sz = 200, orders = [+500, -200], ...

    def apply_background_flow(self, lam=2.0, p_buy=0.5, exec_kwargs=None, **size_kwargs): # this function takes the output from sample_background_orders and feeds into the function execute_market_orders while also creating a list reports that shows the background trades
        if exec_kwargs is None:
            exec_kwargs = {}
        orders = self.sample_background_orders(lam=lam, p_buy=p_buy, **size_kwargs)
        reports = [self.execute_market_order(q, **exec_kwargs) for q in orders] # we execute each of the background orders
        return orders, reports

    def mm_restore_exhausted_top(self, p_restore=0.60, vol_frac=0.10, min_qty=1):
        """
        If the last best bid/ask level was fully depleted, the MM may restore it:
          - With probability p_restore
          - With size = vol_frac * (current best qty on that side)
        Then resets the remembered exhausted level so it won't keep restoring every step.
        """

        # ---- restore bid side (if a bid level was exhausted) ----
        if self.last_exhausted_best_bid is not None:
            if len(self.bids) > 0 and self.rng.random() < p_restore:
                restore_px = self.last_exhausted_best_bid

                # reference qty = current best bid qty (the next level that became best)
                ref_qty = self.bids[0][1]
                new_qty = max(min_qty, int(round(vol_frac * ref_qty)))

                # safety: don't cross the spread
                if len(self.asks) == 0 or restore_px < self.asks[0][0]:
                    # remove any existing level at same price (avoid duplicates)
                    self.bids = [(p, q) for (p, q) in self.bids if p != restore_px]

                    # insert and re-sort (descending)
                    self.bids.append((restore_px, new_qty))
                    self.bids.sort(key=lambda x: x[0], reverse=True)

                    # keep book length under control
                    if len(self.bids) > self.n_levels:
                        self.bids = self.bids[: self.n_levels]

            # reset regardless (so it only tries once)
            self.last_exhausted_best_bid = None

        # ---- restore ask side (if an ask level was exhausted) ----
        if self.last_exhausted_best_ask is not None:
            if len(self.asks) > 0 and self.rng.random() < p_restore:
                restore_px = self.last_exhausted_best_ask

                # reference qty = current best ask qty
                ref_qty = self.asks[0][1]
                new_qty = max(min_qty, int(round(vol_frac * ref_qty)))

                # safety: don't cross the spread
                if len(self.bids) == 0 or restore_px > self.bids[0][0]:
                    self.asks = [(p, q) for (p, q) in self.asks if p != restore_px]

                    # insert and re-sort (ascending)
                    self.asks.append((restore_px, new_qty))
                    self.asks.sort(key=lambda x: x[0])

                    # keep book length under control
                    if len(self.asks) > self.n_levels:
                        self.asks = self.asks[: self.n_levels]

            self.last_exhausted_best_ask = None

    # ---------- sim loop (now includes permanent shift) ----------
    def snapshot(self, t):
        return {"t": t, "bids": list(self.bids), "asks": list(self.asks)}

    def step(self, t, trades=None,
             bg_lam=2.0, bg_p_buy=0.5,
             rho=0.30, noise=0.05,
             # permanent shift params
             perm_eta_ticks=0.8, perm_gamma=1.0, perm_scale=7500,
             # exec kwargs for nonlinear temp impact
             main_exec_kwargs=None, bg_exec_kwargs=None,
             order="bg_first"):
        if trades is None: # trades are the main trades we are executing
            trades = []
        if main_exec_kwargs is None:
            main_exec_kwargs = {}
        if bg_exec_kwargs is None:
            bg_exec_kwargs = {}

        delta_p = 0.0
        trade_reports = []
        bg_orders, bg_reports = [], []

        if order == "main_first":
            trade_reports = [self.execute_market_order(q, **main_exec_kwargs) for q in trades]
            bg_orders, bg_reports = self.apply_background_flow(lam=bg_lam, p_buy=bg_p_buy, exec_kwargs=bg_exec_kwargs) # just call and the function apply_background_flow and set it's outputs into the variables bg_orders, bg_reports
        else:
            bg_orders, bg_reports = self.apply_background_flow(lam=bg_lam, p_buy=bg_p_buy, exec_kwargs=bg_exec_kwargs)
            trade_reports = [self.execute_market_order(q, **main_exec_kwargs) for q in trades]

        net_main_filled = sum(r["filled_qty"] for r in trade_reports)  # signed
        if net_main_filled != 0:
            q = abs(net_main_filled)
            sign = +1 if net_main_filled > 0 else -1
            delta_p = sign * self.tick_size * perm_eta_ticks * ((q / perm_scale) ** perm_gamma)
            self.shift_book_prices(delta_p)

        # IMPORTANT: restore after permanent shift so the restored level isn't immediately shifted away
        self.mm_restore_exhausted_top(
            p_restore=self.mm_p_restore,
            vol_frac=self.mm_vol_frac,
            min_qty=self.mm_min_qty
        )

        self.refill_step(rho=rho, noise=noise)

        return {
            "t": t,
            "bg_orders": bg_orders,
            "bg_reports": bg_reports,
            "trade_reports": trade_reports,
            "net_main_filled": net_main_filled,
            "delta_p_perm": delta_p
        }

    def run(self, n_steps, trade_schedule=None,
            bg_lam=2.0, bg_p_buy=0.5,
            rho=0.30, noise=0.05,
            perm_eta_ticks=0.8, perm_gamma=1.0, perm_scale=7500,
            main_exec_kwargs=None, bg_exec_kwargs=None,
            order="bg_first"):
        if trade_schedule is None:
            trade_schedule = {}
        history = [self.snapshot(0)]
        step_logs = {}

        for t in range(1, n_steps + 1):
            val = trade_schedule.get(t, None)
            if val is None:
                trades = []
            elif isinstance(val, (list, tuple)):
                trades = list(val)
            else:
                trades = [val]

            log = self.step(
                t, trades=trades,
                bg_lam=bg_lam, bg_p_buy=bg_p_buy,
                rho=rho, noise=noise,
                perm_eta_ticks=perm_eta_ticks, perm_gamma=perm_gamma, perm_scale=perm_scale,
                main_exec_kwargs=main_exec_kwargs, bg_exec_kwargs=bg_exec_kwargs,
                order=order
            )
            step_logs[t] = log
            history.append(self.snapshot(t))

        return history, step_logs

    # ---------- printing ----------
    def print_book(self, title="LOB Snapshot", max_levels=None):
        if max_levels is None:
            max_levels = self.n_levels

        print("\n" + "=" * 60)
        print(title)
        print("-" * 60)

        best_bid = self.bids[0] if self.bids else (None, None)
        best_ask = self.asks[0] if self.asks else (None, None)
        print(f"Best Ask: {best_ask[0]} x {best_ask[1]} | Best Bid: {best_bid[0]} x {best_bid[1]}")
        print("-" * 60)

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
            print(f"{ap:>7} {aq:>6} | {bp:<7} {bq:<6}")

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
        if "impact_params" in report:
            print(f"Impact params:  {report['impact_params']}")
        print("-" * 60)
        print("Fills (price, signed_qty):")
        for px, q in report["fills"]:
            print(f"  {px:.2f}, {q}")
        print("=" * 60)