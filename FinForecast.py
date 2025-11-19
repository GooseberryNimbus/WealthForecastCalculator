import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- Full page layout ---
st.set_page_config(page_title="Wealth Forecast", layout="wide")
st.title("Wealth Forecast Calculator")

# --- Sidebar Controls ---
st.sidebar.header("Investment Settings")

# --- Interest slider + text input side by side ---
col1, col2 = st.sidebar.columns([2, 1])
slider_interest = col1.slider("Annual interest rate (%)", 0.0, 20.0, 7.0)
typed_interest = col2.text_input("", value=f"{slider_interest}")

try:
    interest = float(typed_interest) / 100
except ValueError:
    interest = slider_interest / 100

# Monthly investment + starting wealth
investment = st.sidebar.number_input(
    "Monthly investment (€)", min_value=0, value=1000, step=50
)
wealth_start = st.sidebar.number_input(
    "Starting wealth (€)", min_value=0, value=3000, step=1000
)

# Fiscal partner checkbox
col_start, col_end = st.sidebar.columns(2)
model_tax = col_start.checkbox("Vermogens belasting", value=True)
has_partner = col_end.checkbox("Fiscaal partner", value=True)

# Year range
col_start, col_end = st.sidebar.columns(2)
year_start = col_start.number_input("Start year", min_value=1900, max_value=3000, value=2026)
year_end = col_end.number_input("End year", min_value=1900, max_value=3000, value=2069)

# Hypotheek
hypotheek_start = st.sidebar.number_input(
    "Hypotheek (€)", min_value=0, value=400000, step=50000
)
hypotheek_rente = st.sidebar.number_input(
    "HypotheekRente (%)", min_value=0.0, value=4.0, step=0.1
)
hypotheek_rente = hypotheek_rente / 100
maandsom = hypotheek_start * hypotheek_rente / 12 * (1 + hypotheek_rente / 12) ** (30 * 12) / ((1 + hypotheek_rente / 12) ** (30 * 12) - 1)
hypotheek_aflossing = st.sidebar.number_input(
    "Aflossing (€)", min_value=int(maandsom), value=int(maandsom), step=100
)

# Targets
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
tax_threshold = 300 if has_partner else 150

time = np.array([year_start + m / 12 for m in range(months)])
tax_rate = 0.36 if model_tax else 0.0
wealth = [wealth_start]
for _ in range(months - 1):
    gross_add = wealth[-1] * growth
    net_add = min(gross_add, tax_threshold) + np.max(gross_add - tax_threshold, 0) * (1-tax_rate)  # 36% tax
    wealth.append(wealth[-1] + net_add + investment)
wealth = np.array(wealth)

contributions = wealth_start + investment * np.arange(months)

# --- Mortgage Model (Hypotheek) ---
mortgage_months = 30 * 12          # 30-year mortgage
monthly_rate = hypotheek_rente / 12

hypotheek = np.zeros(months)
aflossing = np.zeros(months)
rente = np.zeros(months)

remaining = hypotheek_start

for m in range(months):
    if remaining > 0:
        # Interest this month
        interest_payment = 120 + (remaining * monthly_rate - 120) * 0.63 # hypotheekrenteaftrek 
        
        # Principal paid off
        principal_payment = hypotheek_aflossing - remaining * monthly_rate
        
        # Prevent paying more principal than remaining mortgage
        principal_payment = min(principal_payment, remaining)
        
        remaining -= principal_payment
        
        hypotheek[m] = remaining
        aflossing[m] = m * hypotheek_aflossing
        rente[m] = interest_payment
    else:
        # Mortgage paid off: just keep 0 balance and repeat last aflossing amount
        hypotheek[m] = 0
        aflossing[m] = np.max(aflossing)
        rente[m] = 0
rente = np.cumsum(rente)


