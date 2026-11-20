import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import db_manager as db  # Imported only once at the top!

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="AI Portfolio Optimizer", page_icon="🎯", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    h1, h2, h3 { color: #1e3d59; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .vault-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #6c5ce7;
        margin-top: 20px;
    }
    hr { margin-top: 2rem; margin-bottom: 2rem; border-top: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- SECURITY LOCK ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("🔒 **Access Denied:** Please log in from the Home Page to access this tool.")
    st.stop()

# ==========================================
# 2. HEADER & SIDEBAR INPUTS
# ==========================================
st.title("🎯 AI Portfolio Optimizer")
st.markdown("**Use Markowitz Modern Portfolio Theory to find your mathematically perfect asset allocation.**")

with st.sidebar:
    st.header("⚙️ Portfolio Settings")
    st.markdown("Select assets and timeframe to optimize.")
    
    with st.container():
        tickers_input = st.text_area("📈 Stock Tickers (Comma-separated)", "RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS", height=100)
        start_date = st.date_input("📅 Start Date", pd.to_datetime("2020-01-01"))
        end_date = st.date_input("📅 End Date", pd.to_datetime("today"))
    
    st.divider()
    st.caption("Powered by SciPy & yfinance")

tickers = [ticker.strip().upper() for ticker in tickers_input.split(',') if ticker.strip()]

if len(tickers) < 2:
    st.warning("⚠️ Please enter at least **TWO** valid stocks to optimize a portfolio.")
    st.stop()

# ==========================================
# 3. DATA FETCHING & MATH PREP
# ==========================================
@st.cache_data(ttl=3600)
def fetch_stock_data(tickers, start, end):
    try:
        data = yf.download(tickers, start=start, end=end, progress=False)['Close']
        if isinstance(data, pd.Series):
            data = data.to_frame(name=tickers[0])
        return data.dropna()
    except Exception as e:
        return None

with st.spinner('📡 Downloading market data and preparing mathematical models...'):
    data = fetch_stock_data(tickers, start_date, end_date)

if data is None or data.empty:
    st.error("🚨 No valid data found. Please check for typos in your ticker symbols.")
    st.stop()

# Calculate daily logarithmic returns
log_returns = np.log(data / data.shift(1)).dropna()

# ==========================================
# 4. DASHBOARD TABS
# ==========================================
tab1, tab2 = st.tabs(["🤖 AI Auto-Optimization", "⚖️ Manual Allocation"])

# ------------------------------------------
# TAB 1: ALGORITHMIC OPTIMIZATION
# ------------------------------------------
with tab1:
    st.subheader("Efficient Frontier Simulation")
    st.markdown("The AI is running **2,000 simulated portfolios** to find the maximum risk-adjusted return.")
    
    # Mathematical setup
    num_portfolios = 2000
    all_weights = np.zeros((num_portfolios, len(tickers)))
    ret_arr = np.zeros(num_portfolios)
    vol_arr = np.zeros(num_portfolios)
    sharpe_arr = np.zeros(num_portfolios)

    mean_returns = log_returns.mean()
    cov_matrix = log_returns.cov()

    # Run the simulation
    np.random.seed(42) # For consistent results during presentation
    for i in range(num_portfolios):
        weights = np.array(np.random.random(len(tickers)))
        weights = weights / np.sum(weights)
        all_weights[i,:] = weights
        
        ret_arr[i] = np.sum((mean_returns * weights) * 252)
        vol_arr[i] = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
        sharpe_arr[i] = ret_arr[i] / vol_arr[i]

    # Find the Golden Portfolio
    max_sharpe_idx = sharpe_arr.argmax()
    optimal_return = ret_arr[max_sharpe_idx]
    optimal_volatility = vol_arr[max_sharpe_idx]
    optimal_sharpe = sharpe_arr[max_sharpe_idx]
    optimal_weights = all_weights[max_sharpe_idx, :]

    # Results UI
    st.success("✅ **Optimization Complete!** Here is your mathematically optimal portfolio:")
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("Expected Annual Return", f"{optimal_return * 100:.2f}%", delta="Maximized")
    with metric_col2:
        st.metric("Expected Volatility (Risk)", f"{optimal_volatility * 100:.2f}%", delta="Minimized", delta_color="inverse")
    with metric_col3:
        st.metric("Max Sharpe Ratio", f"{optimal_sharpe:.2f}", delta="Optimal Score")

    st.divider()

    # Layout for Tables and Charts
    col_table, col_chart = st.columns([1, 1.8])
    
    with col_table:
        st.subheader("Optimal Weights")
        weight_df = pd.DataFrame({"Stock": tickers, "Allocation": optimal_weights * 100})
        
        # Styled dataframe for better looks
        st.dataframe(
            weight_df.style.format({"Allocation": "{:.2f}%"}),
            hide_index=True, use_container_width=True
        )
        
        # Pie chart
        fig_pie = px.pie(weight_df, values='Allocation', names='Stock', hole=0.4)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart:
        st.subheader("The Efficient Frontier")
        fig_frontier = go.Figure()
        
        # All simulated portfolios
        fig_frontier.add_trace(go.Scatter(
            x=vol_arr * 100, y=ret_arr * 100, mode='markers',
            marker=dict(color=sharpe_arr, colorscale='Viridis', showscale=True, size=6, colorbar=dict(title="Sharpe")),
            name='Simulations', text=[f"Sharpe: {s:.2f}" for s in sharpe_arr], hoverinfo="text+x+y"
        ))
        
        # Golden Portfolio (Red Star)
        fig_frontier.add_trace(go.Scatter(
            x=[optimal_volatility * 100], y=[optimal_return * 100], mode='markers',
            marker=dict(color='red', size=16, symbol='star', line=dict(color='black', width=1)),
            name='Optimal Portfolio', hoverinfo="x+y"
        ))

        fig_frontier.update_layout(
            xaxis_title="Risk (Annualized Volatility %)",
            yaxis_title="Return (Annualized %)",
            hovermode="closest",
            plot_bgcolor='white', paper_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#e0e0e0'),
            yaxis=dict(showgrid=True, gridcolor='#e0e0e0'),
            margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig_frontier, use_container_width=True)

# ------------------------------------------
# TAB 2: MANUAL ALLOCATION
# ------------------------------------------
with tab2:                                                                                                     
    st.subheader("⚖️ Manual Asset Allocation")
    st.markdown("Test your own strategies. Note: The system will automatically normalize your inputs to equal 100%.")
    
    weights_input = []
    
    # Dynamic columns based on number of tickers
    cols = st.columns(len(tickers))
    for i, t in enumerate(tickers):
        with cols[i]:
            w = st.number_input(f"{t} Weight", min_value=0.0, max_value=100.0, value=100.0/len(tickers), key=f"w_{t}")
            weights_input.append(w)

    total_weight = sum(weights_input)
    if total_weight == 0:
        st.error("Total weight cannot be zero!")
    else:
        manual_weights = np.array([w / total_weight for w in weights_input])
        
        port_return = np.sum((mean_returns * manual_weights) * 252)
        port_volatility = np.sqrt(np.dot(manual_weights.T, np.dot(cov_matrix * 252, manual_weights)))
        port_sharpe = port_return / port_volatility if port_volatility != 0 else 0
        
        st.write("") # Spacing
        c1, c2, c3 = st.columns(3)
        c1.metric("Manual Expected Return", f"{port_return * 100:.2f}%")
        c2.metric("Manual Volatility", f"{port_volatility * 100:.2f}%")
        
        # Color code Sharpe based on if it beats the AI or not
        sharpe_delta = port_sharpe - optimal_sharpe
        c3.metric("Manual Sharpe Ratio", f"{port_sharpe:.2f}", delta=f"{sharpe_delta:.2f} vs AI")
        
        if port_sharpe < optimal_sharpe:
            st.info(f"💡 **Notice:** The AI optimized portfolio achieves a mathematically higher Sharpe Ratio ({optimal_sharpe:.2f}) than your manual setup ({port_sharpe:.2f}).")
        else:
            st.success("🎉 Incredible! You manually found a portfolio allocation that matches or beats the current standard optimization!")

# ==========================================
# 5. SAVE TO VAULT FEATURE
# ==========================================
st.markdown("""
    <div class="vault-card">
        <h3>💾 Save to My Vault</h3>
        <p style='color: #6c757d;'>Save this group of stocks to your personal database to track later.</p>
    </div>
""", unsafe_allow_html=True)

col_name, col_btn = st.columns([3, 1])
with col_name:
    portfolio_name = st.text_input("Give this portfolio a name (e.g., 'Tech Growth', 'Safe Retirement')", label_visibility="collapsed", placeholder="Enter a name for this portfolio...")
with col_btn:
    if st.button("Save Portfolio", use_container_width=True, type="primary"):
        if portfolio_name:
            try:
                # Safely get username from session state, defaulting to 'Admin' if not set
                current_user = st.session_state.get("username", "Admin")
                db.add_portfolio(current_user, portfolio_name, tickers_input)
                st.success(f"✅ '{portfolio_name}' successfully saved to your Vault!")
            except Exception as e:
                st.error(f"Database Error: Could not save portfolio. Have you created the db_manager file? Details: {e}")
        else:
            st.warning("Please enter a name for the portfolio before saving.")