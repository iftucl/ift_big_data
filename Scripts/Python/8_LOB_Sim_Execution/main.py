from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Execution_Methods import Block_Trade, TWAP, multi_order_deep_qlearning


def _fmt_num(value, decimals=4):
    if value is None:
        return "None"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{decimals}f}"


def _build_comparison_row(res, tick_size):
    requested = res.get("net_requested_qty")
    filled = res.get("net_filled_qty")
    arrival_vwap = res.get("arrival_vwap")
    execution_vwap = res.get("global_vwap")
    slippage = res.get("slippage")
    implementation_shortfall = res.get("implementation_shortfall", slippage)

    fill_ratio = None
    if requested not in (None, 0) and filled is not None:
        fill_ratio = abs(filled) / abs(requested)

    slippage_ticks = None
    if slippage is not None and tick_size not in (None, 0):
        slippage_ticks = slippage / tick_size

    shortfall_notional = None
    if implementation_shortfall is not None and filled is not None:
        shortfall_notional = implementation_shortfall * abs(filled)

    return {
        "strategy": res.get("strategy"),
        "net_requested_qty": requested,
        "net_filled_qty": filled,
        "fill_ratio": fill_ratio,
        "arrival_vwap": arrival_vwap,
        "execution_vwap": execution_vwap,
        "slippage": slippage,
        "slippage_ticks": slippage_ticks,
        "implementation_shortfall": implementation_shortfall,
        "shortfall_notional_est": shortfall_notional,
    }


def _print_strategy_summary(res, tick_size):
    row = _build_comparison_row(res, tick_size)
    print(f"Strategy:                   {row['strategy']}")
    print(f"Net Requested Qty:          {row['net_requested_qty']}")
    print(f"Net Filled Qty:             {_fmt_num(row['net_filled_qty'], 2)}")
    print(f"Fill Ratio:                 {_fmt_num(row['fill_ratio'], 4)}")
    print(f"Arrival VWAP:               {_fmt_num(row['arrival_vwap'], 4)}")
    print(f"Execution VWAP (Avg Price): {_fmt_num(row['execution_vwap'], 4)}")
    print(f"Slippage (Price):           {_fmt_num(row['slippage'], 4)}")
    print(f"Slippage (Ticks):           {_fmt_num(row['slippage_ticks'], 2)}")
    print(f"Implementation Shortfall:   {_fmt_num(row['implementation_shortfall'], 4)}")
    print(f"Shortfall Notional (Est):   {_fmt_num(row['shortfall_notional_est'], 2)}")
    print("-" * 80)


def _print_comparison_table(rows):
    headers = [
        "Strategy",
        "ReqQty",
        "FilledQty",
        "FillRatio",
        "ArrVWAP",
        "ExecVWAP",
        "SlipPx",
        "SlipTicks",
        "ISPx",
        "ISNotional",
    ]
    print("\n" + "=" * 140)
    print("COMPARISON TABLE")
    print("=" * 140)
    print(
        f"{headers[0]:<38}"
        f"{headers[1]:>10}"
        f"{headers[2]:>12}"
        f"{headers[3]:>11}"
        f"{headers[4]:>11}"
        f"{headers[5]:>11}"
        f"{headers[6]:>10}"
        f"{headers[7]:>11}"
        f"{headers[8]:>9}"
        f"{headers[9]:>17}"
    )
    print("-" * 140)
    for row in rows:
        print(
            f"{row['strategy']:<38}"
            f"{_fmt_num(row['net_requested_qty'], 0):>10}"
            f"{_fmt_num(row['net_filled_qty'], 2):>12}"
            f"{_fmt_num(row['fill_ratio'], 4):>11}"
            f"{_fmt_num(row['arrival_vwap'], 4):>11}"
            f"{_fmt_num(row['execution_vwap'], 4):>11}"
            f"{_fmt_num(row['slippage'], 4):>10}"
            f"{_fmt_num(row['slippage_ticks'], 2):>11}"
            f"{_fmt_num(row['implementation_shortfall'], 4):>9}"
            f"{_fmt_num(row['shortfall_notional_est'], 2):>17}"
        )
    print("=" * 140)

