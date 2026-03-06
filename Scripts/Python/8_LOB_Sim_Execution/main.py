from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Execution_Methods import Block_Trade, TWAP

if __name__ == "__main__":
    ob_params = dict(reference_price=28.13, tick_size=0.01, n_levels=10, seed=42)
    sim_params = dict(
        bg_lam=3.0, bg_p_buy=0.50, rho=1.0, noise=0.1,
        perm_eta_ticks=0.0, perm_gamma=1.0, perm_scale=7500,
        main_exec_kwargs=dict(impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=7500, impact_use_cum=True),
        bg_exec_kwargs=dict(impact_eta_ticks=0.0, impact_gamma=1.5, impact_scale=7500, impact_use_cum=True),
        order="bg_first"
    )

    # Arriving order flow: Sell 10k at t=5, Sell 5k at t=20, Buy 4k at t=35
    parent_orders = {
        5: -10000,
        20: -5000,
        35: 4000
    }

    horizon = 100

    print("\n" + "=" * 50)
    print("MULTI-ORDER EXECUTION COMPARISON")
    print("=" * 50)

    # Run Block
    block_res = Block_Trade.simulate_multi_order_block(parent_orders, ob_params, sim_params)
    # Run TWAP
    twap_res = TWAP.simulate_multi_order_twap(parent_orders, horizon, ob_params, sim_params)

    for res in [block_res, twap_res]:
        print(f"Strategy:         {res['strategy']}")
        print(f"Net Requested:    {res['net_requested_qty']}")
        print(f"Net Filled:       {res['net_filled_qty']}")
        print(f"Arrival VWAP:     {res['arrival_vwap']:.4f}")
        print(f"Final Execution:  {res['global_vwap']:.4f}")
        slippage_ticks = res['slippage'] / ob_params['tick_size']
        print(f"Slippage:         {res['slippage']:.4f} ({slippage_ticks:.1f} ticks)")
        print("-" * 50)