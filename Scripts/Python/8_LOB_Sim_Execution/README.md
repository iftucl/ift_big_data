# 8_LOB_Sim_Execution

This module simulates order execution quality on a synthetic limit order book (LOB).
It supports three strategy families:
- Block execution
- Multi-order TWAP execution
- Multi-order Deep-Q RL execution

Sign convention used throughout this folder:
- `qty > 0` = BUY
- `qty < 0` = SELL

---

## 1 How This Connects Back to the Overall Pipeline

### Big picture
`8_LOB_Sim_Execution` is the execution simulation layer. It sits after data preparation/validation and helps choose execution strategy before real routing.

Typical flow in this repository:
1. `0_RandomTrades`: generate granular trades into MinIO
2. `1_ETL_MongoDB`: load trades into MongoDB
3. `2_ETL_Mongodb_SQL` and/or `3_ETL_Duckdb_Postgres`: aggregate positions into Postgres
4. `4_Calibrate_Factors`: compute and cache calibration params in Redis
5. `5_Trades_Validate`: mark suspect/non-suspect trades
6. `8_LOB_Sim_Execution`: simulate execution outcomes and compare strategies

### How `main.py` uses pipeline data
`main.py` now has two modes:
- `--mode demo`: uses hardcoded schedule and compares Block/TWAP/Deep-Q
- `--mode pipeline`: reads validated trades from MongoDB (`Trades.SuspectTrades`), builds schedules grouped by `(Trader, Symbol, Ccy)`, runs all three strategies, and writes results to `Trades.ExecutionSimulation`

Pipeline defaults (inside `main.py`):
- source collection: `SuspectTrades`
- sink collection: `ExecutionSimulation`
- default source filter: `IsSuspect == false`
- time filter: `DateTime in [run_start, run_end)`

### Pipeline command example
```bash
cd /Users/siutungwong/Desktop/ift_big_data_projects/ift_big_data/Scripts/Python/8_LOB_Sim_Execution
python main.py --mode pipeline --env_type dev --run_start 2026-03-12T00:00:00Z --run_end 2026-03-13T00:00:00Z --symbol AAPL
```

Optional runtime overrides via environment variables:
- `LOB_MONGO_URI`, `LOB_MONGO_DATABASE`, `LOB_MONGO_SOURCE_COLLECTION`, `LOB_MONGO_SINK_COLLECTION`
- `LOB_TICK_SIZE`, `LOB_SIM_SEED`, `LOB_N_LEVELS`
- `LOB_TWAP_HORIZON`, `LOB_DEEPQ_TRAIN_EPISODES`, `LOB_DEEPQ_EVAL_EPISODES`

---

## 2 How The Simulated LOB Works, Variables, and What They Do

The simulator is implemented in `LOB_Simulation.py` as `OrderBook`.

### Core object
`OrderBook(reference_price, tick_size, n_levels=10, seed=None)`

Variables:
- `reference_price`: baseline mid-price level to initialize around
- `tick_size`: minimum price increment
- `n_levels`: number of bid and ask levels
- `seed`: RNG seed for reproducible runs

### Initial depth generation (`order_book_levels`)
`order_book_levels(execution_qty, noise=0.10, mult_low=5.0, mult_high=10.0, hump_center=3, hump_sigma=1.5, tail_decay=0.20, top_dip=0.40)`

Variables:
- `execution_qty`: reference size used to scale total depth
- `noise`: multiplicative noise in level quantities
- `mult_low`, `mult_high`: bounds for total depth multiplier relative to `execution_qty`
- `hump_center`: depth peak level index
- `hump_sigma`: spread of hump profile
- `tail_decay`: decay speed deeper in the book
- `top_dip`: dampening at top of book level

### Execution impact model (`execute_market_order`)
`execute_market_order(qty_signed, impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=None, impact_use_cum=True)`

Variables:
- `qty_signed`: signed market order quantity
- `impact_eta_ticks`: temporary impact strength in ticks
- `impact_gamma`: nonlinearity exponent for impact
- `impact_scale`: normalization scale for order size
- `impact_use_cum`: if true, impact scales with cumulative fill size

### One simulation step (`step`)
`step(t, trades=None, bg_lam=2.0, bg_p_buy=0.5, rho=0.30, noise=0.05, perm_eta_ticks=0.8, perm_gamma=1.0, perm_scale=7500, main_exec_kwargs=None, bg_exec_kwargs=None, order="bg_first")`

