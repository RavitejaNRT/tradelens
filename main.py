entry_price = float(input("Enter entry price: "))
stop_loss = float(input("Enter stop loss: "))
target = float(input("Enter target: "))

risk = entry_price - stop_loss
reward = target - entry_price

risk_percent = (risk / entry_price) * 100
reward_percent = (reward / entry_price) * 100
risk_reward_ratio = reward / risk

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