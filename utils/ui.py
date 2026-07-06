
import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
            :root {
                --primary-color: #4CAF50;
                --secondary-color: #2196F3;
                --background-light: #f8fafc;
                --card-shadow: 0 1px 3px rgba(0,0,0,0.1);
                --text-color: #1e293b;
                --text-muted: #64748b;
            }
            
            /* Global container adjustments for reduced scrolling */
            .main .block-container {
                padding-top: 1.5rem !important;
                padding-bottom: 2rem !important;
                max-width: 1200px;
            }
            
            /* Compact headers */
            h1 {
                font-size: 1.8rem !important;
                padding-bottom: 0.5rem !important;
                margin-bottom: 1rem !important;
                font-weight: 700 !important;
            }
            h2 {
                font-size: 1.4rem !important;
                padding-top: 0.5rem !important;
                margin-bottom: 0.5rem !important;
                font-weight: 600 !important;
            }
            h3 {
                font-size: 1.1rem !important;
                padding-top: 0.2rem !important;
                margin-bottom: 0.4rem !important;
                font-weight: 600 !important;
            }
            
            /* Card styling for unified look */
            .stCard {
                background: white;
                padding: 1rem;
                border-radius: 0.5rem;
                box-shadow: var(--card-shadow);
                border: 1px solid #e2e8f0;
                margin-bottom: 0.5rem;
            }
            
            /* Metric compacting */
            div[data-testid="stMetric"] {
                background-color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            }
            div[data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;
                color: var(--text-muted) !important;
            }
            div[data-testid="stMetricValue"] {
                font-size: 1.4rem !important;
                font-weight: 600 !important;
            }
            
            /* Button styling */
            .stButton button {
                border-radius: 6px;
                font-weight: 500;
                height: auto;
                padding-top: 0.4rem;
                padding-bottom: 0.4rem;
                transition: all 0.2s;
            }
            .stButton button:hover {
                transform: translateY(-1px);
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            /* Sidebar compacting */
            section[data-testid="stSidebar"] .block-container {
                padding-top: 2rem !important;
                padding-bottom: 1rem !important;
            }
            
            /* Expander compacting */
            .streamlit-expanderHeader {
                background-color: #f8fafc;
                border-radius: 6px;
                padding-top: 0.4rem !important;
                padding-bottom: 0.4rem !important;
                font-size: 0.95rem;
                border: 1px solid #e2e8f0;
            }
            
            /* Input fields compacting */
            .stTextInput > div > div > input {
                padding-top: 0.3rem;
                padding-bottom: 0.3rem;
                min-height: 2.2rem;
            }
            .stSelectbox > div > div > div {
                min-height: 2.2rem;
            }
            
            /* Radio button spacing */
            .stRadio > div {
                gap: 0.5rem;
            }
            
            /* Tabs compacting */
            .stTabs [data-baseweb="tab-list"] {
                gap: 4px;
                margin-bottom: 0.5rem;
            }
            .stTabs [data-baseweb="tab"] {
                height: 36px;
                padding: 4px 16px;
                font-size: 0.9rem;
            }
            
            /* Custom utility classes */
            .compact-text {
                font-size: 0.9rem;
                color: var(--text-muted);
                line-height: 1.4;
            }
            .highlight-box {
                background: #f1f5f9;
                padding: 0.75rem;
                border-radius: 6px;
                border-left: 3px solid var(--secondary-color);
                margin-bottom: 0.5rem;
            }
            
            /* Custom Feature Card (used in Home) */
            .feature-card {
                background: white;
                padding: 1.25rem;
                border-radius: 0.75rem;
                box-shadow: var(--card-shadow);
                border: 1px solid #e2e8f0;
                height: 100%;
                transition: transform 0.2s;
            }
            .feature-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 0.5rem;
                background: #f1f5f9;
                width: 3rem;
                height: 3rem;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
            }
            
            /* Custom Stat Card */
            .stat-card {
                padding: 1rem;
                border-radius: 0.75rem;
                color: white;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .stat-number {
                font-size: 2rem;
                font-weight: 700;
                line-height: 1.2;
            }
            .stat-label {
                font-size: 0.85rem;
                opacity: 0.9;
                margin-top: 0.25rem;
            }

            /* Hide Streamlit footer/menu for cleaner look */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}

            /* Hide Streamlit Cloud manage app button */
            a[data-testid="manage-app"] { display: none !important; }
            div[data-testid="stToolbar"] { display: none !important; }
            div[data-testid="stToolbarActions"] { display: none !important; }
            button[title="Manage app"] { display: none !important; }
            
        </style>
    """, unsafe_allow_html=True)

def render_header(title, icon):
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;">
            <div style="font-size: 2.2rem; line-height: 1;">{icon}</div>
            <h1 style="margin: 0; padding: 0; font-size: 1.8rem; line-height: 1.2;">{title}</h1>
        </div>
    """, unsafe_allow_html=True)
