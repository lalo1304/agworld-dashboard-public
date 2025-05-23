import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from PIL import Image

# Streamlit page setup with neutral styling
site_bg = "#f5f7fa"       # Light gray-blue
sidebar_bg = "#e2e8f0"    # Light slate
text_color = "#1f2937"    # Slate-800
header_color = "#2563eb"  # Blue-600
cell_bg = "#ffffff"       # White
cell_text = "#1f2937"     # Slate text

st.set_page_config(page_title="Agworld Custom Report", layout="wide")

st.markdown(f"""
    <style>
    html, body, [class*="css"]  {{
        background-color: {site_bg} !important;
        color: {text_color} !important;
    }}
    .stApp {{
        background-color: {site_bg};
    }}
    .stDataFrame table {{
        background-color: {cell_bg} !important;
        color: {cell_text} !important;
    }}
    .css-1d391kg, .css-ffhzg2, .stSelectbox, .stMultiSelect, .stDateInput {{
        background-color: #f1f5f9 !important;
        color: {text_color} !important;
    }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        color: {header_color} !important;
        font-weight: bold !important;
    }}
    .stSidebar {{
        background-color: {sidebar_bg};
    }}
    </style>
""", unsafe_allow_html=True)

st.title("🧑‍🌾 Agworld Observations Dashboard")

# PostgreSQL connection
DB_HOST = "127.0.0.1"
DB_PORT = "5432"
DB_NAME = "agworld"
DB_USER = "postgres"
DB_PASS = "BFCo"

conn_str = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(conn_str)

@st.cache_data
def load_data():
    try:
        df = pd.read_sql("SELECT * FROM agworld_custom_report", engine)
        for col in df.columns:
            if "date" in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        drop_cols = ["activity name", "activity tag list", "input", "job id", "activity id", "activity tag", "property", "season", "crop stage"]
        df = df.drop(columns=[col for col in df.columns if col.lower().strip().replace("_", " ") in drop_cols])

        df.rename(columns={
            "Paddock": "Field",
            "Crop": "Crop",
            "Variety": "Variety",
            "Pest List": "Pest List",
            "Problem Severity": "Problem Severity",
            "Activity Comment": "Activity Comment",
            "Activity Author": "Activity Author",
            "Date Created": "Date Created"
        }, inplace=True)

        if "Date Created" in df.columns:
            df["Date Created"] = pd.to_datetime(df["Date Created"]).dt.strftime("%B %d, %Y")

        if "Field" in df.columns:
            df.sort_values(by="Field", ascending=True, inplace=True)

        desired_order = [
            "Date Created", "Field", "Crop", "Variety",
            "Pest List", "Problem Severity", "Activity Comment", "Activity Author"
        ]
        df = df[[col for col in desired_order if col in df.columns]]

        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"Database query failed: {e}")
        return pd.DataFrame()

data = load_data()
if data.empty:
    st.warning("No data loaded.")
    st.stop()

# Logo in sidebar
logo = Image.open("BfCo-logo-2k.png")
st.sidebar.image(logo, caption="", width=120)

# Date handling
date_cols = [col for col in data.columns if "date" in col.lower()]
date_col = date_cols[0] if date_cols else None

if date_col:
    min_date, max_date = pd.to_datetime(data[date_col]).min(), pd.to_datetime(data[date_col]).max()
    today = pd.Timestamp.today()
    default_start = max(min_date, today - pd.Timedelta(days=today.weekday()))
    default_end = min(max_date, default_start + pd.Timedelta(days=6))

    st.sidebar.markdown("#### View a date range:")
    date_range = st.sidebar.date_input(
        "Date Range", [default_start, default_end], min_value=min_date, max_value=max_date
    )

    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        data = data[pd.to_datetime(data[date_col]).between(start_date, end_date)]
    else:
        start_date, end_date = default_start, default_end
else:
    start_date = end_date = datetime.today()

# Sidebar filters
st.sidebar.header("📊 Filters")
if "Crop" in data.columns:
    crop_options = sorted(data["Crop"].dropna().unique())
    crop_filter = st.sidebar.multiselect("Crop", crop_options, default=crop_options)
    data = data[data["Crop"].isin(crop_filter)]

st.markdown(f"### Observations from {start_date.date()} to {end_date.date()}")

def style_table(df):
    return df.style.set_properties(
        **{
            "border": "1px solid #ccc",
            "padding": "8px",
            "font-size": "14px",
            "color": cell_text,
            "background-color": cell_bg,
            "text-align": "center",
            "white-space": "normal",
        }
    ).set_table_styles(
        [{"selector": "th", "props": [("background-color", header_color), ("color", "#ffffff"), ("font-weight", "bold"), ("text-align", "center")]}]
    )

styled_table = style_table(data.copy())
st.dataframe(styled_table, use_container_width=True, height=400, hide_index=True)
