from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import LOB_Simulation

def simulate_multi_order_block(parent_orders, ob_params, sim_params):
    """
    Executes multiple parent orders instantly as blocks exactly when they arrive.
    parent_orders format: { arrival_t: qty, ... } e.g., {5: -10000, 20: -5000}
    """
    # 1. Initialize OrderBook
    ob = LOB_Simulation.OrderBook(**ob_params)
    ob.order_book_levels(execution_qty=abs(list(parent_orders.values())[0]), noise=0.1, mult_low=5.0, mult_high=10.0)

    # Block schedule is just the parent orders exactly as they arrive
    trade_schedule = parent_orders
    max_t = max(parent_orders.keys()) + 5 # run a bit past the last order

    # 2. Run simulation
    history, logs = ob.run(n_steps=max_t, trade_schedule=trade_schedule, **sim_params)

    # 3. Calculate Global Slippage
    total_filled = 0
    total_actual_notional = 0.0
    total_arrival_notional = 0.0

    for t, requested_qty in parent_orders.items():
        # Get mid-price right before the trade (snapshot at t-1)
        snap = history[t - 1]
        best_bid = snap["bids"][0][0] if snap["bids"] else ob.reference_price
        best_ask = snap["asks"][0][0] if snap["asks"] else ob.reference_price
        arrival_mid = (best_bid + best_ask) / 2.0

        # Track expected notional based on arrival mid
        total_arrival_notional += arrival_mid * requested_qty

        # Get actual execution data
        if logs[t]["trade_reports"]:
            rep = logs[t]["trade_reports"][0]
            total_filled += rep["filled_qty"]
            total_actual_notional += rep["notional"]

    # Calculate global metrics
    global_vwap = abs(total_actual_notional) / abs(total_filled) if total_filled != 0 else None
    arrival_vwap = abs(total_arrival_notional) / abs(sum(parent_orders.values())) if sum(parent_orders.values()) != 0 else arrival_mid

    net_parent_qty = sum(parent_orders.values())
    slippage = (global_vwap - arrival_vwap) if net_parent_qty > 0 else (arrival_vwap - global_vwap)

    return {
        "strategy": "Multi-Block",
        "net_requested_qty": net_parent_qty,
        "net_filled_qty": total_filled,
        "arrival_vwap": arrival_vwap,
        "global_vwap": global_vwap,
        "slippage": slippage
    }