Variables:
- `t`: step index
- `trades`: list of signed main trades executed this step
- `bg_lam`: Poisson intensity for background order arrivals
- `bg_p_buy`: probability background order is buy
- `rho`: refill mean reversion strength toward target depth
- `noise`: refill randomness
- `perm_eta_ticks`, `perm_gamma`, `perm_scale`: permanent impact shift parameters
- `main_exec_kwargs`: temp impact settings for main orders
- `bg_exec_kwargs`: temp impact settings for background flow
- `order`: whether background executes before or after main trade (`"bg_first"` or `"main_first"`)

### Full run loop (`run`)
`run(n_steps, trade_schedule=None, ... same dynamics params ...)`

Variables:
- `n_steps`: total simulation steps
- `trade_schedule`: dict where each key is step `t`, value is either signed qty or list of signed qty values

### Market-maker restore controls on the book object
Set directly on object before run:
- `ob.mm_p_restore`: probability of restoring exhausted best level
- `ob.mm_vol_frac`: restored size fraction of current best quantity
- `ob.mm_min_qty`: minimum restored quantity

### Minimal LOB-only example
```python
from LOB_Simulation import OrderBook

ob = OrderBook(reference_price=28.13, tick_size=0.01, n_levels=10, seed=42)
ob.order_book_levels(
    execution_qty=10000,
    noise=0.08,
    mult_low=4.0,
    mult_high=9.0,
    hump_center=3,
    hump_sigma=1.4,
    tail_decay=0.22,
    top_dip=0.35,
)

history, logs = ob.run(
    n_steps=100,
    trade_schedule={5: -10000, 20: -5000, 35: 4000},
    bg_lam=3.0,
    bg_p_buy=0.5,
    rho=1.0,
    noise=0.10,
    perm_eta_ticks=0.0,
    perm_gamma=1.0,
    perm_scale=7500,
    main_exec_kwargs={"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
    bg_exec_kwargs={"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
    order="bg_first",
)
```

---

## 3 Block Order and How To Use It With The Simulated LOB

Module: `Execution_Methods/Block_Trade.py`

Entry point:
- `simulate_multi_order_block(parent_orders, ob_params, sim_params)`

### Inputs
`parent_orders`:
- `{arrival_t: signed_qty}`
- Example: `{5: -10000, 20: -5000, 35: 4000}`

`ob_params`:
- `reference_price`, `tick_size`, `n_levels`, `seed`

`sim_params`:
- same dynamics as `OrderBook.run(...)`

### What it does
- Executes each parent order fully at arrival time (no slicing)
- Computes aggregated execution metrics

### Output keys
- `strategy`
- `net_requested_qty`
- `net_filled_qty`
- `arrival_vwap`
- `global_vwap`
- `slippage`

### Example with variable tuning
```python
from Execution_Methods.Block_Trade import simulate_multi_order_block

parent_orders = {5: -12000, 25: -6000, 40: 3000}

ob_params = {
    "reference_price": 31.25,
    "tick_size": 0.01,
    "n_levels": 12,   # deeper book than default
    "seed": 7,
}

sim_params = {
    "bg_lam": 2.5,
    "bg_p_buy": 0.55,
    "rho": 0.9,
    "noise": 0.08,
    "perm_eta_ticks": 0.1,
    "perm_gamma": 1.0,
    "perm_scale": 9000,
    "main_exec_kwargs": {"impact_eta_ticks": 0.4, "impact_gamma": 1.5, "impact_scale": 9000, "impact_use_cum": True},
    "bg_exec_kwargs": {"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 9000, "impact_use_cum": True},
    "order": "bg_first",
}

res = simulate_multi_order_block(parent_orders, ob_params, sim_params)
print(res)
```

---

## 4 Multi-Order TWAP and How To Use It With The Simulated LOB

Module: `Execution_Methods/TWAP.py`

Entry point:
- `simulate_multi_order_twap(parent_orders, time_horizon, ob_params, sim_params)`

### Additional variable vs Block
`time_horizon`:
- Number of steps over which each parent order is sliced
- Larger horizon means smoother, slower execution

### What it does
- Splits each parent order into near-equal slices
- Aggregates overlapping slices across orders into net child orders per step
- Runs simulation and computes execution metrics

