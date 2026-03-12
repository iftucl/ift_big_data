from __future__ import annotations

from pathlib import Path
import argparse
from datetime import UTC, datetime
import math
import os
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from pymongo import ASCENDING, MongoClient
except Exception:  # pragma: no cover - optional import guard for environments without pymongo
    ASCENDING = 1
    MongoClient = None


PIPELINE_DEFAULTS = {
    "mongo": {
        "dev_uri": "mongodb://localhost:27018",
        "docker_uri": "mongodb://mongo_db:27017",
        "database": "Trades",
        "source_collection": "SuspectTrades",
        "sink_collection": "ExecutionSimulation",
    },
    "simulation": {
        "tick_size": 0.01,
        "seed": 42,
        "n_levels": 10,
        "twap_horizon": 20,
        "deepq_train_episodes": 300,
        "deepq_eval_episodes": 5,
    },
}


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


def _parse_iso_datetime(raw: str) -> datetime:
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalize_trade_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return _parse_iso_datetime(str(value))


def _get_pipeline_runtime_config(env_type: str) -> dict[str, Any]:
    mongo_cfg = PIPELINE_DEFAULTS["mongo"]
    sim_cfg = PIPELINE_DEFAULTS["simulation"]

    default_uri = mongo_cfg["dev_uri"] if env_type == "dev" else mongo_cfg["docker_uri"]
    runtime = {
        "mongo_uri": os.getenv("LOB_MONGO_URI", default_uri),
        "mongo_database": os.getenv("LOB_MONGO_DATABASE", mongo_cfg["database"]),
        "source_collection": os.getenv("LOB_MONGO_SOURCE_COLLECTION", mongo_cfg["source_collection"]),
        "sink_collection": os.getenv("LOB_MONGO_SINK_COLLECTION", mongo_cfg["sink_collection"]),
        "tick_size": float(os.getenv("LOB_TICK_SIZE", sim_cfg["tick_size"])),
        "seed": int(os.getenv("LOB_SIM_SEED", sim_cfg["seed"])),
        "n_levels": int(os.getenv("LOB_N_LEVELS", sim_cfg["n_levels"])),
        "twap_horizon": int(os.getenv("LOB_TWAP_HORIZON", sim_cfg["twap_horizon"])),
        "deepq_train_episodes": int(os.getenv("LOB_DEEPQ_TRAIN_EPISODES", sim_cfg["deepq_train_episodes"])),
        "deepq_eval_episodes": int(os.getenv("LOB_DEEPQ_EVAL_EPISODES", sim_cfg["deepq_eval_episodes"])),
    }
    return runtime


def _build_suspect_query(
    run_start: datetime,
    run_end: datetime,
    trader: str | None,
    symbol: str | None,
    ccy: str | None,
) -> dict[str, Any]:
    query: dict[str, Any] = {
        "IsSuspect": False,
        "DateTime": {"$gte": run_start, "$lt": run_end},
    }
    if trader:
        query["Trader"] = trader
    if symbol:
        query["Symbol"] = symbol
    if ccy:
        query["Ccy"] = ccy
    return query


def _fetch_candidate_trades(collection, query: dict[str, Any]) -> list[dict[str, Any]]:
    projection = {
        "_id": 0,
        "TradeId": 1,
        "DateTime": 1,
        "Trader": 1,
        "Symbol": 1,
        "Quantity": 1,
        "Notional": 1,
        "Ccy": 1,
        "IsSuspect": 1,
        "ValidationLabel": 1,
    }
    cursor = collection.find(query, projection=projection).sort("DateTime", ASCENDING)
    return list(cursor)


def _group_trades_by_key(trades: list[dict[str, Any]]) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for trade in trades:
        key = (str(trade["Trader"]), str(trade["Symbol"]), str(trade["Ccy"]))
        grouped.setdefault(key, []).append(trade)
    return grouped


def _build_schedule_and_lob_meta(records: list[dict[str, Any]], tick_size: float, n_levels: int, seed: int) -> tuple[dict[int, int], dict[str, Any]]:
    sorted_records = sorted(records, key=lambda r: _normalize_trade_datetime(r["DateTime"]))

    timestamp_to_index: dict[datetime, int] = {}
    schedule: dict[int, int] = {}
    next_index = 0

    sum_abs_notional = 0.0
    sum_abs_qty = 0.0

    for rec in sorted_records:
        ts = _normalize_trade_datetime(rec["DateTime"])
        qty = int(rec["Quantity"])
        notion = float(rec["Notional"])
        sum_abs_notional += abs(notion)
        sum_abs_qty += abs(qty)

        idx = timestamp_to_index.get(ts)
        if idx is None:
            idx = next_index
            timestamp_to_index[ts] = idx
            next_index += 1
        schedule[idx] = schedule.get(idx, 0) + qty

    schedule = {k: v for k, v in schedule.items() if v != 0}
    if not schedule:
        return {}, {}

    reference_price = 1.0
    if sum_abs_qty > 0:
        reference_price = max(0.01, sum_abs_notional / sum_abs_qty)

    terminal_t = max(100, len(schedule) + 20)
    lob_params = {
        "reference_price": float(reference_price),
        "tick_size": float(tick_size),
        "n_levels": int(n_levels),
        "seed": int(seed),
        "terminal_t": int(terminal_t),
    }
    return schedule, lob_params