if __name__ == "__main__":
    # Single source of truth for comparison inputs
    seed = 42
    trade_schedule = {
        5: -10000,
        20: -5000,
        35: 4000,
    }
    horizon = 100

    ob_params = dict(reference_price=28.13, tick_size=0.01, n_levels=10, seed=seed)
    sim_params = dict(
        bg_lam=3.0, bg_p_buy=0.50, rho=1.0, noise=0.1,
        perm_eta_ticks=0.0, perm_gamma=1.0, perm_scale=7500,
        main_exec_kwargs=dict(impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=7500, impact_use_cum=True),
        bg_exec_kwargs=dict(impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=7500, impact_use_cum=True),
        order="bg_first"
    )

    print("\n" + "=" * 80)
    print("MULTI-ORDER EXECUTION COMPARISON: BLOCK vs TWAP vs DEEP-Q")
    print("=" * 80)
    print(f"Seed: {seed}")
    print(f"Trade Schedule: {trade_schedule}")
    print(f"Horizon / Terminal Time: {horizon}")
    print("-" * 80)

    # 1) Block
    block_res = Block_Trade.simulate_multi_order_block(trade_schedule, ob_params, sim_params)
    block_res["implementation_shortfall"] = block_res["slippage"]

    # 2) TWAP
    twap_res = TWAP.simulate_multi_order_twap(trade_schedule, horizon, ob_params, sim_params)
    twap_res["implementation_shortfall"] = twap_res["slippage"]

    # 3) Multi-order Deep-Q (same schedule + seed)
    rl_env_cfg = multi_order_deep_qlearning.get_default_multi_order_env_params()
    rl_env_cfg["ob_params"].update(ob_params)
    rl_env_cfg["terminal_t"] = horizon
    rl_env_cfg["step_params"].update(
        {
            "bg_lam": sim_params["bg_lam"],
            "bg_p_buy": sim_params["bg_p_buy"],
            "rho": sim_params["rho"],
            "noise": sim_params["noise"],
            "perm_eta_ticks": sim_params["perm_eta_ticks"],
            "perm_gamma": sim_params["perm_gamma"],
            "perm_scale": sim_params["perm_scale"],
            "main_exec_kwargs": sim_params["main_exec_kwargs"],
            "bg_exec_kwargs": sim_params["bg_exec_kwargs"],
            "order": sim_params["order"],
        }
    )
    rl_env_cfg["init_params"]["execution_qty"] = max(abs(v) for v in trade_schedule.values())

    rl_train_cfg = multi_order_deep_qlearning.get_default_multi_order_train_params()
    rl_eval_cfg = multi_order_deep_qlearning.get_default_multi_order_eval_params()
    # Keep training finite for local comparatives; tune up for production-grade runs.
    rl_train_cfg["num_episodes"] = 300
    rl_eval_cfg["n_episodes"] = 5

    deep_q_res = multi_order_deep_qlearning.train_multi_order_deep_q_execution(
        trade_schedule=trade_schedule,
        env_params=rl_env_cfg,
        train_params=rl_train_cfg,
        eval_params=rl_eval_cfg,
        device=None,
        verbose=False,
    )

    # Detailed per-strategy summaries
    for strategy_res in [block_res, twap_res, deep_q_res]:
        _print_strategy_summary(strategy_res, ob_params["tick_size"])

    # One-line comparison table
    rows = [
        _build_comparison_row(block_res, ob_params["tick_size"]),
        _build_comparison_row(twap_res, ob_params["tick_size"]),
        _build_comparison_row(deep_q_res, ob_params["tick_size"]),
    ]
    _print_comparison_table(rows)
