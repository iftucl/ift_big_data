import math
import random
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
import torch.optim as optim

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import LOB_Simulation
try:
    from .rl_lob_execution import DQN, ReplayBuffer
except ImportError:
    from rl_lob_execution import DQN, ReplayBuffer

def normalize_trade_schedule(trade_schedule: dict[int, Any]) -> dict[int, list[int]]:
    """
    Convert schedule values to a canonical dict[int, list[int]].
    Input examples:
      {1: 1000, 5: 5000, 10: -2000}
      {1: [1000, 2000], 5: -3000}
    """
    normalized = {}
    for t_raw, vals in trade_schedule.items():
        t = int(t_raw)
        if isinstance(vals, (list, tuple)):
            qtys = [int(v) for v in vals if int(v) != 0]
        else:
            q = int(vals)
            qtys = [q] if q != 0 else []
        if qtys:
            normalized[t] = qtys
    return normalized


def get_default_trade_schedule() -> dict[int, int]:
    return {1: 1000, 5: 5000, 10: -2000}


@dataclass
class ParentOrder:
    parent_id: str
    arrival_t: int
    side: int
    qty_total: int
    qty_remaining: int
    arrival_mid: float
    requested_benchmark_notional: float
    qty_filled: int = 0
    exec_notional: float = 0.0
    benchmark_notional_filled: float = 0.0
    realized_shortfall: float = 0.0
    terminal_penalty: float = 0.0

    def is_active(self) -> bool:
        return self.qty_remaining != 0