def _build_common_sim_params() -> dict[str, Any]:
    return {
        "bg_lam": 3.0,
        "bg_p_buy": 0.50,
        "rho": 1.0,
        "noise": 0.1,
        "perm_eta_ticks": 0.0,
        "perm_gamma": 1.0,
        "perm_scale": 7500,
        "main_exec_kwargs": {
            "impact_eta_ticks": 0.0,
            "impact_gamma": 1.5,
            "impact_scale": 7500,
            "impact_use_cum": True,
        },
        "bg_exec_kwargs": {
            "impact_eta_ticks": 0.0,
            "impact_gamma": 1.5,
            "impact_scale": 7500,
            "impact_use_cum": True,
        },
        "order": "bg_first",
    }


def _normalize_strategy_result(name: str, raw: dict[str, Any]) -> dict[str, Any]:
    requested = raw.get("net_requested_qty")
    filled = raw.get("net_filled_qty")
    slippage = raw.get("slippage")

    open_qty_abs = None
    if requested is not None and filled is not None:
        open_qty_abs = abs(float(requested) - float(filled))

    total_cost = raw.get("total_cost")
    if total_cost is None:
        if slippage is not None and filled is not None:
            total_cost = abs(float(slippage)) * abs(float(filled))
        else:
            total_cost = math.inf

    return {
        "strategy": name,
        "net_requested_qty": requested,
        "net_filled_qty": filled,
        "arrival_vwap": raw.get("arrival_vwap"),
        "global_vwap": raw.get("global_vwap"),
        "slippage": slippage,
        "implementation_shortfall": raw.get("implementation_shortfall", slippage),
        "open_qty_abs": open_qty_abs,
        "total_cost": float(total_cost) if total_cost is not None else math.inf,
    }


def _summarize_deepq_result(raw: dict[str, Any]) -> dict[str, Any]:
    eval_diag = raw.get("evaluation_diagnostics", {})
    avg_open_qty = None
    episodes = eval_diag.get("episodes", [])
    if episodes:
        vals = [float(ep.get("open_qty_abs", 0)) for ep in episodes]
        avg_open_qty = sum(vals) / len(vals)

    summary = {
        "strategy": raw.get("strategy"),
        "net_requested_qty": raw.get("net_requested_qty"),
        "net_filled_qty": raw.get("net_filled_qty"),
        "arrival_vwap": raw.get("arrival_vwap"),
        "global_vwap": raw.get("global_vwap"),
        "slippage": raw.get("slippage"),
        "implementation_shortfall": raw.get("implementation_shortfall"),
        "total_cost": eval_diag.get("avg_total_cost"),
        "open_qty_abs": avg_open_qty,
        "diagnostics": {
            "avg_total_cost": eval_diag.get("avg_total_cost"),
            "avg_slippage": eval_diag.get("avg_slippage"),
            "avg_net_filled_qty": eval_diag.get("avg_net_filled_qty"),
            "evaluation_episodes": len(episodes),
            "training_episodes": len(raw.get("training_diagnostics", {}).get("episode_costs", [])),
        },
    }
    return summary


