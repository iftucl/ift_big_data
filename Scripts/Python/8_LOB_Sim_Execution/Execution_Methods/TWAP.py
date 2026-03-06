from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import LOB_Simulation
def simulate_multi_order_twap(parent_orders, time_horizon, ob_params, sim_params):
    """
    Slices multiple parent orders independently from their arrival time,
    aggregating any overlapping slices into a single net market order per step.
    """
    # 1. Build the overlapping TWAP schedule (No peeking ahead!)
    trade_schedule = {}
    max_t = 0

    for arrival_t, qty in parent_orders.items():
        sign = 1 if qty > 0 else -1
        abs_qty = abs(qty)
        slice_size = abs_qty // time_horizon
        remainder = abs_qty % time_horizon

        for i in range(time_horizon):
            t = arrival_t + i
            chunk = slice_size
            if i == time_horizon - 1:
                chunk += remainder # sweep odd lots on the last slice

            # Net overlapping orders together
            trade_schedule[t] = trade_schedule.get(t, 0) + (chunk * sign)
            max_t = max(max_t, t)

    # 2. Initialize and Run
    ob = LOB_Simulation.OrderBook(**ob_params)
    ob.order_book_levels(execution_qty=abs(list(parent_orders.values())[0]), noise=0.1, mult_low=5.0, mult_high=10.0)

    history, logs = ob.run(n_steps=max_t, trade_schedule=trade_schedule, **sim_params)

    # 3. Calculate Global Slippage
    total_filled = 0
    total_actual_notional = 0.0
    total_arrival_notional = 0.0

    # Calculate what the ideal arrival notional was for each parent order
    for t, requested_qty in parent_orders.items():
        snap = history[t - 1] # Snapshot just before this specific order arrived
        best_bid = snap["bids"][0][0] if snap["bids"] else ob.reference_price
        best_ask = snap["asks"][0][0] if snap["asks"] else ob.reference_price
        arrival_mid = (best_bid + best_ask) / 2.0

        total_arrival_notional += arrival_mid * requested_qty

    # Calculate actual executed notional across all TWAP steps
    for t in range(1, max_t + 1):
        if t in logs and logs[t]["trade_reports"]:
            rep = logs[t]["trade_reports"][0]
            total_filled += rep["filled_qty"]
            total_actual_notional += rep["notional"]

    # Calculate global metrics
    global_vwap = abs(total_actual_notional) / abs(total_filled) if total_filled != 0 else None
    arrival_vwap = abs(total_arrival_notional) / abs(sum(parent_orders.values())) if sum(parent_orders.values()) != 0 else arrival_mid

    net_parent_qty = sum(parent_orders.values())
    slippage = (global_vwap - arrival_vwap) if net_parent_qty > 0 else (arrival_vwap - global_vwap)

    return {
        "strategy": f"Multi-TWAP (Horizon={time_horizon})",
        "net_requested_qty": net_parent_qty,
        "net_filled_qty": total_filled,
        "arrival_vwap": arrival_vwap,
        "global_vwap": global_vwap,
        "slippage": slippage
    }