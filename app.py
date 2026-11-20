import streamlit as st
import db_manager as db

# Page Configuration must be the first Streamlit command
st.set_page_config(page_title="Wealth Dashboard", layout="centered", page_icon="🔐")

# --- CUSTOM FRONTEND DESIGN (CSS) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Center the Login Card */
    .login-card {
        background: white;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0px 10px 25px rgba(0, 0, 0, 0.05);
        border: 1px solid #f1f5f9;
        margin-top: 20px;
    }

    /* Style the buttons */
    div.stButton > button:first-child {
        background-color: #0f172a;
        color: white;
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    div.stButton > button:first-child:hover {
        background-color: #3b82f6;
        border: none;
        color: white;
        box-shadow: 0px 4px 12px rgba(59, 130, 246, 0.3);
    }

    /* Input field borders and focus */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        padding: 10px 15px;
    }
    
    .stTextInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
    }
    
    /* Titles and text */
    h1, h2, h3 {
        color: #0f172a;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    p {
        color: #475569;
    }
</style>
""", unsafe_allow_html=True)

# Initialize the database tables
db.create_usertable()
db.create_portfoliotable()

# Create a session state variable to track login status
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIN / SIGNUP INTERFACE ---
if not st.session_state["logged_in"]:
    # Wrap login section in a custom styled div
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    
    st.title("Wealth Manager")
    st.markdown("Access your institutional-grade financial toolkit.")
    st.write("") # Spacing
    
    # Use tabs instead of a selectbox for a cleaner UI
    tab_login, tab_signup = st.tabs(["Sign In", "Create Account"])

    # Login Tab
    with tab_login:
        username = st.text_input("Username", placeholder="Enter your username", key="login_user")
        password = st.text_input("Password", type='password', placeholder="Enter your password", key="login_pass")
        
        st.write("") # Spacing
        if st.button("Sign In"):
            result = db.login_user(username, password)
            if result:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.success("Authentication successful. Redirecting...")
                st.rerun()
            else:
                st.error("⚠️ Invalid credentials. Please try again.")

    # Sign Up Tab
    with tab_signup:
        new_user = st.text_input("Create Username", placeholder="Choose a unique username", key="reg_user")
        new_password = st.text_input("Create Password", type='password', placeholder="Use a strong password", key="reg_pass")
        
        st.write("") # Spacing
        if st.button("Register Account"):
            if new_user and new_password:
                db.add_userdata(new_user, new_password)
                st.success("✅ Account registered! You can now sign in from the 'Sign In' tab.")
            else:
                st.warning("Please fill in both fields to continue.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- POST-LOGIN DASHBOARD ---
else:
    # Sidebar features for logged-in user
    with st.sidebar:
        st.subheader("Account Settings")
        st.write(f"👤 **{st.session_state['username']}**")
        st.divider()
        if st.button("Secure Logout"):
            st.session_state["logged_in"] = False
            st.rerun()

    # Main Dashboard Content
    st.title("Financial Command Center")
    st.info(f"Welcome back, {st.session_state['username']}! Your session is secure.")
    
    st.divider()
    
    # Use columns to neatly organize the dashboard instructions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ###  Portfolio Analytics
        Manage risk and optimize your asset distribution using real-time market simulations. Access this via the sidebar to find your Efficient Frontier.
        """)
        
    with col2:
        st.markdown("""
        ### ⏳ Wealth Projection
        Use the SIP simulator to model long-term growth. Project future wealth based on real historical data and compound interest.
        """)