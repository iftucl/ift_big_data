import math
import random
import numpy as np
from collections import deque
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import Any
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import LOB_Simulation


class lob_environment:
    def __init__(self,
                 reference_price=28.13,
                 tick_size=0.01,
                 n_levels=10,
                 seed=None,
                 # Book initialisation parameters
                 noise=0.10,
                 mult_low=5.0,
                 mult_high=10.0,
                 book_init_execution_qty=10000,
                 # Background flow and refill
                 bg_lam=3.0,
                 bg_p_buy=0.5,
                 rho=0.30,
                 noise_refill=0.05,
                 # Permanent impact (set to 0 for simple demonstration)
                 perm_eta_ticks=0.0,
                 perm_gamma=1.0,
                 perm_scale=7500,
                 # Temporary impact for main trades
                 impact_eta_ticks=0.0,
                 impact_gamma=1.5,
                 impact_scale=7500,
                 impact_use_cum=True,
                 # Temporary impact for background trades (usually zero)
                 bg_impact_eta_ticks=0.0,
                 bg_impact_gamma=1.5,
                 bg_impact_scale=7500,
                 bg_impact_use_cum=True,
                 # RL specific
                 action_fracs=(0.0, 0.1, 0.25, 0.5, 1.0),
                 max_steps=20,
                 enforce_min_clip_to_finish=True,
                 order="bg_first"):

        self.reference_price = reference_price
        self.tick_size = tick_size
        self.n_levels = n_levels
        self.base_seed = seed
        self.seed = seed   # will be updated on reset

        self.noise = noise
        self.mult_low = mult_low
        self.mult_high = mult_high
        self.book_init_execution_qty = abs(int(book_init_execution_qty))

        self.bg_lam = bg_lam
        self.bg_p_buy = bg_p_buy
        self.rho = rho
        self.noise_refill = noise_refill

        self.perm_eta_ticks = perm_eta_ticks
        self.perm_gamma = perm_gamma
        self.perm_scale = perm_scale

        self.main_exec_kwargs = {
            "impact_eta_ticks": impact_eta_ticks,
            "impact_gamma": impact_gamma,
            "impact_scale": impact_scale,
            "impact_use_cum": impact_use_cum,
        }
        self.bg_exec_kwargs = {
            "impact_eta_ticks": bg_impact_eta_ticks,
            "impact_gamma": bg_impact_gamma,
            "impact_scale": bg_impact_scale,
            "impact_use_cum": bg_impact_use_cum,
        }

        self.action_fracs = list(action_fracs)
        self.max_steps = max_steps
        self.enforce_min_clip_to_finish = enforce_min_clip_to_finish
        self.order = order

        # Will be set in reset()
        self.ob = None
        self.remaining = None
        self.parent_qty = None
        self.arrival_price = None
        self.total_notional = None
        self.episode_step = None
        self.total_abs_notional = None
        self.total_filled_abs = None

    def _get_state(self):
        """Construct the observation vector from the current LOB."""
        bids = self.ob.bids
        asks = self.ob.asks

        # Best levels
        best_bid = bids[0][0] if bids else self.reference_price
        best_ask = asks[0][0] if asks else self.reference_price
        bid_size = bids[0][1] if bids else 0
        ask_size = asks[0][1] if asks else 0

        # Normalised features
        remaining_frac = self.remaining / self.parent_qty if self.parent_qty != 0 else 0.0
        time_frac = (self.max_steps - self.episode_step) / self.max_steps

        # Price levels relative to arrival (in ticks)
        bid_rel = (best_bid - self.arrival_price) / self.tick_size
        ask_rel = (best_ask - self.arrival_price) / self.tick_size

        # Log‑scale sizes (to handle wide range)
        bid_size_norm = np.log1p(bid_size) / 10.0
        ask_size_norm = np.log1p(ask_size) / 10.0

        # Next few levels (top 3)
        n_depth = 3
        bid_prices, bid_sizes, ask_prices, ask_sizes = [], [], [], []
        for i in range(n_depth):
            if i < len(bids):
                p, q = bids[i]
                bid_prices.append((p - self.arrival_price) / self.tick_size)
                bid_sizes.append(np.log1p(q))
            else:
                bid_prices.append(0.0)
                bid_sizes.append(0.0)
            if i < len(asks):
                p, q = asks[i]
                ask_prices.append((p - self.arrival_price) / self.tick_size)
                ask_sizes.append(np.log1p(q))
            else:
                ask_prices.append(0.0)
                ask_sizes.append(0.0)

        # Flatten into a single array
        state = np.array([
            remaining_frac,
            time_frac,
            bid_rel,
            ask_rel,
            bid_size_norm,
            ask_size_norm,
            *bid_prices,
            *bid_sizes,
            *ask_prices,
            *ask_sizes
        ], dtype=np.float32)
        return state

    def reset(self, parent_qty, side=None):
        """
        Start a new episode.
        parent_qty : signed quantity to execute (negative = sell, positive = buy)
        side       : optional, if given overrides sign (e.g., side='sell')
        """
        if side is not None:
            parent_qty = abs(parent_qty) * (1 if side == 'buy' else -1)
        self.parent_qty = parent_qty
        self.remaining = parent_qty
        self.total_notional = 0.0
        self.episode_step = 0
        self.total_abs_notional = 0.0
        self.total_filled_abs = 0

        # Vary the seed slightly to get different random streams each episode
        if self.base_seed is not None:
            self.seed = self.base_seed + np.random.randint(0, 10000)

        # Create and initialise the order book
        self.ob = LOB_Simulation.OrderBook(
            self.reference_price,
            self.tick_size,
            self.n_levels,
            self.seed,
        )
        self.ob.order_book_levels(execution_qty=self.book_init_execution_qty,
                                  noise=self.noise,
                                  mult_low=self.mult_low,
                                  mult_high=self.mult_high)

        # Arrival mid price (benchmark)
        best_bid = self.ob.bids[0][0] if self.ob.bids else self.reference_price
        best_ask = self.ob.asks[0][0] if self.ob.asks else self.reference_price
        self.arrival_price = (best_bid + best_ask) / 2.0

        return self._get_state()

    def step(self, action_idx):
        """
        Execute one time step.
        action_idx : index into self.action_fracs
        returns (next_state, reward, done, info)
        """
        # ----- 1. Determine quantity to trade this step -----
        if self.episode_step == self.max_steps - 1:
            # Last step: must liquidate all remaining inventory
            qty_to_trade = self.remaining
        else:
            frac = self.action_fracs[action_idx]
            qty_to_trade = int(round(frac * abs(self.remaining)))
            qty_to_trade = qty_to_trade * (1 if self.remaining > 0 else -1)

            # Optional pacing guardrail: ensure we trade enough each step
            # so the remaining inventory can be finished by the horizon.
            if self.enforce_min_clip_to_finish:
                steps_left_including_this = self.max_steps - self.episode_step
                min_abs_clip = int(math.ceil(abs(self.remaining) / max(1, steps_left_including_this)))
                if abs(qty_to_trade) < min_abs_clip:
                    qty_to_trade = min_abs_clip * (1 if self.remaining > 0 else -1)

            # Guard against rounding overshoot
            if abs(qty_to_trade) > abs(self.remaining):
                qty_to_trade = self.remaining

        # ----- 2. Advance the order book by one time unit -----
        # (background flow, main trade, refill, permanent impact)
        t_label = self.episode_step + 1
        log = self.ob.step(
            t=t_label,
            trades=[qty_to_trade] if qty_to_trade != 0 else [],
            bg_lam=self.bg_lam,
            bg_p_buy=self.bg_p_buy,
            rho=self.rho,
            noise=self.noise_refill,
            perm_eta_ticks=self.perm_eta_ticks,
            perm_gamma=self.perm_gamma,
            perm_scale=self.perm_scale,
            main_exec_kwargs=self.main_exec_kwargs,
            bg_exec_kwargs=self.bg_exec_kwargs,
            order=self.order
        )

        # ----- 3. Update inventory and compute incremental cost -----
        trade_report = log['trade_reports'][0] if log['trade_reports'] else None
        step_cost = 0.0
        if trade_report is not None:
            filled = trade_report['filled_qty']
            notional = trade_report['notional']
            filled_abs = abs(filled)
            self.remaining -= filled
            self.total_notional += notional
            self.total_abs_notional += abs(notional)
            self.total_filled_abs += filled_abs

            # Incremental cost relative to arrival price
            vwap = trade_report['vwap']
            if filled_abs > 0 and vwap is not None:
                if self.parent_qty < 0:   # sell
                    step_cost = (self.arrival_price - vwap) * filled_abs
                else:                      # buy
                    step_cost = (vwap - self.arrival_price) * filled_abs
            reward = -step_cost
        else:
            reward = 0.0

        self.episode_step += 1

        # ----- 4. Check termination -----
        done = (self.remaining == 0) or (self.episode_step >= self.max_steps)

        # If we hit max_steps and still have inventory, mark to market at current mid
        # (this handles the case where full liquidation failed due to insufficient depth)
        if done and self.remaining != 0:
            best_bid = self.ob.bids[0][0] if self.ob.bids else self.reference_price
            best_ask = self.ob.asks[0][0] if self.ob.asks else self.reference_price
            current_mid = (best_bid + best_ask) / 2.0
            rem_abs = abs(self.remaining)
            if self.parent_qty < 0:
                terminal_cost = (self.arrival_price - current_mid) * rem_abs
            else:
                terminal_cost = (current_mid - self.arrival_price) * rem_abs
            reward += -terminal_cost   # add the mark‑to‑market penalty
            step_cost += terminal_cost
            # (remaining is not actually filled, but we treat it as an opportunity cost)

        next_state = self._get_state()
        info = {
            'filled': trade_report['filled_qty'] if trade_report else 0,
            'vwap': trade_report['vwap'] if trade_report else None,
            'remaining': self.remaining,
            'step': self.episode_step,
            'cost': step_cost
        }

        if done:
            episode_vwap = (self.total_abs_notional / self.total_filled_abs) if self.total_filled_abs > 0 else None
            if episode_vwap is not None:
                slippage = (episode_vwap - self.arrival_price) if self.parent_qty > 0 else (self.arrival_price - episode_vwap)
            else:
                slippage = None
            info['episode_vwap'] = episode_vwap
            info['episode_slippage'] = slippage

        return next_state, reward, done, info

