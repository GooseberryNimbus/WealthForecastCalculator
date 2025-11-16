import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- Full page layout ---
st.set_page_config(page_title="Wealth Forecast", layout="wide")

st.title("Wealth Forecast Calculator")

# --- Sidebar Controls ---
st.sidebar.header("Investment Settings")
interest = st.sidebar.slider("Annual interest rate (%)", 0.0, 20.0, 7.0) / 100
investment = st.sidebar.number_input("Monthly investment (€)", min_value=0, value=1000)
wealth_start = st.sidebar.number_input("Starting wealth (€)", min_value=0, value=3000)
year_start = st.sidebar.number_input("Start year", min_value=1900, max_value=3000, value=2026)
year_end = st.sidebar.number_input("End year", min_value=1900, max_value=3000, value=2069)

st.sidebar.markdown("### Set your own target(s)")
targets_input = st.sidebar.text_area(
    "Enter target values separated by commas (e.g., 100000, 250000, 500000)",
    value="100000"
)
try:
    targets = [float(t.strip()) for t in targets_input.split(",") if t.strip()]
except ValueError:
    st.sidebar.error("Please enter valid numbers separated by commas.")
    targets = []

# --- Calculations ---
growth = (1 + interest) ** (1 / 12) - 1
months = 12 * (year_end - year_start)
time = np.array([year_start + m / 12 for m in range(months)])

wealth = [wealth_start]
for _ in range(months - 1):
    wealth.append(wealth[-1] * (1 + growth) + investment)
wealth = np.array(wealth)

# --- Display Target Achievements First ---
if targets:
    st.markdown("### 🎯 Target Achievements")
    # --- Check for millionaire milestone ---
    millionaire_idx = np.argmax(wealth >= 1_000_000)
    if wealth[millionaire_idx] >= 1_000_000 and (year_start + millionaire_idx / 12) <= year_end:
        millionaire_year = year_start + millionaire_idx / 12
        st.success(f"💰 You will be a millionaire by the year {millionaire_year:.0f}!")
    target_years = []
    for i, target in enumerate(targets, start=1):
        reached_idx = np.argmax(wealth >= target)
        if wealth[reached_idx] >= target:
            year_reached = year_start + reached_idx / 12
            st.write(f"Target €{target:,.0f} reached in year {year_reached:.0f}")
            target_years.append((target, year_reached))
        else:
            st.write(f"Target €{target:,.0f} not reached by {year_end}")
            target_years.append((target, None))

# --- Graph Below with Header ---
st.markdown("### 📈 Wealth Forecast Graph")

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(time, wealth, label="Wealth Forecast", linewidth=2)
ax.plot(time, wealth_start + investment * np.arange(len(time)), label="Total Investment", linewidth=2)

# Plot targets as dashed lines
for i, target in enumerate(targets, start=1):
    ax.plot(time, [target] * len(time), linestyle="--", label=f"Target {i} (€{target:,.0f})")

ax.set_xlim(year_start, year_end)
ax.set_ylim(0, max(np.max(wealth), max(targets) if targets else 0, 1_000_000) * 1.1)
ax.set_xlabel("Year")
ax.set_ylabel("Accumulated Wealth (€)")
ax.set_title(
    f"Wealth forecast starting with €{wealth_start:,} in {year_start}, "
    f"monthly investment €{investment:,}, "
    f"annual interest rate {(interest * 100):.2f}%"
)
ax.legend()
ax.grid(True)

st.pyplot(fig)