class ManagerRL:
    """
    Coordinates parent-order bookkeeping and side-level routing.
    """

    def __init__(self, terminal_t: int, enforce_min_clip_to_finish: bool = True):
        self.terminal_t = int(terminal_t)
        self.enforce_min_clip_to_finish = bool(enforce_min_clip_to_finish)
        self.allow_crossing = False
        self.reset()

    def reset(self):
        self._counter = 0
        self.orders_by_side = {+1: [], -1: []}
        self.orders: dict[str, ParentOrder] = {}
        self.total_requested_qty = 0
        self.total_requested_abs = 0
        self.total_realized_shortfall = 0.0
        self.total_terminal_penalty = 0.0

    def register_parent_order(self, arrival_t: int, qty_signed: int, arrival_mid: float) -> str | None:
        qty = int(qty_signed)
        if qty == 0:
            return None

        side = +1 if qty > 0 else -1
        self._counter += 1
        parent_id = f"P{self._counter:05d}"
        order = ParentOrder(
            parent_id=parent_id,
            arrival_t=int(arrival_t),
            side=side,
            qty_total=qty,
            qty_remaining=qty,
            arrival_mid=float(arrival_mid),
            requested_benchmark_notional=float(arrival_mid * qty),
        )
        self.orders[parent_id] = order
        self.orders_by_side[side].append(order)
        self.total_requested_qty += qty
        self.total_requested_abs += abs(qty)
        return parent_id

    def ingest_arrivals(self, t: int, schedule: dict[int, list[int]], arrival_mid: float):
        for qty in schedule.get(int(t), []):
            self.register_parent_order(arrival_t=t, qty_signed=int(qty), arrival_mid=arrival_mid)

    def active_orders(self, side: int | None = None) -> list[ParentOrder]:
        if side in (+1, -1):
            return [o for o in self.orders_by_side[side] if o.is_active()]
        active = []
        for s in (+1, -1):
            active.extend([o for o in self.orders_by_side[s] if o.is_active()])
        return active

    def has_active_orders(self) -> bool:
        return len(self.active_orders()) > 0

    def active_count(self, side: int) -> int:
        return len(self.active_orders(side=side))

    def remaining_abs_by_side(self, side: int) -> int:
        return int(sum(abs(o.qty_remaining) for o in self.active_orders(side=side)))

    def remaining_signed_by_side(self, side: int) -> int:
        return int(sum(o.qty_remaining for o in self.active_orders(side=side)))

    def _oldest_active_arrival(self, side: int) -> int:
        actives = self.active_orders(side=side)
        if not actives:
            return 10**9
        return min(o.arrival_t for o in actives)

    def select_side(self, t: int) -> int:
        """
        Return +1 (buy), -1 (sell), or 0 (no active order).
        No crossing: executes one side per step.
        """
        buy_rem = self.remaining_abs_by_side(+1)
        sell_rem = self.remaining_abs_by_side(-1)

        if buy_rem == 0 and sell_rem == 0:
            return 0
        if buy_rem == 0:
            return -1
        if sell_rem == 0:
            return +1

        steps_left = max(1, self.terminal_t - int(t) + 1)
        buy_urgency = buy_rem / steps_left
        sell_urgency = sell_rem / steps_left

        if buy_urgency > sell_urgency:
            return +1
        if sell_urgency > buy_urgency:
            return -1

        # Tie-break on oldest active parent
        return +1 if self._oldest_active_arrival(+1) <= self._oldest_active_arrival(-1) else -1

    def child_order_from_fraction(self, side: int, fraction: float, t: int) -> int:
        if side not in (+1, -1):
            return 0

        remaining_abs = self.remaining_abs_by_side(side)
        if remaining_abs <= 0:
            return 0

        fraction = float(max(0.0, min(1.0, fraction)))
        qty_abs = int(round(fraction * remaining_abs))

        if self.enforce_min_clip_to_finish:
            steps_left = max(1, self.terminal_t - int(t) + 1)
            min_clip = int(math.ceil(remaining_abs / steps_left))
            qty_abs = max(qty_abs, min_clip)

        qty_abs = min(qty_abs, remaining_abs)
        return int(side * qty_abs)

    def attribute_fill_fifo(self, filled_qty_signed: int, fill_notional_signed: float) -> float:
        """
        Attribute one aggregated child fill back to parent orders (FIFO by arrival).
        Returns incremental realized shortfall cost (positive = worse execution).
        """
        filled = int(filled_qty_signed)
        if filled == 0:
            return 0.0

        side = +1 if filled > 0 else -1
        fill_abs = abs(filled)
        vwap = abs(float(fill_notional_signed)) / fill_abs
        to_allocate = fill_abs
        step_shortfall = 0.0

        for order in self.orders_by_side[side]:
            if not order.is_active():
                continue
            available = abs(order.qty_remaining)
            if available <= 0:
                continue

            take_abs = min(available, to_allocate)
            signed_take = side * take_abs

            order.qty_remaining -= signed_take
            order.qty_filled += signed_take

            exec_notional = signed_take * vwap
            bench_notional = signed_take * order.arrival_mid
            order.exec_notional += exec_notional
            order.benchmark_notional_filled += bench_notional

            if side > 0:
                local_shortfall = (vwap - order.arrival_mid) * take_abs
            else:
                local_shortfall = (order.arrival_mid - vwap) * take_abs
            order.realized_shortfall += local_shortfall
            step_shortfall += local_shortfall

            to_allocate -= take_abs
            if to_allocate == 0:
                break

        self.total_realized_shortfall += step_shortfall
        return float(step_shortfall)

    def apply_terminal_penalty(self, current_mid: float) -> float:
        penalty = 0.0
        mid = float(current_mid)
        for order in self.active_orders():
            rem_abs = abs(order.qty_remaining)
            if rem_abs == 0:
                continue
            if order.side > 0:
                local_penalty = (mid - order.arrival_mid) * rem_abs
            else:
                local_penalty = (order.arrival_mid - mid) * rem_abs
            order.terminal_penalty += local_penalty
            penalty += local_penalty

        self.total_terminal_penalty += penalty
        return float(penalty)

    def build_summary(self) -> dict[str, Any]:
        per_parent = []
        total_requested = 0
        total_filled = 0
        total_req_bench_notional = 0.0
        total_exec_notional = 0.0
        total_open_abs = 0

        for order in self.orders.values():
            total_requested += order.qty_total
            total_filled += order.qty_filled
            total_req_bench_notional += order.requested_benchmark_notional
            total_exec_notional += order.exec_notional
            total_open_abs += abs(order.qty_remaining)

            parent_slippage = None
            if order.qty_filled != 0:
                parent_arrival = abs(order.requested_benchmark_notional) / abs(order.qty_total)
                parent_exec = abs(order.exec_notional) / abs(order.qty_filled)
                if order.qty_total > 0:
                    parent_slippage = parent_exec - parent_arrival
                else:
                    parent_slippage = parent_arrival - parent_exec

            per_parent.append(
                {
                    "parent_id": order.parent_id,
                    "arrival_t": order.arrival_t,
                    "side": "BUY" if order.side > 0 else "SELL",
                    "qty_total": order.qty_total,
                    "qty_filled": order.qty_filled,
                    "qty_remaining": order.qty_remaining,
                    "arrival_mid": order.arrival_mid,
                    "realized_shortfall": order.realized_shortfall,
                    "terminal_penalty": order.terminal_penalty,
                    "total_cost": order.realized_shortfall + order.terminal_penalty,
                    "slippage": parent_slippage,
                }
            )

        arrival_vwap = None
        if total_requested != 0:
            arrival_vwap = abs(total_req_bench_notional) / abs(total_requested)

        global_vwap = None
        if total_filled != 0:
            global_vwap = abs(total_exec_notional) / abs(total_filled)

        slippage = None
        if arrival_vwap is not None and global_vwap is not None and total_requested != 0:
            if total_requested > 0:
                slippage = global_vwap - arrival_vwap
            else:
                slippage = arrival_vwap - global_vwap

        summary = {
            "no_crossing": True,
            "net_requested_qty": int(total_requested),
            "net_filled_qty": int(total_filled),
            "open_qty_abs": int(total_open_abs),
            "arrival_vwap": arrival_vwap,
            "global_vwap": global_vwap,
            "slippage": slippage,
            "realized_shortfall_cost": float(self.total_realized_shortfall),
            "terminal_penalty_cost": float(self.total_terminal_penalty),
            "total_cost": float(self.total_realized_shortfall + self.total_terminal_penalty),
            "per_parent": per_parent,
        }
        return summary


