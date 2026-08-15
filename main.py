from trade_calculator import calculate_trade

trades = [
    {
        "symbol": "RELIANCE",
        "entry": 500,
        "stop_loss": 480,
        "target": 540
    },
    {
        "symbol": "TCS",
        "entry": 1000,
        "stop_loss": 960,
        "target": 1050
    },
    {
        "symbol": "INFY",
        "entry": 1500,
        "stop_loss": 1450,
        "target": 1600
    }
]


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