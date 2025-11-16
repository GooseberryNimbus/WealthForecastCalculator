import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --- Full page layout ---
st.set_page_config(page_title="Wealth Forecast", layout="wide")
st.title("📈 Wealth Forecast Calculator")

# --- Sidebar Controls ---
st.sidebar.header("Investment Settings")

# --- Interest slider + text input side by side ---
col1, col2 = st.sidebar.columns([2, 1])
slider_interest = col1.slider("Annual interest rate (%)", 0.0, 20.0, 7.0)
typed_interest = col2.text_input("", value=f"{slider_interest}")

# Synchronize: typed input overrides slider if valid
try:
    interest = float(typed_interest) / 100
except ValueError:
    interest = slider_interest / 100  # fallback to slider

# Monthly investment and starting wealth with custom increments
investment = st.sidebar.number_input(
    "Monthly investment (€)", min_value=0, value=1000, step=50
)
wealth_start = st.sidebar.number_input(
    "Starting wealth (€)", min_value=0, value=3000, step=1000
)

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

# --- Display Target Achievements ---
if targets:
    st.markdown("### 🎯 Target Achievements")
    # Millionaire milestone
    millionaire_idx = np.argmax(wealth >= 1_000_000)
    if wealth[millionaire_idx] >= 1_000_000 and (year_start + millionaire_idx / 12) <= year_end:
        millionaire_year = year_start + millionaire_idx / 12
        st.success(f"💰 You will be a millionaire by year {millionaire_year:.0f}!")
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

# --- Graph ---
st.markdown("### 📈 Wealth Forecast Graph")

fig, ax = plt.subplots(figsize=(14, 6))

# Plot Wealth Forecast
ax.plot(time, wealth / 1e6, label="Wealth Forecast", color="#1f77b4", linewidth=3)

# Plot Total Contributions
ax.plot(time, (wealth_start + investment * np.arange(len(time))) / 1e6,
        label="Total Contributions", color="#ff7f0e", linewidth=2, linestyle="--")

# Plot targets
for i, target in enumerate(targets, start=1):
    ax.axhline(y=target / 1e6, linestyle="--", color="gray", linewidth=1.5,
               label=f"Target {i} (€{target:,.0f})")

# Highlight millionaire milestone
if wealth[millionaire_idx] >= 1_000_000:
    ax.scatter(year_start + millionaire_idx / 12, wealth[millionaire_idx] / 1e6,
               color="gold", s=100, zorder=5, label="Millionaire milestone")

# Format Y-axis in Millions
ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.0f}M'))

# Style improvements
ax.set_xlim(year_start, year_end)
ax.set_ylim(0, max(np.max(wealth), max(targets) if targets else 0, 1_000_000) / 1e6 * 1.1)
ax.set_xlabel("Year", fontsize=12, weight='bold')
ax.set_ylabel("Accumulated Wealth (€ Millions)", fontsize=12, weight='bold')
ax.set_title(f"Wealth Forecast with €{wealth_start:,} start, €{investment:,}/month, {interest*100:.2f}% annual interest",
             fontsize=14, weight='bold')

ax.grid(True, linestyle='--', alpha=0.5)
ax.legend(loc='upper left', fontsize=10, frameon=True, shadow=True)

st.pyplot(fig)