class MultiParentExecutionEnv:
    """
    Multi-parent RL environment with:
    - global terminal time
    - no crossing between buy/sell flows
    - FIFO attribution from child fills to active parent orders
    """

    def __init__(
        self,
        trade_schedule: dict[int, Any],
        ob_params: dict[str, Any],
        init_params: dict[str, Any],
        step_params: dict[str, Any],
        terminal_t: int = 50,
        action_fracs: tuple[float, ...] = (0.0, 0.1, 0.25, 0.5, 1.0),
        enforce_min_clip_to_finish: bool = True,
        seed_jitter_max: int = 10000,
    ):
        self.trade_schedule = normalize_trade_schedule(trade_schedule)
        self.ob_params = dict(ob_params)
        self.init_params = dict(init_params)
        self.step_params = dict(step_params)
        self.terminal_t = int(terminal_t)
        self.action_fracs = list(action_fracs)
        self.enforce_min_clip_to_finish = bool(enforce_min_clip_to_finish)
        self.seed_jitter_max = int(seed_jitter_max)

        self.schedule_times = sorted(self.trade_schedule.keys())
        self.total_abs_requested = sum(abs(q) for vals in self.trade_schedule.values() for q in vals)
        self.max_abs_order = max([abs(q) for vals in self.trade_schedule.values() for q in vals] + [1])

        self.manager = ManagerRL(
            terminal_t=self.terminal_t,
            enforce_min_clip_to_finish=self.enforce_min_clip_to_finish,
        )
        self.ob = None
        self.current_t = None
        self.current_selected_side = 0

    def _has_future_arrivals(self, t: int) -> bool:
        t_int = int(t)
        return any(ts >= t_int for ts in self.schedule_times)

    def _new_order_book(self) -> LOB_Simulation:
        params = dict(self.ob_params)
        seed = params.get("seed", None)
        if seed is not None and self.seed_jitter_max > 0:
            params["seed"] = int(seed + np.random.randint(0, self.seed_jitter_max))
        return LOB_Simulation.OrderBook(**params)

    def _mid_price(self) -> float:
        best_bid = self.ob.bids[0][0] if self.ob.bids else self.ob.reference_price
        best_ask = self.ob.asks[0][0] if self.ob.asks else self.ob.reference_price
        return float((best_bid + best_ask) / 2.0)

    def _build_state(self, selected_side: int) -> np.ndarray:
        denom = max(1, self.total_abs_requested)
        steps_left = max(0, self.terminal_t - int(self.current_t) + 1)

        buy_remaining = self.manager.remaining_abs_by_side(+1)
        sell_remaining = self.manager.remaining_abs_by_side(-1)
        selected_remaining = self.manager.remaining_abs_by_side(selected_side) if selected_side in (+1, -1) else 0

        bids = self.ob.bids
        asks = self.ob.asks
        best_bid = bids[0][0] if bids else self.ob.reference_price
        best_ask = asks[0][0] if asks else self.ob.reference_price
        best_bid_sz = bids[0][1] if bids else 0
        best_ask_sz = asks[0][1] if asks else 0

        bid_rel = (best_bid - self.ob.reference_price) / self.ob.tick_size
        ask_rel = (best_ask - self.ob.reference_price) / self.ob.tick_size

        n_depth = 3
        bid_prices, bid_sizes, ask_prices, ask_sizes = [], [], [], []
        for i in range(n_depth):
            if i < len(bids):
                p, q = bids[i]
                bid_prices.append((p - self.ob.reference_price) / self.ob.tick_size)
                bid_sizes.append(np.log1p(q) / 10.0)
            else:
                bid_prices.append(0.0)
                bid_sizes.append(0.0)
            if i < len(asks):
                p, q = asks[i]
                ask_prices.append((p - self.ob.reference_price) / self.ob.tick_size)
                ask_sizes.append(np.log1p(q) / 10.0)
            else:
                ask_prices.append(0.0)
                ask_sizes.append(0.0)

        state = np.array(
            [
                float(selected_side),
                steps_left / max(1, self.terminal_t),
                buy_remaining / denom,
                sell_remaining / denom,
                selected_remaining / denom,
                self.manager.active_count(+1) / 10.0,
                self.manager.active_count(-1) / 10.0,
                bid_rel,
                ask_rel,
                np.log1p(best_bid_sz) / 10.0,
                np.log1p(best_ask_sz) / 10.0,
                *bid_prices,
                *bid_sizes,
                *ask_prices,
                *ask_sizes,
            ],
            dtype=np.float32,
        )
        return state

    def reset(self) -> np.ndarray:
        self.manager.reset()
        self.ob = self._new_order_book()

        init_qty = max(int(self.init_params.get("execution_qty", 10000)), self.max_abs_order)
        self.ob.order_book_levels(
            execution_qty=init_qty,
            noise=float(self.init_params.get("noise", 0.10)),
            mult_low=float(self.init_params.get("mult_low", 5.0)),
            mult_high=float(self.init_params.get("mult_high", 10.0)),
            hump_center=float(self.init_params.get("hump_center", 3)),
            hump_sigma=float(self.init_params.get("hump_sigma", 1.5)),
            tail_decay=float(self.init_params.get("tail_decay", 0.20)),
            top_dip=float(self.init_params.get("top_dip", 0.40)),
        )

        # t=0 arrivals can be active before first decision
        self.manager.ingest_arrivals(0, self.trade_schedule, self._mid_price())

        self.current_t = 1
        self.manager.ingest_arrivals(self.current_t, self.trade_schedule, self._mid_price())
        self.current_selected_side = self.manager.select_side(self.current_t)
        return self._build_state(self.current_selected_side)

    def step(self, action_idx: int):
        if action_idx < 0 or action_idx >= len(self.action_fracs):
            raise IndexError(f"Invalid action_idx={action_idx}.")
        if self.current_t is None:
            raise RuntimeError("Call reset() before step().")

        t = int(self.current_t)
        selected_side = int(self.current_selected_side)

        if selected_side == 0:
            action_frac = 0.0
            child_qty = 0
        else:
            action_frac = float(self.action_fracs[action_idx])
            child_qty = self.manager.child_order_from_fraction(selected_side, action_frac, t)

        trades = [child_qty] if child_qty != 0 else []
        log = self.ob.step(
            t=t,
            trades=trades,
            bg_lam=float(self.step_params.get("bg_lam", 3.0)),
            bg_p_buy=float(self.step_params.get("bg_p_buy", 0.5)),
            rho=float(self.step_params.get("rho", 1.0)),
            noise=float(self.step_params.get("noise", 0.05)),
            perm_eta_ticks=float(self.step_params.get("perm_eta_ticks", 0.2)),
            perm_gamma=float(self.step_params.get("perm_gamma", 1.0)),
            perm_scale=float(self.step_params.get("perm_scale", 7500)),
            main_exec_kwargs=dict(self.step_params.get("main_exec_kwargs", {})),
            bg_exec_kwargs=dict(self.step_params.get("bg_exec_kwargs", {})),
            order=str(self.step_params.get("order", "bg_first")),
        )

        report = log["trade_reports"][0] if log.get("trade_reports") else None
        filled_qty = int(report["filled_qty"]) if report else 0
        fill_notional = float(report["notional"]) if report else 0.0

        step_shortfall = self.manager.attribute_fill_fifo(filled_qty, fill_notional) if filled_qty != 0 else 0.0
        reward = -step_shortfall

        info = {
            "t": t,
            "selected_side": selected_side,
            "action_fraction": action_frac,
            "child_qty_requested": child_qty,
            "filled_qty": filled_qty,
            "step_shortfall": step_shortfall,
            "reward": reward,
        }

        self.current_t += 1
        no_more_work = (not self.manager.has_active_orders()) and (not self._has_future_arrivals(self.current_t))
        terminal_done = self.current_t > self.terminal_t
        done = bool(no_more_work or terminal_done)

        terminal_penalty = 0.0
        if done and self.manager.has_active_orders():
            terminal_penalty = self.manager.apply_terminal_penalty(self._mid_price())
            reward -= terminal_penalty
            info["terminal_penalty"] = terminal_penalty
            info["reward"] = reward

        if done:
            info["manager_summary"] = self.manager.build_summary()
            next_state = self._build_state(selected_side=0)
            self.current_selected_side = 0
            return next_state, reward, done, info

        self.manager.ingest_arrivals(self.current_t, self.trade_schedule, self._mid_price())
        self.current_selected_side = self.manager.select_side(self.current_t)
        next_state = self._build_state(self.current_selected_side)
        return next_state, reward, done, info