def _pick_best_strategy(strategies: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    def score(item: tuple[str, dict[str, Any]]) -> tuple[float, float, float, str]:
        name, payload = item
        total_cost = payload.get("total_cost")
        slippage = payload.get("slippage")
        open_qty_abs = payload.get("open_qty_abs")

        total_cost_score = float(total_cost) if total_cost is not None else math.inf
        slippage_score = abs(float(slippage)) if slippage is not None else math.inf
        open_qty_score = float(open_qty_abs) if open_qty_abs is not None else math.inf
        return (total_cost_score, slippage_score, open_qty_score, name)

    best_name, best_payload = min(strategies.items(), key=score)
    return best_name, best_payload


def _build_execution_document(
    run_id: str,
    source_window: dict[str, str],
    source_collection: str,
    group_key: tuple[str, str, str],
    schedule: dict[int, int],
    lob_params: dict[str, Any],
    sim_params: dict[str, Any],
    strategies: dict[str, dict[str, Any]],
    selected_name: str,
    selected_payload: dict[str, Any],
) -> dict[str, Any]:
    trader, symbol, ccy = group_key
    return {
        "run_id": run_id,
        "source_window": source_window,
        "source_collection": source_collection,
        "group_key": {"trader": trader, "symbol": symbol, "ccy": ccy},
        "input_schedule": {str(k): int(v) for k, v in sorted(schedule.items())},
        "lob_params": lob_params,
        "sim_params": sim_params,
        "strategies": strategies,
        "selected_strategy": selected_name,
        "selection_metric": "total_cost",
        "selection_tiebreakers": ["abs(slippage)", "open_qty_abs"],
        "selected_strategy_metrics": selected_payload,
        "created_at": datetime.now(UTC),
    }


def _ensure_sink_index(collection):
    collection.create_index(
        [
            ("run_id", ASCENDING),
            ("group_key.trader", ASCENDING),
            ("group_key.symbol", ASCENDING),
            ("group_key.ccy", ASCENDING),
        ],
        unique=True,
        name="uq_run_group_key",
    )


def _run_pipeline(args: argparse.Namespace) -> int:
    from Execution_Methods import Block_Trade, TWAP, multi_order_deep_qlearning

    if MongoClient is None:
        raise RuntimeError("pymongo is required for pipeline mode. Install pymongo to continue.")

    if not args.run_start or not args.run_end:
        raise ValueError("--run_start and --run_end are required in pipeline mode")

    run_start = _parse_iso_datetime(args.run_start)
    run_end = _parse_iso_datetime(args.run_end)
    if run_end <= run_start:
        raise ValueError("--run_end must be strictly after --run_start")

    runtime_cfg = _get_pipeline_runtime_config(args.env_type)
    if args.tick_size is not None:
        runtime_cfg["tick_size"] = float(args.tick_size)

    run_id = args.run_id or datetime.now(UTC).strftime("run_%Y%m%dT%H%M%SZ")

    mongo_client = MongoClient(runtime_cfg["mongo_uri"])
    db = mongo_client[runtime_cfg["mongo_database"]]
    source_collection = db[runtime_cfg["source_collection"]]
    sink_collection = db[runtime_cfg["sink_collection"]]

    _ensure_sink_index(sink_collection)

    query = _build_suspect_query(
        run_start=run_start,
        run_end=run_end,
        trader=args.trader,
        symbol=args.symbol,
        ccy=args.ccy,
    )

    input_trades = _fetch_candidate_trades(source_collection, query)
    if not input_trades:
        print("No eligible trades found for pipeline window/filter. Nothing written.")
        return 0

    grouped = _group_trades_by_key(input_trades)
    sim_params = _build_common_sim_params()

    upserted = 0
    skipped = 0

    for group_key, records in grouped.items():
        schedule, lob_meta = _build_schedule_and_lob_meta(
            records,
            tick_size=runtime_cfg["tick_size"],
            n_levels=runtime_cfg["n_levels"],
            seed=runtime_cfg["seed"],
        )
        if not schedule:
            skipped += 1
            continue

        ob_params = {
            "reference_price": lob_meta["reference_price"],
            "tick_size": lob_meta["tick_size"],
            "n_levels": lob_meta["n_levels"],
            "seed": lob_meta["seed"],
        }
        terminal_t = int(lob_meta["terminal_t"])

        block_raw = Block_Trade.simulate_multi_order_block(schedule, ob_params, sim_params)
        block_raw["implementation_shortfall"] = block_raw.get("slippage")

        twap_horizon = max(1, min(int(runtime_cfg["twap_horizon"]), terminal_t))
        twap_raw = TWAP.simulate_multi_order_twap(schedule, twap_horizon, ob_params, sim_params)
        twap_raw["implementation_shortfall"] = twap_raw.get("slippage")

        rl_env_cfg = multi_order_deep_qlearning.get_default_multi_order_env_params()
        rl_env_cfg["ob_params"].update(ob_params)
        rl_env_cfg["terminal_t"] = terminal_t
        rl_env_cfg["step_params"].update(sim_params)
        rl_env_cfg["init_params"]["execution_qty"] = max(abs(v) for v in schedule.values())

        rl_train_cfg = multi_order_deep_qlearning.get_default_multi_order_train_params()
        rl_eval_cfg = multi_order_deep_qlearning.get_default_multi_order_eval_params()
        rl_train_cfg["num_episodes"] = int(runtime_cfg["deepq_train_episodes"])
        rl_eval_cfg["n_episodes"] = int(runtime_cfg["deepq_eval_episodes"])

        deepq_raw = multi_order_deep_qlearning.train_multi_order_deep_q_execution(
            trade_schedule=schedule,
            env_params=rl_env_cfg,
            train_params=rl_train_cfg,
            eval_params=rl_eval_cfg,
            device=None,
            verbose=False,
        )

        strategies = {
            "block": _normalize_strategy_result("block", block_raw),
            "twap": _normalize_strategy_result("twap", twap_raw),
            "deep_q": _normalize_strategy_result("deep_q", _summarize_deepq_result(deepq_raw)),
        }

        selected_name, selected_payload = _pick_best_strategy(strategies)

        doc = _build_execution_document(
            run_id=run_id,
            source_window={
                "run_start": run_start.isoformat(),
                "run_end": run_end.isoformat(),
            },
            source_collection=runtime_cfg["source_collection"],
            group_key=group_key,
            schedule=schedule,
            lob_params=lob_meta,
            sim_params={
                "twap_horizon": twap_horizon,
                "deepq_train_episodes": rl_train_cfg["num_episodes"],
                "deepq_eval_episodes": rl_eval_cfg["n_episodes"],
                "market_step_params": sim_params,
            },
            strategies=strategies,
            selected_name=selected_name,
            selected_payload=selected_payload,
        )

        filter_key = {
            "run_id": run_id,
            "group_key.trader": group_key[0],
            "group_key.symbol": group_key[1],
            "group_key.ccy": group_key[2],
        }
        sink_collection.update_one(filter_key, {"$set": doc}, upsert=True)
        upserted += 1

    print(
        f"Pipeline simulation complete | run_id={run_id} | groups_total={len(grouped)} "
        f"| upserted={upserted} | skipped={skipped}"
    )
    return 0


def _run_demo() -> int:
    from Execution_Methods import Block_Trade, TWAP, multi_order_deep_qlearning

    seed = 42
    trade_schedule = {
        5: -10000,
        20: -5000,
        35: 4000,
    }
    horizon = 100

    ob_params = dict(reference_price=28.13, tick_size=0.01, n_levels=10, seed=seed)
    sim_params = dict(
        bg_lam=3.0,
        bg_p_buy=0.50,
        rho=1.0,
        noise=0.1,
        perm_eta_ticks=0.0,
        perm_gamma=1.0,
        perm_scale=7500,
        main_exec_kwargs=dict(impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=7500, impact_use_cum=True),
        bg_exec_kwargs=dict(impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=7500, impact_use_cum=True),
        order="bg_first",
    )

    print("\n" + "=" * 80)
    print("MULTI-ORDER EXECUTION COMPARISON: BLOCK vs TWAP vs DEEP-Q")
    print("=" * 80)
    print(f"Seed: {seed}")
    print(f"Trade Schedule: {trade_schedule}")
    print(f"Horizon / Terminal Time: {horizon}")
    print("-" * 80)

    block_res = Block_Trade.simulate_multi_order_block(trade_schedule, ob_params, sim_params)
    block_res["implementation_shortfall"] = block_res["slippage"]

    twap_res = TWAP.simulate_multi_order_twap(trade_schedule, horizon, ob_params, sim_params)
    twap_res["implementation_shortfall"] = twap_res["slippage"]

    rl_env_cfg = multi_order_deep_qlearning.get_default_multi_order_env_params()
    rl_env_cfg["ob_params"].update(ob_params)
    rl_env_cfg["terminal_t"] = horizon
    rl_env_cfg["step_params"].update(sim_params)
    rl_env_cfg["init_params"]["execution_qty"] = max(abs(v) for v in trade_schedule.values())

    rl_train_cfg = multi_order_deep_qlearning.get_default_multi_order_train_params()
    rl_eval_cfg = multi_order_deep_qlearning.get_default_multi_order_eval_params()
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

    for strategy_res in [block_res, twap_res, deep_q_res]:
        _print_strategy_summary(strategy_res, ob_params["tick_size"])

    rows = [
        _build_comparison_row(block_res, ob_params["tick_size"]),
        _build_comparison_row(twap_res, ob_params["tick_size"]),
        _build_comparison_row(deep_q_res, ob_params["tick_size"]),
    ]
    _print_comparison_table(rows)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="LOB simulation runner (demo + pipeline modes)")
    parser.add_argument("--mode", choices=["demo", "pipeline"], default="demo", help="Execution mode")
    parser.add_argument("--env_type", choices=["dev", "docker"], default="dev", help="Runtime environment")

    parser.add_argument("--run_id", required=False, help="Pipeline run id (defaults to timestamp)")
    parser.add_argument("--run_start", required=False, help="Pipeline window start (ISO-8601)")
    parser.add_argument("--run_end", required=False, help="Pipeline window end (ISO-8601)")
    parser.add_argument("--trader", required=False, help="Optional trader filter")
    parser.add_argument("--symbol", required=False, help="Optional symbol filter")
    parser.add_argument("--ccy", required=False, help="Optional ccy filter")
    parser.add_argument("--tick_size", required=False, type=float, help="Optional tick-size override")
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.mode == "demo":
        return _run_demo()
    return _run_pipeline(args)


if __name__ == "__main__":
    raise SystemExit(main())
