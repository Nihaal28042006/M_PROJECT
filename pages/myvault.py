import streamlit as st
import db_manager as db
import yfinance as yf
import pandas as pd

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS
# ==========================================
st.set_page_config(page_title="My Vault", page_icon="🏦", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    h1, h2, h3 { color: #1e3d59; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .vault-header {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #1f77b4;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- SECURITY LOCK ---
if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
    st.error("🔒 **Access Denied:** Please log in from the Home Page to access this tool.")
    st.stop()

# Safely get full username for Database operations
username = st.session_state.get('username', 'Investor')

# Create a clean display name (strips out @gmail.com and capitalizes)
display_name = username.split('@')[0].capitalize()

# ==========================================
# 2. MAIN HEADER
# ==========================================
st.markdown(f"""
    <div class="vault-header">
        <h1>🏦 {display_name}'s Wealth Vault</h1>
        <p style='color: #6c757d; font-size: 1.1rem; margin: 0;'>Track the live performance of your saved AI-optimized portfolios.</p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# 3. FETCH & DISPLAY PORTFOLIOS
# ==========================================
try:
    # Use the full email address 'username' here so the DB finds the correct records!
    saved_portfolios = db.get_portfolios(username)
except Exception as e:
    st.error(f"🚨 **Database Error:** Could not load portfolios. Make sure db_manager.py is working. Details: {e}")
    st.stop()

if not saved_portfolios:
    st.info("📭 **Your vault is empty.** Go to the **Portfolio Optimizer**, create a custom stock grouping, and click 'Save to Vault'.")
else:
    st.success(f"✅ You have **{len(saved_portfolios)}** saved portfolios in your vault.")
    st.divider()
    
    # Loop through each saved portfolio and display it
    for port in saved_portfolios:
        port_name = port[0]
        tickers_str = port[1]
        tickers_list = [t.strip().upper() for t in tickers_str.split(',') if t.strip()]
        
        # We start the expander collapsed so the UI isn't cluttered
        with st.expander(f"📂 {port_name} | Assets: {len(tickers_list)}", expanded=False):
            st.markdown(f"**Tracked Assets:** `{', '.join(tickers_list)}`")
            
            try:
                with st.spinner(f'Fetching live market prices for {port_name}...'):
                    # Get today's data safely
                    live_data = yf.download(tickers_list, period="1d", progress=False)['Close']
                    
                    if isinstance(live_data, pd.Series):
                        live_data = live_data.to_frame(name=tickers_list[0])
                        
                    # Handle recent yfinance multi-index changes automatically
                    if isinstance(live_data.columns, pd.MultiIndex):
                        live_data.columns = live_data.columns.droplevel(1)
                    
                    st.write("### Latest Market Prices")
                    
                    # Display prices as cool metric cards (Max 4 across the screen)
                    cols = st.columns(min(len(tickers_list), 4))
                    for idx, ticker in enumerate(tickers_list):
                        col = cols[idx % 4]
                        if ticker in live_data.columns:
                            price = float(live_data[ticker].iloc[-1])
                            col.metric(ticker, f"${price:,.2f}")
                        else:
                            col.metric(ticker, "N/A")

                    st.write("") # Spacing
                    st.divider()
                    
                    # Delete Button Layout
                    del_col1, del_col2 = st.columns([4, 1])
                    with del_col2:
                        if st.button(f"🗑️ Delete Portfolio", key=f"del_{port_name}", use_container_width=True):
                            db.delete_portfolio(username, port_name)
                            st.rerun()
                            
            except Exception as e:
                st.warning("⚠️ Could not fetch live prices right now. The market might be closed, or the tickers are invalid.")
                # Fallback delete button in case Yahoo Finance crashes
                if st.button(f"🗑️ Force Delete '{port_name}'", key=f"del_err_{port_name}"):
                    db.delete_portfolio(username, port_name)
                    st.rerun()