def _resolve_device(device: str | torch.device | None) -> torch.device:
    if device is None:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if isinstance(device, torch.device):
        return device
    return torch.device(device)


def get_default_multi_order_env_params() -> dict[str, Any]:
    return {
        "ob_params": {
            "reference_price": 28.13,
            "tick_size": 0.01,
            "n_levels": 10,
            "seed": 7,
        },
        "init_params": {
            "execution_qty": 10000,
            "noise": 0.10,
            "mult_low": 5.0,
            "mult_high": 10.0,
            "hump_center": 3,
            "hump_sigma": 1.5,
            "tail_decay": 0.20,
            "top_dip": 0.40,
        },
        "step_params": {
            "bg_lam": 3.0,
            "bg_p_buy": 0.5,
            "rho": 1.0,
            "noise": 0.05,
            "perm_eta_ticks": 0.2,
            "perm_gamma": 1.0,
            "perm_scale": 7500,
            "main_exec_kwargs": {
                "impact_eta_ticks": 0.5,
                "impact_gamma": 1.5,
                "impact_scale": 7500,
                "impact_use_cum": True,
            },
            "bg_exec_kwargs": {
                "impact_eta_ticks": 0.5,
                "impact_gamma": 1.5,
                "impact_scale": 7500,
                "impact_use_cum": True,
            },
            "order": "bg_first",
        },
        "terminal_t": 50,
        "action_fracs": (
            0.0,
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
            0.35,
            0.40,
            0.45,
            0.50,
            0.55,
            0.60,
            0.65,
            0.70,
            0.75,
            0.80,
            0.85,
            0.90,
            0.95,
            1.0,
        ),
        "enforce_min_clip_to_finish": True,
        "seed_jitter_max": 10000,
    }


