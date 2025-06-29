import streamlit as st
import cv2
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
import os
import json
import subprocess
import threading
import time
from drowsiness_detector import DrowsinessDetector

# Page config
st.set_page_config(
    page_title="Drowsiness Detection System",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for navigation bar
st.markdown("""
<style>
/* Navigation Bar */
.nav-bar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem 2rem;
    margin: -1rem -1rem 2rem -1rem;
    border-radius: 0 0 10px 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.nav-title {
    color: white;
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.nav-tabs {
    display: flex;
    justify-content: center;
    gap: 1rem;
    margin-top: 1rem;
}

.nav-tab {
    background: rgba(255,255,255,0.2);
    color: white;
    padding: 0.8rem 1.5rem;
    border-radius: 25px;
    text-decoration: none;
    font-weight: 500;
    transition: all 0.3s ease;
    border: 2px solid transparent;
    cursor: pointer;
}

.nav-tab:hover {
    background: rgba(255,255,255,0.3);
    border-color: white;
    transform: translateY(-2px);
}

.nav-tab.active {
    background: white;
    color: #667eea;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.live-section {
    background: linear-gradient(135deg, #ff6b6b, #ee5a24);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
    text-align: center;
}

.live-button {
    background: white;
    color: #ff6b6b;
    padding: 1rem 2rem;
    border-radius: 50px;
    font-weight: bold;
    font-size: 1.2rem;
    border: none;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.live-button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
}

.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.status-live { background: #00ff00; }
.status-processing { background: #ffaa00; }
.status-ready { background: #0099ff; }

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.metric-card {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}

.video-analysis-section {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    margin: 2rem 0;
}
</style>
""", unsafe_allow_html=True)

def create_navigation():
    """Create navigation bar"""
    st.markdown("""
    <div class="nav-bar">
        <h1 class="nav-title">👁️ Drowsiness Detection System</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tabs = st.tabs(["🎥 Live Detection", "📹 Video Analysis", "📊 Analytics Dashboard", "⚙️ Settings"])
    return tabs

def init_detector():
    """Initialize the drowsiness detector"""
    try:
        detector = DrowsinessDetector()
        return detector, True, "✅ System Ready"
    except Exception as e:
        return None, False, f"❌ Error: {e}"

def check_live_session_status():
    """Check if there's an active live session"""
    status_file = "live_session_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            return status
        except:
            return {"active": False}
    return {"active": False}

def start_live_detection():
    """Start live detection in background process"""
    def run_live_detection():
        try:
            # Create output directory
            os.makedirs("live_sessions", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"live_sessions/session_{timestamp}.mp4"
            
            # Update status
            status = {
                "active": True,
                "start_time": datetime.now().isoformat(),
                "output_file": output_file,
                "session_id": timestamp
            }
            
            with open("live_session_status.json", "w") as f:
                json.dump(status, f)
            
            # Run detection with output recording
            cmd = [
                "python", "realtime_detector.py",
                "--output", output_file,
                "--auto_stop", "120"  # Auto stop after 2 minutes
            ]
            
            process = subprocess.Popen(cmd)
            process.wait()
            
            # Update status when finished
            status["active"] = False
            status["end_time"] = datetime.now().isoformat()
            status["completed"] = True
            
            with open("live_session_status.json", "w") as f:
                json.dump(status, f)
                
        except Exception as e:
            # Update status on error
            status = {"active": False, "error": str(e)}
            with open("live_session_status.json", "w") as f:
                json.dump(status, f)
    
    thread = threading.Thread(target=run_live_detection)
    thread.daemon = True
    thread.start()

def live_detection_tab():
    """Live detection interface"""
    st.markdown("""
    <div class="live-section">
        <h2>🎥 Real-Time Drowsiness Detection</h2>
        <p>Start live camera detection with automatic session recording</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check current status
    status = check_live_session_status()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if status.get("active", False):
            st.markdown("""
            <div style="text-align: center; background: #e8f5e8; padding: 2rem; border-radius: 15px; margin: 1rem 0;">
                <span class="status-indicator status-live"></span>
                <h3 style="color: #2e7d32; margin: 0;">🔴 LIVE DETECTION ACTIVE</h3>
                <p style="margin: 0.5rem 0;">Session started: {}</p>
                <p style="margin: 0; color: #666;">Recording will auto-save when you close the detection window</p>
            </div>
            """.format(status.get("start_time", "")), unsafe_allow_html=True)
            
            if st.button("🛑 Stop Live Detection", key="stop_live"):
                # Kill any running processes
                try:
                    subprocess.run(["pkill", "-f", "realtime_detector.py"], check=False)
                except:
                    pass
                
                # Update status
                status["active"] = False
                with open("live_session_status.json", "w") as f:
                    json.dump(status, f)
                st.rerun()
                
        else:
            st.markdown("""
            <div style="text-align: center; background: #f0f9ff; padding: 2rem; border-radius: 15px; margin: 1rem 0;">
                <span class="status-indicator status-ready"></span>
                <h3 style="color: #1976d2; margin: 0;">Ready for Live Detection</h3>
                <p style="margin: 0.5rem 0;">Click below to start real-time drowsiness monitoring</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚀 Start Live Detection", key="start_live", type="primary"):
                start_live_detection()
                st.success("🎥 Live detection started! A new window will open.")
                st.info("💡 The session will be automatically recorded and saved for analysis.")
                time.sleep(2)
                st.rerun()
    
    # Show completed sessions
    st.subheader("💾 Recent Live Sessions")
    
    live_sessions_dir = "live_sessions"
    if os.path.exists(live_sessions_dir):
        sessions = [f for f in os.listdir(live_sessions_dir) if f.endswith('.mp4')]
        sessions.sort(reverse=True)
        
        if sessions:
            for session in sessions[:5]:  # Show last 5 sessions
                session_path = os.path.join(live_sessions_dir, session)
                file_size = os.path.getsize(session_path) / (1024*1024)  # MB
                mod_time = datetime.fromtimestamp(os.path.getmtime(session_path))
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"📹 {session}")
                    st.caption(f"Created: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                with col2:
                    st.write(f"📊 {file_size:.1f} MB")
                with col3:
                    if st.button("🔍 Analyze", key=f"analyze_{session}"):
                        st.session_state.analyze_video = session_path
                        st.session_state.active_tab = 1  # Switch to video analysis tab
                        st.rerun()
        else:
            st.info("No recorded sessions yet. Start a live detection to create your first session!")
    else:
        st.info("No live sessions directory found. Start your first live detection!")

def video_analysis_tab(detector):
    """Video analysis interface"""
    st.markdown("""
    <div class="video-analysis-section">
        <h2>📹 Video Analysis</h2>
        <p>Upload videos or analyze recorded live sessions</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we need to analyze a specific video
    if hasattr(st.session_state, 'analyze_video'):
        video_path = st.session_state.analyze_video
        st.success(f"🎯 Analyzing recorded session: {os.path.basename(video_path)}")
        
        # Process the video
        with st.spinner("Processing recorded session..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            frame_results = process_video_file_path(detector, video_path, progress_bar, status_text)
            
            if frame_results:
                st.session_state.frame_results = frame_results
                display_video_results(frame_results)
        
        # Clear the analyze_video flag
        del st.session_state.analyze_video
        return
    
    # Regular video upload
    uploaded_file = st.file_uploader(
        "📁 Upload Video File",
        type=['mp4', 'avi', 'mov', 'mkv'],
        help="Upload a video to analyze for drowsiness detection"
    )
    
    if uploaded_file:
        st.video(uploaded_file)
        
        if st.button("🔍 Analyze Video", type="primary"):
            with st.spinner("Processing video..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                frame_results = process_uploaded_video(detector, uploaded_file, progress_bar, status_text)
                
                if frame_results:
                    st.session_state.frame_results = frame_results
                    display_video_results(frame_results)

def process_video_file_path(detector, video_path, progress_bar, status_text):
    """Process video from file path"""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        st.error("❌ Could not open video file")
        return None
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    frame_results = []
    detector.reset_session()
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        processed_frame, results = detector.process_frame(frame, play_sound=False)
        frame_results.append({
            'frame': frame_count,
            'timestamp': frame_count / fps,
            'ear': results['ear'],
            'drowsy': results['drowsy'],
            'alert': results['alert_triggered'],
            'faces': results['faces_detected']
        })
        
        frame_count += 1
        progress = min(frame_count / total_frames, 1.0)
        progress_bar.progress(progress)
        status_text.text(f"Processing frame {frame_count}/{total_frames}")
        
        if frame_count > 2000:  # Limit for performance
            break
    
    cap.release()
    return frame_results

def process_uploaded_video(detector, uploaded_file, progress_bar, status_text):
    """Process uploaded video file"""
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    tfile.close()
    
    result = process_video_file_path(detector, tfile.name, progress_bar, status_text)
    os.unlink(tfile.name)
    return result

def display_video_results(frame_results):
    """Display video analysis results"""
    if not frame_results:
        return
        
    st.success("✅ Video analysis completed!")
    
    # Summary metrics
    total_frames = len(frame_results)
    drowsy_frames = sum(1 for r in frame_results if r['drowsy'])
    alert_count = sum(1 for r in frame_results if r['alert'])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_frames}</h3>
            <p>Total Frames</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{drowsy_frames}</h3>
            <p>Drowsy Frames</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{alert_count}</h3>
            <p>Alerts Triggered</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        drowsy_percent = (drowsy_frames / total_frames) * 100 if total_frames > 0 else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>{drowsy_percent:.1f}%</h3>
            <p>Drowsiness Level</p>
        </div>
        """, unsafe_allow_html=True)
    
    # EAR chart
    df_frames = pd.DataFrame(frame_results)
    fig_ear = px.line(df_frames, x='timestamp', y='ear',
                     title='Eye Aspect Ratio Over Time',
                     labels={'timestamp': 'Time (seconds)', 'ear': 'EAR Value'})
    fig_ear.add_hline(y=0.25, line_dash="dash", line_color="red",
                     annotation_text="Drowsiness Threshold")
    st.plotly_chart(fig_ear, use_container_width=True)

def analytics_dashboard(detector):
    """Analytics dashboard"""
    st.header("📊 Analytics Dashboard")
    
    historical_logs = detector.load_historical_logs()
    
    if not historical_logs:
        st.info("No historical data available. Complete some detection sessions to see analytics.")
        return
    
    df_sessions = pd.DataFrame(historical_logs)
    df_sessions['session_date'] = pd.to_datetime(df_sessions['session_id']).dt.date
    df_sessions['duration_minutes'] = df_sessions['duration_seconds'] / 60
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", len(df_sessions))
    with col2:
        avg_duration = df_sessions['duration_minutes'].mean()
        st.metric("Avg Duration", f"{avg_duration:.1f} min")
    with col3:
        total_events = df_sessions['drowsy_events'].sum()
        st.metric("Total Alerts", total_events)
    with col4:
        avg_drowsiness = df_sessions['drowsiness_percentage'].mean()
        st.metric("Avg Drowsiness", f"{avg_drowsiness:.1f}%")
    
    # Trend chart
    fig_trend = px.line(df_sessions, x='session_date', y='drowsiness_percentage',
                       title='Drowsiness Trend Over Time')
    st.plotly_chart(fig_trend, use_container_width=True)

def settings_tab(detector):
    """Settings interface"""
    st.header("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Detection Parameters")
        new_thresh = st.slider("EAR Threshold", 0.1, 0.4, detector.thresh, 0.01)
        new_frame_check = st.slider("Frame Check Count", 5, 50, detector.frame_check)
        
        if st.button("Apply Settings"):
            detector.thresh = new_thresh
            detector.frame_check = new_frame_check
            st.success("✅ Settings updated!")
    
    with col2:
        st.subheader("System Status")
        st.info(f"""
        **Model Path:** {detector.model_path}
        **Threshold:** {detector.thresh}
        **Frame Check:** {detector.frame_check}
        """)

def main():
    # Initialize detector
    if 'detector' not in st.session_state:
        detector, success, message = init_detector()
        st.session_state.detector = detector
        st.session_state.detector_status = success
    
    # Create navigation
    tabs = create_navigation()
    
    if not st.session_state.detector_status:
        st.error("System initialization failed. Please check model files.")
        return
    
    detector = st.session_state.detector
    
    # Tab content
    with tabs[0]:
        live_detection_tab()
    
    with tabs[1]:
        video_analysis_tab(detector)
    
    with tabs[2]:
        analytics_dashboard(detector)
    
    with tabs[3]:
        settings_tab(detector)

if __name__ == "__main__":
    main()