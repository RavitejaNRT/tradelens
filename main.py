def calculate_trade(entry_price, stop_loss, target):
    risk = entry_price - stop_loss
    reward = target - entry_price

    risk_percent = (risk / entry_price) * 100
    reward_percent = (reward / entry_price) * 100
    risk_reward_ratio = reward / risk

    return {
        "entry": entry_price,
        "stop_loss": stop_loss,
        "target": target,
        "risk": risk,
        "reward": reward,
        "risk_percent": risk_percent,
        "reward_percent": reward_percent,
        "risk_reward_ratio": risk_reward_ratio
    }


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