# --- Display Target Achievements ---
if targets:
    st.markdown("### 🎯 Target Achievements")

    # Millionaire milestone
    millionaire_idx = np.argmax(wealth >= 1_000_000)
    if wealth[millionaire_idx] >= 1_000_000:
        millionaire_year = year_start + millionaire_idx / 12
        st.success(f"💰 You will be a millionaire by {millionaire_year:.0f}!")

    # Custom targets
    for i, target in enumerate(targets, start=1):
        idx = np.argmax(wealth >= target)
        if wealth[idx] >= target:
            year_reached = year_start + idx / 12
            st.write(f"Target €{target:,.0f} reached in year {year_reached:.0f}")
        else:
            st.write(f"Target €{target:,.0f} not reached by {year_end}")

# --- Plotly Graph ---
st.markdown("### 📈 Vermogens Forecast")

fig = go.Figure()

# Wealth Forecast Line with final marker
fig.add_trace(go.Scatter(
    x=time,
    y=wealth / 1e6,
    name="Wealth Forecast",
    mode="lines+markers+text",          # add markers and text
    line=dict(color="#1f77b4", width=3),
    marker=dict(size=[0]*(len(wealth)-1) + [12], color="#1f77b4"),  # only final marker
    text=[None]*(len(wealth)-1) + [f"{wealth[-1]/1e6:.2f}M"],      # only final text
    textposition="middle right",
    hovertemplate="Year: %{x:.0f}<br>Wealth: €%{y:.2f}M"
))

# Total Contributions Line with final marker
fig.add_trace(go.Scatter(
    x=time,
    y=contributions / 1e6,
    name="Total Contributions",
    mode="lines+markers+text",
    line=dict(color="#ff7f0e", width=2, dash="dash"),
    marker=dict(size=[0]*(len(contributions)-1) + [12], color="#ff7f0e"),
    text=[None]*(len(contributions)-1) + [f"{contributions[-1]/1e6:.2f}M"],
    textposition="middle right",
    hovertemplate="Year: %{x:.0f}<br>Total Contributions: €%{y:.2f}M"
))

# Hypotheek line
fig.add_trace(go.Scatter(
    x=time,
    y=hypotheek / 1e6,
    name="Restschuld Hypotheek",
    line=dict(color="#a51fb4", width=2),
    hovertemplate="Year: %{x:.0f}<br>Hypotheek: €%{y:.2f}M"
))

fig.add_trace(go.Scatter(
    x=time,
    y=rente / 1e6,
    name="Hypotheek Rente",
    mode="lines+markers+text",
    line=dict(color="#ff0e0e", width=2, dash="dash"),
    marker=dict(size=[0]*(len(rente)-1) + [12], color="#ff0e0e"),
    text=[None]*(len(rente)-1) + [f"{rente[-1]/1e6:.2f}M"],
    textposition="middle right",
    hovertemplate="Year: %{x:.0f}<br>Total Rente: €%{y:.2f}M"
))

# Target lines
for i, target in enumerate(targets, start=1):
    fig.add_trace(go.Scatter(
        x=[time[0], time[-1]],
        y=[target / 1e6, target / 1e6],
        mode="lines",
        name=f"Target {i} (€{target:,.0f})",
        line=dict(color="gray", dash="dot")
    ))

# Millionaire milestone
millionaire_idx = np.argmax(wealth >= 1_000_000)
if wealth[millionaire_idx] >= 1_000_000:
    fig.add_trace(go.Scatter(
        x=[year_start + millionaire_idx / 12],
        y=[wealth[millionaire_idx] / 1e6],
        mode="markers",
        marker=dict(size=14, color="gold", symbol="star"),
        name="Millionaire milestone"
    ))

# Layout
fig.update_layout(
    height=550,
    xaxis_title="Year",
    yaxis_title="Accumulated Wealth (€ Millions)",
    title=f"Wealth Forecast with €{wealth_start:,} start, €{investment:,}/month, {interest*100:.2f}% annual interest",
    hovermode="closest",
    template="plotly_white",
    legend=dict(
        orientation="h",
        x=0,
        y=1.1,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="lightgray",
        borderwidth=1,
    )
)

# Y-axis formatting
#fig.update_yaxes(tickformat=".1f")

st.plotly_chart(fig, use_container_width=True)
