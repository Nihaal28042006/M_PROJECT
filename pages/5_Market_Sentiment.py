import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import urllib.request
import xml.etree.ElementTree as ET

# ==========================================
# 1. PAGE CONFIG & CUSTOM CSS (UI/UX)
# ==========================================
st.set_page_config(
    page_title="Market Sentiment AI", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern, Clean UI
st.markdown("""
    <style>
    /* Background and typography */
    .stApp {
        background-color: #f4f7f6;
    }
    h1, h2, h3 {
        color: #1e3d59;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Custom News Card Styling */
    .news-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.04);
        margin-bottom: 15px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border-left: 5px solid #d3d3d3;
    }
    .news-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    .news-card a {
        text-decoration: none;
        color: #2b2b2b;
        font-size: 1.15rem;
        font-weight: 600;
    }
    .news-card a:hover {
        color: #1f77b4;
    }
    .news-meta {
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 8px;
    }
    
    /* Sentiment Border Colors */
    .card-bullish { border-left-color: #00b894; } /* Soft Green */
    .card-bearish { border-left-color: #d63031; } /* Soft Red */
    .card-neutral { border-left-color: #636e72; } /* Soft Grey */
    
    /* Divider */
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
    st.header("⚙️ AI Configuration")
    st.markdown("Customize your NLP engine settings below.")
    
    # Modern input grouping
    with st.container():
        stock_symbol = st.text_input("📈 Stock Ticker Symbol", "AAPL", help="Enter a valid ticker like TSLA, MSFT, or RELIANCE.NS").upper().strip()
    
    st.divider()
    st.caption("Powered by VADER NLP & Google RSS")

# ==========================================
# 4. CORE LOGIC (UNCHANGED)
# ==========================================
analyzer = SentimentIntensityAnalyzer()

@st.cache_data(ttl=1800)
def get_news_and_sentiment(ticker):
    if not ticker: return None, None
    try:
        url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        
        analyzed_news = []
        total_score = 0
        valid_articles = 0
        
        for item in root.findall('.//item')[:15]: 
            title = item.find('title').text
            link = item.find('link').text
            
            if " - " in title:
                headline, publisher = title.rsplit(" - ", 1)
            else:
                headline = title; publisher = "News Source"
            
            sentiment = analyzer.polarity_scores(headline)
            compound_score = sentiment['compound'] 
            total_score += compound_score
            valid_articles += 1
            
            # Categorize for CSS classes
            if compound_score >= 0.05:
                label, css_class = "🟢 Bullish", "card-bullish"
            elif compound_score <= -0.05:
                label, css_class = "🔴 Bearish", "card-bearish"
            else:
                label, css_class = "⚪ Neutral", "card-neutral"
                
            analyzed_news.append({
                "Headline": headline, "Publisher": publisher,
                "Sentiment": label, "Score": compound_score,
                "Link": link, "CSS_Class": css_class
            })
            
        if valid_articles == 0: return "NO_NEWS", None
        return pd.DataFrame(analyzed_news), (total_score / valid_articles)
    except Exception as e:
        return f"CRASH_DETAILS: {str(e)}", None

if not stock_symbol:
    st.info("💡 Enter a ticker in the sidebar to begin analysis.")
    st.stop()

# ==========================================
# 5. MAIN UI HEADER & DASHBOARD
# ==========================================
st.title("🧠 Live Market Sentiment Intelligence")
st.markdown(f"**Real-time Natural Language Processing for `{stock_symbol}`**")

with st.spinner(f"📡 AI is scanning global news networks for {stock_symbol}..."):
    news_df, overall_sentiment = get_news_and_sentiment(stock_symbol)

# Error Handling UI
if isinstance(news_df, str):
    if news_df == "NO_NEWS":
        st.warning(f"⚠️ No recent news articles found for '{stock_symbol}'. Try another ticker.")
        st.stop()
    elif news_df.startswith("CRASH_DETAILS"):
        st.error(f"🚨 **Network Alert:** Unable to fetch live data. Please check your internet or mobile hotspot.\n\n`{news_df}`")
        st.stop()
elif news_df is None:
    st.stop()

# ==========================================
# 6. RESULTS & VISUALIZATIONS
# ==========================================

# Using Tabs for better content organization
tab1, tab2 = st.tabs(["📊 Dashboard Overview", "📂 Raw NLP Data"])

with tab1:
    # Top Metrics Row
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    
    with metric_col1:
        st.metric(label="Articles Analyzed", value=len(news_df), delta="Live Feed")
    with metric_col2:
        # Determine overall trend for metric
        trend = "Bullish" if overall_sentiment >= 0.05 else "Bearish" if overall_sentiment <= -0.05 else "Neutral"
        delta_color = "normal" if trend == "Bullish" else "inverse" if trend == "Bearish" else "off"
        st.metric(label="Overall Market Mood", value=trend, delta=f"{overall_sentiment:.2f} Score", delta_color=delta_color)
    with metric_col3:
        bullish_count = len(news_df[news_df['Sentiment'] == '🟢 Bullish'])
        st.metric(label="Bullish Articles", value=bullish_count)

    st.divider()

    # Main Dashboard Columns
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("📰 Live News Feed")
        # Displaying Custom CSS Cards
        for _, row in news_df.iterrows():
            st.markdown(f"""
                <div class="news-card {row['CSS_Class']}">
                    <a href="{row['Link']}" target="_blank">{row['Headline']}</a>
                    <div class="news-meta">
                        🏢 <b>{row['Publisher']}</b> &nbsp; | &nbsp; {row['Sentiment']} (Score: {row['Score']:.2f})
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with col2:
        st.subheader("🧭 Sentiment Thermometer")
        # Plotly Gauge Chart in a container
        with st.container():
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = overall_sentiment,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [-1, 1], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': "rgba(0,0,0,0.5)"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [-1, -0.05], 'color': "#ff7675"}, # Soft Red
                        {'range': [-0.05, 0.05], 'color': "#dfe6e9"}, # Soft Grey
                        {'range': [0.05, 1], 'color': "#55efc4"}     # Soft Green
                    ]
                }
            ))
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
        with st.expander("ℹ️ How to read this chart?"):
            st.write("""
            * **Green Zone (0.05 to 1.0):** The AI detects positive words. The market is feeling optimistic (Bullish).
            * **Red Zone (-1.0 to -0.05):** The AI detects negative words. The market is feeling pessimistic (Bearish).
            * **Grey Zone (-0.05 to 0.05):** The news is purely factual with no strong emotion (Neutral).
            """)

with tab2:
    st.subheader("Raw Data Output")
    st.markdown("Below is the structured DataFrame output from the NLP engine.")
    # Display dataframe without the HTML/CSS class column for cleaner viewing
    display_df = news_df.drop(columns=['CSS_Class'])
    st.dataframe(display_df, use_container_width=True)