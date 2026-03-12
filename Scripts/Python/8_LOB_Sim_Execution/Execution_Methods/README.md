# Execution Methods Guide

This guide explains the four execution modules in this folder for users who are new to execution algorithms.

Core sign convention used across all methods:
- Positive quantity (`qty > 0`) means BUY.
- Negative quantity (`qty < 0`) means SELL.

Shared terminology:
- Parent order: the high-level order we want to execute (for example, sell 10,000 shares).
- Child order: smaller slices of a parent order sent over time.
- Arrival VWAP: benchmark price near parent-order arrival.
- Execution VWAP (global_vwap): realized average execution price.
- Slippage: performance gap between execution VWAP and arrival VWAP (direction-aware).

The methods all run on top of the synthetic order-book engine in `LOB_Simulation.py`.

---

## 1 Block_Trade

### What it does
`Block_Trade.py` executes each parent order immediately and fully at its arrival time (one-shot block style).

Main function:
- `simulate_multi_order_block(parent_orders, ob_params, sim_params)`

### Input variables
`parent_orders` (dict[int, int]):
- Format: `{arrival_t: signed_qty}`
- Example: `{5: -10000, 20: -5000, 35: 4000}`
- Meaning: at time 5 sell 10,000; at time 20 sell 5,000; at time 35 buy 4,000.

`ob_params` (dict): parameters for `OrderBook(...)`
- `reference_price` (float): starting reference price.
- `tick_size` (float): minimum price increment.
- `n_levels` (int): number of levels on each side of the book.
- `seed` (int or None): RNG seed for reproducibility.

`sim_params` (dict): simulation dynamics passed into `ob.run(...)`
- Background flow: `bg_lam`, `bg_p_buy`.
- Refill/noise: `rho`, `noise`.
- Permanent impact: `perm_eta_ticks`, `perm_gamma`, `perm_scale`.
- Temporary impact kwargs: `main_exec_kwargs`, `bg_exec_kwargs`.
- Processing order: `order` (for example `"bg_first"`).

### Output structure
Returns a dictionary with:
- `strategy`: method label (`"Multi-Block"`).
- `net_requested_qty`: sum of all requested parent quantities.
- `net_filled_qty`: total filled quantity.
- `arrival_vwap`: benchmark VWAP at arrival snapshots.
- `global_vwap`: realized VWAP.
- `slippage`: direction-aware gap vs benchmark.

### When to use
Use Block when you want a baseline for immediacy and impact. It is simple and aggressive.

### Example
```python
from Execution_Methods.Block_Trade import simulate_multi_order_block

parent_orders = {5: -10000, 20: -5000, 35: 4000}
ob_params = {"reference_price": 28.13, "tick_size": 0.01, "n_levels": 10, "seed": 42}
sim_params = {
    "bg_lam": 3.0,
    "bg_p_buy": 0.5,
    "rho": 1.0,
    "noise": 0.1,
    "perm_eta_ticks": 0.0,
    "perm_gamma": 1.0,
    "perm_scale": 7500,
    "main_exec_kwargs": {"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
    "bg_exec_kwargs": {"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
    "order": "bg_first",
}

result = simulate_multi_order_block(parent_orders, ob_params, sim_params)
print(result)
```

---

## 2 TWAP

### What it does
`TWAP.py` slices each parent order evenly across a fixed horizon (`time_horizon`) and nets overlapping child slices.

Main function:
- `simulate_multi_order_twap(parent_orders, time_horizon, ob_params, sim_params)`

### Input variables
`parent_orders` (dict[int, int]): same format as Block.

`time_horizon` (int):
- Number of steps used to split each parent order.
- Larger values spread execution over more time.

`ob_params` and `sim_params`: same meaning as Block.

### Internal behavior
For each parent order:
- Splits `abs(qty)` into `time_horizon` slices.
- Uses integer floor slices plus remainder on last slice.
- If two parent orders overlap in time, child quantities are netted at that step.

### Output structure
Returns:
- `strategy`: `"Multi-TWAP (Horizon=...)"`
- `net_requested_qty`
- `net_filled_qty`
- `arrival_vwap`
- `global_vwap`
- `slippage`

### When to use
Use TWAP for smoother execution with less instantaneous impact than Block, at the cost of time risk.

### Example
```python
from Execution_Methods.TWAP import simulate_multi_order_twap

result = simulate_multi_order_twap(
    parent_orders={5: -10000, 20: -5000, 35: 4000},
    time_horizon=20,
    ob_params={"reference_price": 28.13, "tick_size": 0.01, "n_levels": 10, "seed": 42},
    sim_params={
        "bg_lam": 3.0,
        "bg_p_buy": 0.5,
        "rho": 1.0,
        "noise": 0.1,
        "perm_eta_ticks": 0.0,
        "perm_gamma": 1.0,
        "perm_scale": 7500,
        "main_exec_kwargs": {"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
        "bg_exec_kwargs": {"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
        "order": "bg_first",
    },
)
print(result)
```

---

## 3 rl_lob_execution

### What it does
`rl_lob_execution.py` trains a Deep-Q (DQN) policy for a single parent order execution problem.

Main components:
- `lob_environment`: RL environment around the synthetic LOB.
- `DQN`: Q-network.
- `ReplayBuffer`: transition memory.
- `train_deep_q_execution(...)`: end-to-end trainer + evaluator.

