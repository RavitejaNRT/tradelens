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