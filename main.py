def calculate_trade(entry_price, stop_loss, target):
    risk = entry_price - stop_loss
    reward = target - entry_price

    risk_percent = (risk / entry_price) * 100
    reward_percent = (reward / entry_price) * 100
    risk_reward_ratio = reward / risk

    return risk, reward, risk_percent, reward_percent, risk_reward_ratio


entry_price = float(input("Enter entry price: "))
stop_loss = float(input("Enter stop loss: "))
target = float(input("Enter target: "))

if stop_loss >= entry_price:
    print("Invalid setup: stop loss must be below entry price.")
    exit()

if target <= entry_price:
    print("Invalid setup: target must be above entry price.")
    exit()

risk, reward, risk_percent, reward_percent, risk_reward_ratio = calculate_trade(
    entry_price, stop_loss, target
)

print("Entry price:", entry_price)
print("Stop loss:", stop_loss)
print("Target:", target)
print("Risk:", risk)
print("Reward:", reward)
print("Risk %:", risk_percent)
print("Reward %:", reward_percent)
print("Risk/Reward:", risk_reward_ratio)

if risk_reward_ratio >= 2:
    print("Trade setup is acceptable")
else:
    print("Trade setup is rejected")