### Key environment inputs
`lob_environment(...)` supports many parameters. The most important:
- Book setup: `reference_price`, `tick_size`, `n_levels`, `seed`.
- Background dynamics: `bg_lam`, `bg_p_buy`, `rho`, `noise_refill`.
- Impact controls: `perm_eta_ticks`, `perm_gamma`, `perm_scale`, plus temporary impact parameters.
- RL controls: `action_fracs`, `max_steps`, `enforce_min_clip_to_finish`, `order`.

### Training function
`train_deep_q_execution(env_params, train_params, eval_params=None, device=None, verbose=True)`

`env_params` from `get_default_env_params()`.

`train_params` from `get_default_train_params()` includes:
- network size: `hidden_dims`
- optimizer: `learning_rate`
- replay buffer and batching: `buffer_capacity`, `batch_size`
- discount and updates: `gamma`, `target_update_freq`
- exploration: `epsilon_start`, `epsilon_end`, `epsilon_decay`
- training length: `num_episodes`
- order size: `parent_qty` (signed)

`eval_params` from `get_default_eval_params()`:
- `n_episodes` for post-training evaluation.

### Output structure
Returns dictionary with:
- high-level metrics: `strategy`, `net_requested_qty`, `net_filled_qty`, `arrival_vwap`, `global_vwap`, `slippage`
- `training_diagnostics`: reward/cost/loss traces and final epsilon
- `evaluation_diagnostics`: averaged evaluation metrics + per-episode rows
- `artifacts`: trained `policy_net` and `target_net`

### When to use
Use this module when you want RL-based policy learning for a single parent order benchmark.

### Example
```python
from Execution_Methods.rl_lob_execution import (
    get_default_env_params,
    get_default_train_params,
    get_default_eval_params,
    train_deep_q_execution,
)

env_cfg = get_default_env_params()
train_cfg = get_default_train_params()
eval_cfg = get_default_eval_params()

output = train_deep_q_execution(
    env_params=env_cfg,
    train_params=train_cfg,
    eval_params=eval_cfg,
    device=None,
    verbose=True,
)
print(output["strategy"], output["slippage"])
```

---

## 4) multi_order_deep_qlearning

### What it does
`multi_order_deep_qlearning.py` extends RL to multiple parent orders with arrival-time schedule support.

Key ideas implemented:
- Normalize/ingest schedule of many parent orders.
- No crossing between buy/sell flows in same step.
- Side selection by urgency with oldest-order tie-break.
- FIFO fill attribution from child fills back to parent orders.
- End-of-horizon terminal penalty for unfilled inventory.

Main entrypoint:
- `train_multi_order_deep_q_execution(trade_schedule, env_params, train_params, eval_params=None, device=None, verbose=True)`

### Input variables
`trade_schedule`:
- accepted forms:
  - `{t: qty}`
  - `{t: [qty1, qty2, ...]}`
- normalized by `normalize_trade_schedule(...)` into canonical form.

`env_params` from `get_default_multi_order_env_params()`:
- `ob_params`: order-book setup.
- `init_params`: initial depth-shape setup.
- `step_params`: background flow + impact settings.
- `terminal_t`: global horizon.
- `action_fracs`: action space for sizing child clips.
- `enforce_min_clip_to_finish`, `seed_jitter_max`.

`train_params` from `get_default_multi_order_train_params()`:
- same RL knobs as single-parent version (`hidden_dims`, epsilon schedule, etc.)
- includes `num_episodes`.

`eval_params` from `get_default_multi_order_eval_params()`:
- `n_episodes`.

### Output structure
Returns dictionary including:
- `strategy`: `"Deep-Q Multi-Parent (No Crossing)"`
- `net_requested_qty`, `net_filled_qty`, `arrival_vwap`, `global_vwap`, `slippage`
- `implementation_shortfall`
- `training_diagnostics`
- `evaluation_diagnostics` (contains aggregated cost/slippage and per-episode summaries)
- `manager_policy` metadata (`no_crossing`, allocation style, side selection policy)

### When to use
Use this module when you need RL execution under multiple parent orders and realistic schedule interactions.

### Example
```python
from Execution_Methods.multi_order_deep_qlearning import (
    get_default_multi_order_env_params,
    get_default_multi_order_train_params,
    get_default_multi_order_eval_params,
    train_multi_order_deep_q_execution,
)

schedule = {5: -10000, 20: -5000, 35: 4000}
env_cfg = get_default_multi_order_env_params()
train_cfg = get_default_multi_order_train_params()
eval_cfg = get_default_multi_order_eval_params()

# Often reduced for local quick tests
train_cfg["num_episodes"] = 300
eval_cfg["n_episodes"] = 5

result = train_multi_order_deep_q_execution(
    trade_schedule=schedule,
    env_params=env_cfg,
    train_params=train_cfg,
    eval_params=eval_cfg,
    device=None,
    verbose=False,
)
print(result["strategy"], result["slippage"], result["evaluation_diagnostics"].get("avg_total_cost"))
```

---

## Practical method selection

- Use `Block_Trade` when you need a fast benchmark for immediate execution.
- Use `TWAP` when you want smoother time-sliced execution with minimal complexity.
- Use `rl_lob_execution` for RL research on one parent order.
- Use `multi_order_deep_qlearning` for realistic multi-order scheduling and policy learning.

## Notes for pipeline integration

When integrating with pipeline outputs (for example from validated trades):
- Build schedule as `{t_index: signed_qty}` after sorting by trade timestamp.
- Keep sign convention consistent (`+BUY`, `-SELL`).
- Store all strategy outputs, not only winner, so you can audit strategy decisions.
