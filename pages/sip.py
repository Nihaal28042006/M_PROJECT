import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# ==========================================
# 1. PAGE CONFIGURATION & CUSTOM CSS
# ==========================================
# UI Improvement: Added a relevant page icon and kept the wide layout for better data visualization.
st.set_page_config(page_title="Monte Carlo SIP", page_icon="🎲", layout="wide")

# UI Improvement: Injected custom CSS to create modern styling, rounded corners, soft shadows, 
# and a professional card-like appearance for metrics.
custom_css = """
<style>
    /* Main background and typography adjustments */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Styling metric containers to look like modern UI cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e6ed;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
    
    /* Hover effect for metric cards */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }

    /* Dark mode compatibility for cards */
    @media (prefers-color-scheme: dark) {
        div[data-testid="metric-container"] {
            background-color: #1e2127;
            border: 1px solid #2d333b;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }
    }

    /* Subtitle text styling */
    .subtitle-text {
        color: #6b7280;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- SECURITY LOCK ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.warning("🔒 Please log in from the Home Page to access this tool.")
    st.stop()

# ==========================================
# 2. HEADER SECTION
# ==========================================
# UI Improvement: Clean header with a distinct, muted subtitle for a professional look.
st.title("🎲 Monte Carlo SIP Simulator")
st.markdown('<p class="subtitle-text">Simulate 1,000 parallel market realities to forecast your future wealth with stochastic modeling.</p>', unsafe_allow_html=True)

# ==========================================
# 3. SIDEBAR CONFIGURATION (INPUTS)
# ==========================================
# UI Improvement: Structured sidebar with clear sections, dividers, and intuitive groupings.
with st.sidebar:
    st.header("⚙️ Simulation Settings")
    st.markdown("Configure your asset and investment strategy below.")
    st.divider()
    
    st.subheader("📈 Asset Details")
    stock_symbol = st.text_input("Stock Ticker (e.g., RELIANCE.NS, SPY)", "RELIANCE.NS").upper()
    
    st.divider()
    st.subheader("💰 Investment Plan")
    sip_type = st.radio("SIP Type", ["Standard SIP", "Step-Up SIP"], index=0)
    
    col_inv1, col_inv2 = st.columns(2)
    with col_inv1:
        monthly_investment = st.number_input("Starting SIP (₹)", min_value=500, value=5000, step=500)
    with col_inv2:
        years = st.number_input("Duration (Yrs)", min_value=1, value=10, step=1)

    step_up_percent = 0
    if sip_type == "Step-Up SIP":
        step_up_percent = st.slider("Annual Step-Up (%)", min_value=1, max_value=50, value=10, step=1)
    
    st.divider()
    st.info("💡 **Tip:** Step-Up SIPs account for annual salary increases to maximize long-term compounding.")

# ==========================================
# 4. CORE LOGIC (DATA FETCH & SIMULATION)
# ==========================================
# Code Constraint Maintained: Untouched underlying logic for fetching and calculating.
@st.cache_data(ttl=3600)
def get_historical_stats(symbol):
    data = yf.Ticker(symbol).history(period="10y")
    if len(data) < 252:
        return None, None
    
    data.index = pd.to_datetime(data.index)
    monthly_data = data['Close'].resample('M').last()
    monthly_returns = monthly_data.pct_change().dropna()
    
    mu = monthly_returns.mean()
    sigma = monthly_returns.std()
    return mu, sigma

# UI Improvement: Using a friendly spinner while fetching data.
with st.spinner(f"Analyzing 10-year historical volatility for {stock_symbol}..."):
    mu, sigma = get_historical_stats(stock_symbol)

if mu is None or sigma is None:
    st.error(f"⚠️ Not enough historical data found for '{stock_symbol}'. Please try another ticker.")
    st.stop()

# --- MONTE CARLO SIMULATION MATH ---
months = years * 12
num_simulations = 1000

np.random.seed(42)
random_returns = np.random.normal(mu, sigma, (months, num_simulations))

portfolio_simulations = np.zeros((months, num_simulations))
invested_amounts = np.zeros(months)

current_investment = monthly_investment
total_invested = 0

for m in range(months):
    total_invested += current_investment
    invested_amounts[m] = total_invested
    
    if m == 0:
        portfolio_simulations[m] = current_investment * (1 + random_returns[m])
    else:
        portfolio_simulations[m] = (portfolio_simulations[m-1] + current_investment) * (1 + random_returns[m])
        
    if sip_type == "Step-Up SIP" and (m + 1) % 12 == 0:
        current_investment += current_investment * (step_up_percent / 100)

final_wealths = portfolio_simulations[-1, :]

worst_case = np.percentile(final_wealths, 10)
expected_case = np.percentile(final_wealths, 50)
best_case = np.percentile(final_wealths, 90)

worst_path = portfolio_simulations[:, np.abs(final_wealths - worst_case).argmin()]
expected_path = portfolio_simulations[:, np.abs(final_wealths - expected_case).argmin()]
best_path = portfolio_simulations[:, np.abs(final_wealths - best_case).argmin()]

# ==========================================
# 5. DASHBOARD & VISUALIZATION (RESULTS)
# ==========================================
st.success(f"✅ Successfully ran **1,000 market realities** for **{stock_symbol}**.")

# UI Improvement: Grouped metrics into well-spaced columns. CSS at the top handles the "Card" aesthetics.
st.subheader("📊 Projected Wealth Outcomes", divider="gray")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Invested", f"₹ {total_invested:,.0f}", delta="Guaranteed", delta_color="off")
m2.metric("Worst Case (10th %ile)", f"₹ {worst_case:,.0f}", delta="Bear Market", delta_color="inverse")
m3.metric("Expected (50th %ile)", f"₹ {expected_case:,.0f}", delta="Average Market")
m4.metric("Best Case (90th %ile)", f"₹ {best_case:,.0f}", delta="Bull Market")

st.write("") # Spacer

# UI Improvement: Using Tabs to separate the primary chart from educational/technical details.
tab1, tab2 = st.tabs(["📈 Wealth Trajectory Forecast", "🔬 Simulation Insights"])

with tab1:
    # UI Improvement: Refined Plotly layout. Added fill to zero for a modern area-chart feel, 
    # unified hover templates, and polished color schemes.
    fig = go.Figure()

    # Plot Total Invested (Base Line)
    fig.add_trace(go.Scatter(
        x=list(range(1, months + 1)), y=invested_amounts, 
        mode='lines', name='Total Invested', 
        line=dict(color='#8c8c8c', width=3, dash='dash')
    ))

    # Plot Worst Case
    fig.add_trace(go.Scatter(
        x=list(range(1, months + 1)), y=worst_path, 
        mode='lines', name='Worst Case (10th %ile)', 
        line=dict(color='#ff4b4b', width=2)
    ))

    # Plot Expected Case
    fig.add_trace(go.Scatter(
        x=list(range(1, months + 1)), y=expected_path, 
        mode='lines', name='Expected Case (Median)', 
        line=dict(color='#1f77b4', width=3),
        fill='tonexty', fillcolor='rgba(31, 119, 180, 0.1)' # Soft fill for visual weight
    ))

    # Plot Best Case
    fig.add_trace(go.Scatter(
        x=list(range(1, months + 1)), y=best_path, 
        mode='lines', name='Best Case (90th %ile)', 
        line=dict(color='#00cc96', width=2),
        fill='tonexty', fillcolor='rgba(0, 204, 150, 0.05)' # Soft fill
    ))

    # UI Improvement: Minimalist axes, transparent background, and interactive legend
    fig.update_layout(
        xaxis_title="Investment Duration (Months)",
        yaxis_title="Portfolio Value (₹)",
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02, 
            xanchor="right", x=1
        ),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)', tickformat=",.0f")
    )

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # UI Improvement: Using expanders to tuck away technical data, keeping the main UI clean.
    st.markdown("### How to read this data")
    st.write(
        "A Monte Carlo simulation does not predict the exact future. Instead, it uses the "
        "historical mathematical properties of the chosen asset (mean return and volatility) to "
        "roll the dice thousands of times. This helps us understand the *probability* of different outcomes."
    )
    
    with st.expander("🔍 View Technical Parameters"):
        st.write(f"- **Asset Analyzed:** {stock_symbol}")
        st.write(f"- **Historical Monthly Mean Return (μ):** {mu:.4f} ({(mu*100):.2f}%)")
        st.write(f"- **Historical Monthly Volatility (σ):** {sigma:.4f} ({(sigma*100):.2f}%)")
        st.write(f"- **Total Simulations Run:** {num_simulations:,}")
        st.write(f"- **Simulated Timeframe:** {months} months")