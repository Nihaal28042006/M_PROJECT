import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (UI/UX)
# ==========================================
st.set_page_config(
    page_title="AI Price Predictor", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern, Clean UI
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f7f6;
    }
    h1, h2, h3 {
        color: #1e3d59;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .info-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        margin-bottom: 15px;
        border-left: 5px solid #1f77b4;
    }
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 0;
        border-top: 1px solid #e0e0e0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. SECURITY & STATE MANAGEMENT
# ==========================================
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("🔒 **Access Denied:** Please log in from the Home Page to access the AI modules.")
    st.stop()

# ==========================================
# 3. SIDEBAR NAVIGATION & INPUTS
# ==========================================
with st.sidebar:
    st.header("⚙️ ML Configuration")
    st.markdown("Customize your Machine Learning model.")
    
    with st.container():
        stock_symbol = st.text_input("📈 Stock Ticker Symbol", "AAPL", help="e.g., AAPL, TSLA, RELIANCE.NS").upper().strip()
        data_period = st.selectbox("📅 Historical Data Training Period", ["2y", "5y", "10y"], index=1)
        
        st.divider()
        st.markdown("**🔮 Future Forecasting**")
        # Added a slider so you can dynamically show 1 to 90 days in the presentation!
        forecast_days = st.slider("Days to Predict into Future", min_value=1, max_value=90, value=30)
    
    st.divider()
    st.caption("Powered by Scikit-Learn (Random Forest)")

if not stock_symbol:
    st.info("💡 Enter a ticker in the sidebar to train the AI.")
    st.stop()

# ==========================================
# 4. CORE MACHINE LEARNING (AUTOREGRESSIVE)
# ==========================================
@st.cache_data(ttl=3600)
def train_and_predict(ticker, period, future_days):
    try:
        # Fetch Data
        data = yf.download(ticker, period=period, progress=False)
        
        if data.empty:
            return "NO_DATA", None, None, None, None, None
            
        # Flatten multi-level columns if yfinance returns them
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        # Feature Engineering
        df = data[['Close', 'Volume']].copy()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Create Target Variable (Predicting NEXT day's close price)
        df['Target'] = df['Close'].shift(-1)
        
        # Save current state for future predictions
        current_price = float(df.iloc[-1]['Close'])
        
        # Drop NaNs to train the model
        train_df = df.dropna().copy()
        
        # Define Features (X) and Target (y)
        X = train_df[['Close', 'Volume', 'SMA_10', 'SMA_50']]
        y = train_df['Target']
        
        # Train-Test Split & Model Training
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate Accuracy
        test_predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, test_predictions)
        
        # --- AUTOREGRESSIVE FORECASTING LOOP (UP TO 90 DAYS) ---
        last_50_closes = df['Close'].dropna().tail(50).tolist()
        # Keep volume constant as a recent average to stabilize predictions
        avg_volume = float(df['Volume'].tail(10).mean()) 
        
        future_predictions = []
        
        # Generate future dates (Business days only, skipping weekends)
        last_date = df.index[-1]
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=future_days, freq='B')
        
        for _ in range(future_days):
            curr_close = last_50_closes[-1]
            sma_10 = sum(last_50_closes[-10:]) / 10
            sma_50 = sum(last_50_closes[-50:]) / 50
            
            # Create a DataFrame for the single prediction to avoid sklearn warnings
            next_features = pd.DataFrame([[curr_close, avg_volume, sma_10, sma_50]], 
                                         columns=['Close', 'Volume', 'SMA_10', 'SMA_50'])
            
            pred_close = float(model.predict(next_features)[0])
            future_predictions.append(pred_close)
            
            # Add predicted price to our list so the next loop can use it for moving averages!
            last_50_closes.append(pred_close)
            
        # Prepare historical data for the chart (last 120 days for a good view)
        chart_data = df.tail(120).copy()
        
        return df, current_price, future_dates, future_predictions, mae, chart_data
        
    except Exception as e:
        return f"ERROR: {str(e)}", None, None, None, None, None

# ==========================================
# 5. MAIN UI HEADER & DASHBOARD
# ==========================================
st.title(" AI Price Predictor (Machine Learning)")
st.markdown(f"**Random Forest Regressor forecasting {forecast_days} days into the future for `{stock_symbol}`**")