class DQN(nn.Module):
    def __init__(self, state_dim, action_dim, hidden_dims=[128, 64]):
        """
        Args:
            state_dim (int): dimension of the input state (18 for our environment)
            action_dim (int): number of discrete actions
            hidden_dims (list): list of hidden layer sizes
        """
        super(DQN, self).__init__()
        layers = []
        prev_dim = state_dim
        for h in hidden_dims:
            layers.append(nn.Linear(prev_dim, h))
            layers.append(nn.ReLU())
            prev_dim = h
        layers.append(nn.Linear(prev_dim, action_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        """
        Args:
            x (torch.Tensor): state tensor of shape (batch_size, state_dim)
        Returns:
            torch.Tensor: Q-values for each action, shape (batch_size, action_dim)
        """
        return self.net(x)

class ReplayBuffer:
    def __init__(self, capacity):
        """
        Args:
            capacity (int): maximum number of transitions to store
        """
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """
        Store a transition.
        Args:
            state:       numpy array or tensor of shape (state_dim,)
            action:      int (action index)
            reward:      float
            next_state:  numpy array or tensor of shape (state_dim,)
            done:        bool
        """
        # Convert numpy arrays to tensors for consistency
        if not isinstance(state, torch.Tensor):
            state = torch.FloatTensor(state)
        if not isinstance(next_state, torch.Tensor):
            next_state = torch.FloatTensor(next_state)
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        """
        Sample a random batch of transitions.
        Returns:
            A tuple of (states, actions, rewards, next_states, dones)
            all as PyTorch tensors (except dones as booleans).
        """
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        # Stack into tensors
        states = torch.stack(states)                 # (batch, state_dim)
        actions = torch.LongTensor(actions)          # (batch,)
        rewards = torch.FloatTensor(rewards)         # (batch,)
        next_states = torch.stack(next_states)       # (batch, state_dim)
        dones = torch.BoolTensor(dones)               # (batch,)

        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)

def get_default_env_params() -> dict[str, Any]:
    return {
        "reference_price": 28.13,
        "tick_size": 0.01,
        "n_levels": 10,
        "seed": 7,
        "noise": 0.10,
        "mult_low": 5.0,
        "mult_high": 10.0,
        "book_init_execution_qty": 7000,
        "bg_lam": 3.0,
        "bg_p_buy": 0.5,
        "rho": 1.0,
        "noise_refill": 0.05,
        "perm_eta_ticks": 0.2,
        "perm_gamma": 1.0,
        "perm_scale": 7500,
        "impact_eta_ticks": 0.5,
        "impact_gamma": 1.5,
        "impact_scale": 7500,
        "impact_use_cum": True,
        "bg_impact_eta_ticks": 0.5,
        "bg_impact_gamma": 1.5,
        "bg_impact_scale": 7500,
        "bg_impact_use_cum": True,
        "action_fracs": (0.0, 0.1, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.0),
        "max_steps": 50,
        "order": "bg_first",
    }


def get_default_train_params() -> dict[str, Any]:
    return {
        "hidden_dims": [128, 64],
        "learning_rate": 1e-3,
        "buffer_capacity": 10000,
        "batch_size": 128,
        "gamma": 0.99,
        "target_update_freq": 50,
        "epsilon_start": 1.0,
        "epsilon_end": 0.05,
        "epsilon_decay": 500,
        "num_episodes": 5000,
        "parent_qty": -10000,
    }


def get_default_eval_params() -> dict[str, Any]:
    return {"n_episodes": 5}


def get_epsilon(step: int, epsilon_start: float, epsilon_end: float, epsilon_decay: float) -> float:
    return epsilon_end + (epsilon_start - epsilon_end) * math.exp(-1.0 * step / epsilon_decay)


def _resolve_device(device: str | torch.device | None) -> torch.device:
    if device is None:
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if isinstance(device, torch.device):
        return device
    return torch.device(device)


def evaluate_policy(env, policy_net, parent_qty, device, n_episodes=100, verbose=True):
    policy_net.eval()
    parent_abs = max(1, abs(parent_qty))
    total_costs = []
    per_episode = []

    for ep in range(n_episodes):
        state = env.reset(parent_qty=parent_qty)
        arrival_vwap = float(env.arrival_price)
        state = torch.FloatTensor(state).to(device)
        done = False
        cost = 0.0
        step = 0
        action_schedule = []
        exec_frac_schedule = []
        info = {}

        while not done:
            with torch.no_grad():
                q_values = policy_net(state.unsqueeze(0))
                action = q_values.argmax().item()

            if step < env.max_steps - 1:
                frac = env.action_fracs[action]
            else:
                frac = 1.0
            action_schedule.append(frac)

            next_state_np, reward, done, info = env.step(action)
            state = torch.FloatTensor(next_state_np).to(device)
            exec_frac_schedule.append(abs(info["filled"]) / parent_abs)
            cost += -reward
            step += 1

        total_costs.append(cost)

        global_vwap = info.get("episode_vwap", None)
        if global_vwap is not None:
            global_vwap = float(global_vwap)

        if global_vwap is None:
            slippage = None
        elif parent_qty > 0:
            slippage = global_vwap - arrival_vwap
        else:
            slippage = arrival_vwap - global_vwap

        net_filled_qty = int(parent_qty - info.get("remaining", parent_qty))

        ep_row = {
            "episode": ep + 1,
            "cost": float(cost),
            "arrival_vwap": arrival_vwap,
            "global_vwap": global_vwap,
            "slippage": slippage,
            "net_requested_qty": int(parent_qty),
            "net_filled_qty": net_filled_qty,
            "action_schedule": action_schedule,
            "exec_frac_parent": exec_frac_schedule,
        }
        per_episode.append(ep_row)

        if verbose:
            vwap_str = f"{global_vwap:.4f}" if global_vwap is not None else "None"
            slippage_str = f"{slippage:.4f}" if slippage is not None else "None"
            print(
                f"Test episode {ep+1}: cost = {cost:.2f}, vwap = {vwap_str}, slippage = {slippage_str}, "
                f"actions = {[f'{f:.2f}' for f in action_schedule]}, "
                f"exec_frac_parent = {[f'{f:.2f}' for f in exec_frac_schedule]}"
            )

    avg_cost = float(np.mean(total_costs)) if total_costs else None
    arrival_vals = [r["arrival_vwap"] for r in per_episode if r["arrival_vwap"] is not None]
    global_vals = [r["global_vwap"] for r in per_episode if r["global_vwap"] is not None]
    slip_vals = [r["slippage"] for r in per_episode if r["slippage"] is not None]
    filled_vals = [r["net_filled_qty"] for r in per_episode]

    summary = {
        "avg_cost": avg_cost,
        "avg_arrival_vwap": float(np.mean(arrival_vals)) if arrival_vals else None,
        "avg_global_vwap": float(np.mean(global_vals)) if global_vals else None,
        "avg_slippage": float(np.mean(slip_vals)) if slip_vals else None,
        "avg_net_filled_qty": float(np.mean(filled_vals)) if filled_vals else None,
        "episodes": per_episode,
    }

    if verbose and avg_cost is not None:
        print(f"Average test cost: {avg_cost:.2f}")

    return summary


def train_deep_q_execution(env_params, train_params, eval_params=None, device=None, verbose=True):
    if env_params is None or train_params is None:
        raise ValueError("env_params and train_params must be provided.")

    if eval_params is None:
        eval_params = {}

    resolved_device = _resolve_device(device)
    if verbose:
        print(f"Using device: {resolved_device}")

    env = lob_environment(**env_params)

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
    parent_qty = int(train_params["parent_qty"])

    sample_state = env.reset(parent_qty=parent_qty)
    state_dim = int(len(sample_state))
    action_dim = len(env.action_fracs)

    policy_net = DQN(state_dim, action_dim, hidden_dims).to(resolved_device)
    target_net = DQN(state_dim, action_dim, hidden_dims).to(resolved_device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=learning_rate)
    replay_buffer = ReplayBuffer(buffer_capacity)

    global_step = 0
    episode_rewards = []
    episode_costs = []
    loss_history = []
    epsilon = epsilon_start

    for ep in range(num_episodes):
        state = env.reset(parent_qty=parent_qty)
        state = torch.FloatTensor(state).to(resolved_device)
        done = False
        total_reward = 0.0
        total_cost = 0.0

        while not done:
            epsilon = get_epsilon(global_step, epsilon_start, epsilon_end, epsilon_decay)
            if random.random() < epsilon:
                action = random.randint(0, action_dim - 1)
            else:
                with torch.no_grad():
                    q_values = policy_net(state.unsqueeze(0))
                    action = q_values.argmax().item()

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
            print(f"Episode {ep+1}, Avg Cost (last 50): {avg_cost:.2f}, Epsilon: {epsilon:.4f}")

    if verbose:
        print("Training finished.")

    n_eval_episodes = int(eval_params.get("n_episodes", 5))
    eval_summary = evaluate_policy(
        env=env,
        policy_net=policy_net,
        parent_qty=parent_qty,
        device=resolved_device,
        n_episodes=n_eval_episodes,
        verbose=verbose,
    )

    result = {
        "strategy": "Deep-Q (Single Parent)",
        "net_requested_qty": int(parent_qty),
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
    }
    return result


if __name__ == "__main__":
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

    summary = {
        "strategy": output["strategy"],
        "net_requested_qty": output["net_requested_qty"],
        "net_filled_qty": output["net_filled_qty"],
        "arrival_vwap": output["arrival_vwap"],
        "global_vwap": output["global_vwap"],
        "slippage": output["slippage"],
        "implementation_shortfall": output["implementation_shortfall"],
    }
    print("\nDeep-Q summary:")
    print(summary)