### Output keys
- `strategy`
- `net_requested_qty`
- `net_filled_qty`
- `arrival_vwap`
- `global_vwap`
- `slippage`

### Example with variable tuning
```python
from Execution_Methods.TWAP import simulate_multi_order_twap

parent_orders = {5: -10000, 20: -5000, 35: 4000}
time_horizon = 30  # slower execution than default 20

ob_params = {"reference_price": 28.13, "tick_size": 0.01, "n_levels": 10, "seed": 42}

sim_params = {
    "bg_lam": 3.5,
    "bg_p_buy": 0.5,
    "rho": 1.0,
    "noise": 0.10,
    "perm_eta_ticks": 0.0,
    "perm_gamma": 1.0,
    "perm_scale": 7500,
    "main_exec_kwargs": {"impact_eta_ticks": 0.2, "impact_gamma": 1.6, "impact_scale": 7500, "impact_use_cum": True},
    "bg_exec_kwargs": {"impact_eta_ticks": 0.0, "impact_gamma": 1.5, "impact_scale": 7500, "impact_use_cum": True},
    "order": "bg_first",
}

res = simulate_multi_order_twap(parent_orders, time_horizon, ob_params, sim_params)
print(res)
```

---

## 5 Multi-Order Deep Q Learning and How To Use It With The LOB Simulator

Module: `Execution_Methods/multi_order_deep_qlearning.py`

Entry points:
- `get_default_multi_order_env_params()`
- `get_default_multi_order_train_params()`
- `get_default_multi_order_eval_params()`
- `train_multi_order_deep_q_execution(...)`

### Core input contracts
`trade_schedule`:
- accepted format:
  - `{t: qty}`
  - `{t: [qty1, qty2, ...]}`
- internally normalized to canonical schedule

`env_params` (major sub-groups):
- `ob_params`: `reference_price`, `tick_size`, `n_levels`, `seed`
- `init_params`: initial shape/depth controls (`execution_qty`, `noise`, `mult_low`, `mult_high`, `hump_center`, `hump_sigma`, `tail_decay`, `top_dip`)
- `step_params`: dynamic/impact controls for each step (`bg_lam`, `bg_p_buy`, `rho`, `noise`, permanent impact, main/bg execution impact, `order`)
- `terminal_t`: total allowed time
- `action_fracs`: action space (fractions of remaining inventory)
- `enforce_min_clip_to_finish`, `seed_jitter_max`

`train_params`:
- model and RL training controls (`hidden_dims`, `learning_rate`, `buffer_capacity`, `batch_size`, `gamma`, `target_update_freq`, epsilon schedule, `num_episodes`)

`eval_params`:
- `n_episodes` for policy evaluation

### What it does
- Learns a policy that chooses child-order fraction by step
- Supports multiple parent orders with FIFO attribution and no crossing between buy/sell streams
- Returns average execution and cost metrics plus diagnostics

### Output keys (high-level)
- `strategy`
- `net_requested_qty`
- `net_filled_qty`
- `arrival_vwap`
- `global_vwap`
- `slippage`
- `implementation_shortfall`
- `training_diagnostics`
- `evaluation_diagnostics`
- `manager_policy`

### Example with variable tuning
```python
from Execution_Methods.multi_order_deep_qlearning import (
    get_default_multi_order_env_params,
    get_default_multi_order_train_params,
    get_default_multi_order_eval_params,
    train_multi_order_deep_q_execution,
)

schedule = {
    5: -10000,
    20: -5000,
    35: 4000,
}

env_cfg = get_default_multi_order_env_params()
train_cfg = get_default_multi_order_train_params()
eval_cfg = get_default_multi_order_eval_params()

# LOB-related tuning
env_cfg["ob_params"]["reference_price"] = 28.13
env_cfg["ob_params"]["tick_size"] = 0.01
env_cfg["terminal_t"] = 120
env_cfg["step_params"]["bg_lam"] = 4.0
env_cfg["step_params"]["main_exec_kwargs"]["impact_eta_ticks"] = 0.3

# RL training/eval tuning
train_cfg["num_episodes"] = 300
train_cfg["epsilon_decay"] = 1200
eval_cfg["n_episodes"] = 8

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

### Practical note
For reproducibility when comparing methods:
- keep `seed`, `reference_price`, `tick_size`, `n_levels`, and core simulation dynamics aligned across strategies
- change one variable family at a time (for example only `main_exec_kwargs`) when doing experiments