with st.spinner(f"🤖 Training Neural Trees & generating {forecast_days}-day forecast for {stock_symbol}..."):
    result = train_and_predict(stock_symbol, data_period, forecast_days)

# Error Handling
if isinstance(result[0], str):
    if result[0] == "NO_DATA":
        st.warning(f"⚠️ No data found for '{stock_symbol}'. Please check the ticker symbol.")
        st.stop()
    else:
        st.error(f"🚨 **System Crash:** {result[0]}")
        st.stop()

df, current_price, future_dates, future_predictions, mae, chart_data = result

# Calculations for UI based on the FINAL day of the forecast
final_future_price = future_predictions[-1]
price_difference = final_future_price - current_price
percent_change = (price_difference / current_price) * 100
trend = "🟢 UPWARD" if price_difference > 0 else "🔴 DOWNWARD"
delta_color = "normal" if price_difference > 0 else "inverse"

# ==========================================
# 6. RESULTS & VISUALIZATIONS
# ==========================================
tab1, tab2 = st.tabs(["📊 Prediction Dashboard", "⚙️ Model Analytics"])

with tab1:
    # Top Metrics Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Closing Price", f"${current_price:.2f}")
    with col2:
        st.metric(
            f"AI Target Price (Day {forecast_days})", 
            f"${final_future_price:.2f}", 
            f"{percent_change:.2f}% (${price_difference:.2f})"
        )
    with col3:
        st.metric(f"{forecast_days}-Day Trend", trend)

    st.divider()

    # Interactive Plotly Chart
    st.subheader("Historical Action vs. AI Future Forecast")
    
    fig = go.Figure()
    
    # 1. Historical Close Prices
    fig.add_trace(go.Scatter(
        x=chart_data.index, y=chart_data['Close'],
        mode='lines', name='Historical Close',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 2. Historical SMA 50
    fig.add_trace(go.Scatter(
        x=chart_data.index, y=chart_data['SMA_50'],
        mode='lines', name='50-Day Moving Avg',
        line=dict(color='#ff7f0e', width=1.5, dash='dot')
    ))
    
    # 3. FUTURE PREDICTION LINE (The 90-day forecast!)
    # We connect the last known price to the start of the prediction array so the line doesn't break
    connect_date = [chart_data.index[-1]] + list(future_dates)
    connect_price = [current_price] + future_predictions

    fig.add_trace(go.Scatter(
        x=connect_date, y=connect_price,
        mode='lines', name=f'{forecast_days}-Day AI Forecast',
        line=dict(color='#2ca02c' if price_difference > 0 else '#d62728', width=3, dash='dash')
    ))

    # Add a marker at the very end of the prediction
    fig.add_trace(go.Scatter(
        x=[future_dates[-1]], y=[final_future_price],
        mode='markers+text', name='Final Target',
        marker=dict(color='gold', size=12, symbol='star', line=dict(color='black', width=1)),
        text=[f"${final_future_price:.2f}"],
        textposition="top center"
    ))

    fig.update_layout(
        hovermode="x unified",
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#e0e0e0', title="Date"),
        yaxis=dict(showgrid=True, gridcolor='#e0e0e0', title="Stock Price (USD)"),
        height=500, margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Model Performance & Future Target Data")
    
    st.markdown(f"""
    <div class="info-card">
        <h4>Model Accuracy (Mean Absolute Error)</h4>
        <p>The AI's historical average error is <b>${mae:.2f}</b> per share on 1-day predictions. 
        <i>Note: The further out the AI predicts (like 90 days), the wider the margin of error becomes due to unforeseen market events.</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a nice dataframe to show the exact future prices
    future_df = pd.DataFrame({
        "Date": future_dates,
        "Predicted Price (USD)": np.round(future_predictions, 2)
    })
    future_df.set_index("Date", inplace=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🔮 Predicted Future Prices")
        st.dataframe(future_df, use_container_width=True)
    with col2:
        st.subheader("📂 Raw Historical Dataset")
        st.dataframe(df.tail(30), use_container_width=True)