def get_default_multi_order_train_params() -> dict[str, Any]:
    return {
        "hidden_dims": [128, 64],
        "learning_rate": 1e-3,
        "buffer_capacity": 10000,
        "batch_size": 128,
        "gamma": 0.99,
        "target_update_freq": 50,
        "epsilon_start": 1.0,
        "epsilon_end": 0.05,
        "epsilon_decay": 1000,
        "num_episodes": 800,
    }


def get_default_multi_order_eval_params() -> dict[str, Any]:
    return {"n_episodes": 5}


def _aggregate_eval_summaries(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    if not episodes:
        return {
            "avg_arrival_vwap": None,
            "avg_global_vwap": None,
            "avg_slippage": None,
            "avg_net_filled_qty": None,
            "avg_total_cost": None,
            "episodes": [],
        }

    arrivals = [ep["arrival_vwap"] for ep in episodes if ep["arrival_vwap"] is not None]
    globals_ = [ep["global_vwap"] for ep in episodes if ep["global_vwap"] is not None]
    slippages = [ep["slippage"] for ep in episodes if ep["slippage"] is not None]
    net_filled = [ep["net_filled_qty"] for ep in episodes]
    total_costs = [ep["total_cost"] for ep in episodes]

    return {
        "avg_arrival_vwap": float(np.mean(arrivals)) if arrivals else None,
        "avg_global_vwap": float(np.mean(globals_)) if globals_ else None,
        "avg_slippage": float(np.mean(slippages)) if slippages else None,
        "avg_net_filled_qty": float(np.mean(net_filled)) if net_filled else None,
        "avg_total_cost": float(np.mean(total_costs)) if total_costs else None,
        "episodes": episodes,
    }


def evaluate_multi_order_policy(
    env: MultiParentExecutionEnv,
    policy_net: DQN,
    device: torch.device,
    n_episodes: int = 20,
    verbose: bool = True,
) -> dict[str, Any]:
    policy_net.eval()
    summaries = []

    for ep in range(int(n_episodes)):
        state_np = env.reset()
        state = torch.FloatTensor(state_np).to(device)
        done = False
        last_info = {}

        while not done:
            if env.current_selected_side == 0:
                action = 0
            else:
                with torch.no_grad():
                    q_values = policy_net(state.unsqueeze(0))
                    action = int(q_values.argmax().item())

            next_state_np, _, done, info = env.step(action)
            state = torch.FloatTensor(next_state_np).to(device)
            last_info = info

        ep_summary = last_info.get("manager_summary", env.manager.build_summary())
        summaries.append(ep_summary)

        if verbose:
            av = ep_summary["arrival_vwap"]
            gv = ep_summary["global_vwap"]
            sv = ep_summary["slippage"]
            avs = f"{av:.4f}" if av is not None else "None"
            gvs = f"{gv:.4f}" if gv is not None else "None"
            svs = f"{sv:.4f}" if sv is not None else "None"
            print(
                f"Eval episode {ep+1}: "
                f"requested={ep_summary['net_requested_qty']}, "
                f"filled={ep_summary['net_filled_qty']}, "
                f"arrival_vwap={avs}, global_vwap={gvs}, slippage={svs}, "
                f"open_qty_abs={ep_summary['open_qty_abs']}"
            )

    return _aggregate_eval_summaries(summaries)


def train_multi_order_deep_q_execution(
    trade_schedule: dict[int, Any],
    env_params: dict[str, Any],
    train_params: dict[str, Any],
    eval_params: dict[str, Any] | None = None,
    device: str | torch.device | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    if eval_params is None:
        eval_params = {}

    resolved_device = _resolve_device(device)
    if verbose:
        print(f"Using device: {resolved_device}")

    env = MultiParentExecutionEnv(trade_schedule=trade_schedule, **env_params)

    hidden_dims = list(train_params["hidden_dims"])
    learning_rate = float(train_params["learning_rate"])
    buffer_capacity = int(train_params["buffer_capacity"])
    batch_size = int(train_params["batch_size"])
    gamma = float(train_params["gamma"])
    target_update_freq = int(train_params["target_update_freq"])
    epsilon_start = float(train_params["epsilon_start"])
    epsilon_end = float(train_params["epsilon_end"])
    epsilon_decay = float(train_params["epsilon_decay"])
    num_episodes = int(train_params["num_episodes"])

    sample_state = env.reset()
    state_dim = int(len(sample_state))
    action_dim = len(env.action_fracs)

    policy_net = DQN(state_dim, action_dim, hidden_dims).to(resolved_device)
    target_net = DQN(state_dim, action_dim, hidden_dims).to(resolved_device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=learning_rate)
    replay_buffer = ReplayBuffer(buffer_capacity)

    global_step = 0
    epsilon = epsilon_start
    episode_rewards = []
    episode_costs = []
    loss_history = []

    for ep in range(num_episodes):
        state_np = env.reset()
        state = torch.FloatTensor(state_np).to(resolved_device)
        done = False
        total_reward = 0.0
        total_cost = 0.0

        while not done:
            if env.current_selected_side == 0:
                action = 0
            else:
                epsilon = epsilon_end + (epsilon_start - epsilon_end) * math.exp(-1.0 * global_step / epsilon_decay)
                if random.random() < epsilon:
                    action = random.randint(0, action_dim - 1)
                else:
                    with torch.no_grad():
                        q_values = policy_net(state.unsqueeze(0))
                        action = int(q_values.argmax().item())

            next_state_np, reward, done, _ = env.step(action)
            next_state = torch.FloatTensor(next_state_np).to(resolved_device)

            replay_buffer.push(state.cpu(), action, reward, next_state.cpu(), done)
            state = next_state
            total_reward += reward
            total_cost += -reward
            global_step += 1

            if len(replay_buffer) >= batch_size:
                states, actions, rewards, next_states, dones = replay_buffer.sample(batch_size)
                states = states.to(resolved_device)
                actions = actions.to(resolved_device)
                rewards = rewards.to(resolved_device)
                next_states = next_states.to(resolved_device)
                dones = dones.to(resolved_device)

                current_q = policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
                with torch.no_grad():
                    next_q = target_net(next_states).max(1)[0]
                    target_q = rewards + gamma * next_q * (~dones)

                loss = F.mse_loss(current_q, target_q)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                loss_history.append(float(loss.item()))

            if global_step % target_update_freq == 0:
                target_net.load_state_dict(policy_net.state_dict())

        episode_rewards.append(float(total_reward))
        episode_costs.append(float(total_cost))

        if verbose and (ep + 1) % 50 == 0:
            avg_cost = float(np.mean(episode_costs[-50:]))
            print(f"Episode {ep+1}, Avg Cost(last 50): {avg_cost:.2f}, Epsilon: {epsilon:.4f}")

    if verbose:
        print("Training finished.")

    eval_summary = evaluate_multi_order_policy(
        env=env,
        policy_net=policy_net,
        device=resolved_device,
        n_episodes=int(eval_params.get("n_episodes", 5)),
        verbose=verbose,
    )

    net_requested_qty = sum(int(v) for vals in normalize_trade_schedule(trade_schedule).values() for v in vals)
    result = {
        "strategy": "Deep-Q Multi-Parent (No Crossing)",
        "net_requested_qty": int(net_requested_qty),
        "net_filled_qty": eval_summary["avg_net_filled_qty"],
        "arrival_vwap": eval_summary["avg_arrival_vwap"],
        "global_vwap": eval_summary["avg_global_vwap"],
        "slippage": eval_summary["avg_slippage"],
        "implementation_shortfall": eval_summary["avg_slippage"],
        "training_diagnostics": {
            "episode_rewards": episode_rewards,
            "episode_costs": episode_costs,
            "loss_history": loss_history,
            "final_epsilon": float(epsilon),
            "device": str(resolved_device),
        },
        "evaluation_diagnostics": eval_summary,
        "artifacts": {
            "policy_net": policy_net,
            "target_net": target_net,
        },
        "manager_policy": {
            "no_crossing": True,
            "allocation": "fifo",
            "side_selection": "urgency_with_oldest_tie_break",
        },
    }
    return result


if __name__ == "__main__":
    schedule = get_default_trade_schedule()
    env_cfg = get_default_multi_order_env_params()
    train_cfg = get_default_multi_order_train_params()
    eval_cfg = get_default_multi_order_eval_params()

    output = train_multi_order_deep_q_execution(
        trade_schedule=schedule,
        env_params=env_cfg,
        train_params=train_cfg,
        eval_params=eval_cfg,
        device=None,
        verbose=True,
    )

    summary = {
        "strategy": output["strategy"],
        "net_requested_qty": output["net_requested_qty"],
        "net_filled_qty": output["net_filled_qty"],
        "arrival_vwap": output["arrival_vwap"],
        "global_vwap": output["global_vwap"],
        "slippage": output["slippage"],
        "implementation_shortfall": output["implementation_shortfall"],
    }
    print("\nDeep-Q multi-order summary:")
    print(summary)
