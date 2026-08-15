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


entry_price = float(input("Enter entry price: "))
stop_loss = float(input("Enter stop loss: "))
target = float(input("Enter target: "))

if stop_loss >= entry_price:
    print("Invalid setup: stop loss must be below entry price.")
    exit()

if target <= entry_price:
    print("Invalid setup: target must be above entry price.")
    exit()

trade = calculate_trade(entry_price, stop_loss, target)

print("Entry price:", trade["entry"])
print("Stop loss:", trade["stop_loss"])
print("Target:", trade["target"])
print("Risk:", trade["risk"])
print("Reward:", trade["reward"])
print("Risk %:", trade["risk_percent"])
print("Reward %:", trade["reward_percent"])
print("Risk/Reward:", trade["risk_reward_ratio"])

if trade["risk_reward_ratio"] >= 2:
    print("Trade setup is acceptable")
else:
    print("Trade setup is rejected")