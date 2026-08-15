from trade_calculator import calculate_trade
from trade_data import trades

for trade_input in trades:
    trade = calculate_trade(
        trade_input["entry"],
        trade_input["stop_loss"],
        trade_input["target"]
    )

    print(trade_input["symbol"])
    print("Risk %:", trade["risk_percent"])
    print("Reward %:", trade["reward_percent"])
    print("Risk/Reward:", trade["risk_reward_ratio"])

    if trade["risk_reward_ratio"] >= 2:
        print("Decision: ACCEPT")
    else:
        print("Decision: REJECT")

    print()