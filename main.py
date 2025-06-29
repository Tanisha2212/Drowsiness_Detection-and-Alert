import streamlit as st
from drowsiness import DrowsinessDetector
import pandas as pd
import datetime
import os
from pathlib import Path

# Page config
st.set_page_config(page_title="Drowsiness Monitor", layout="wide")

# Initialize session state
if 'detector' not in st.session_state:
    st.session_state.detector = None
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

# Sidebar - Admin Controls
with st.sidebar:
    st.header("Admin Panel")
    app_mode = st.selectbox("Select Mode", 
        ["Live Monitoring", "Video Analysis", "Alert Logs", "User Management"])
    
    # System settings
    with st.expander("⚙️ System Settings"):
        ear_threshold = st.slider("EAR Threshold", 0.1, 0.4, 0.25, 0.01)
        frame_threshold = st.slider("Frame Threshold", 5, 50, 20)
        audio_alerts = st.checkbox("Enable Audio Alerts", True)

# Main Content Area
if app_mode == "Live Monitoring":
    st.title("Real-time Drowsiness Monitoring")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Camera Feed")
        video_placeholder = st.empty()
        
    with col2:
        st.subheader("EAR Graph")
        chart_placeholder = st.line_chart(pd.DataFrame(columns=['EAR'], index=range(30)))
        
    if st.button("Start Monitoring"):
        st.session_state.detector = DrowsinessDetector(ear_threshold, frame_threshold)
        st.session_state.detector.run_live(video_placeholder, chart_placeholder)

elif app_mode == "Video Analysis":
    st.title("Video Analysis")
    uploaded_file = st.file_uploader("Upload Test Video", type=["mp4", "avi"])
    
    if uploaded_file:
        if st.session_state.detector is None:
            st.session_state.detector = DrowsinessDetector(ear_threshold, frame_threshold)
        
        with st.spinner("Processing video..."):
            frames, alerts = st.session_state.detector.process_video(uploaded_file)
            
            if len(frames) > 0:
                st.success(f"Processed {len(frames)} frames")
                st.video(frames[0].tobytes())
                
                # Create results dataframe
                results = pd.DataFrame({
                    'Frame': range(len(frames)),
                    'EAR': [a[0] for a in alerts],
                    'Alert': [a[1] for a in alerts]
                })
                
                # Add to session state for logs
                st.session_state.alerts.extend([
                    {
                        "Timestamp": datetime.datetime.now(),
                        "Duration": f"{sum([a[1] for a in alerts])} frames",
                        "Location": "Simulated GPS"
                    }
                ])
                
                st.download_button(
                    "Download Results",
                    results.to_csv(index=False),
                    "analysis_results.csv",
                    "text/csv"
                )

elif app_mode == "Alert Logs":
    st.title("Alert History")
    if st.session_state.alerts:
        st.dataframe(pd.DataFrame(st.session_state.alerts))
    else:
        st.info("No alerts recorded yet")
        # Demo data
        st.dataframe(pd.DataFrame({
            "Timestamp": [datetime.datetime.now()],
            "Driver": ["Demo User"],
            "Duration": ["5.2s"],
            "Location": ["37.7749° N, 122.4194° W"]
        }))

elif app_mode == "User Management":
    st.title("Driver Management")
    st.write("User management functionality would be implemented here")
    # Example UI elements
    with st.form("user_form"):
        name = st.text_input("Driver Name")
        id = st.text_input("Driver ID")
        submitted = st.form_submit_button("Add Driver")
        if submitted:
            st.success(f"Driver {name} added successfully")

# Add some custom CSS
st.markdown("""
<style>
    .stAlert {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .st-b7 {
        color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)