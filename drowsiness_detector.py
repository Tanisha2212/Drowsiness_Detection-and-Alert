from scipy.spatial import distance
from imutils import face_utils
from pygame import mixer
import imutils
import dlib
import cv2
import numpy as np
import datetime
import json
import os

class DrowsinessDetector:
    def __init__(self, thresh=0.25, frame_check=20, model_path="models/shape_predictor_68_face_landmarks.dat", 
                 music_path="music.wav", log_file="drowsiness_log.json"):
        self.thresh = thresh
        self.frame_check = frame_check
        self.model_path = model_path
        self.music_path = music_path
        self.log_file = log_file
        
        # Initialize mixer
        mixer.init()
        if os.path.exists(music_path):
            mixer.music.load(music_path)
        
        # Initialize face detection
        self.detect = dlib.get_frontal_face_detector()
        if os.path.exists(model_path):
            self.predict = dlib.shape_predictor(model_path)
        else:
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Eye landmark indices
        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
        (self.rStart, self.rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
        
        # Session tracking
        self.reset_session()
        
    def reset_session(self):
        """Reset session variables for new detection session"""
        self.flag = 0
        self.session_start = datetime.datetime.now()
        self.drowsy_events = []
        self.total_frames = 0
        self.drowsy_frames = 0
        self.ear_history = []
        
    def eye_aspect_ratio(self, eye):
        """Calculate Eye Aspect Ratio"""
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        C = distance.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    def log_drowsy_event(self, ear_value):
        """Log drowsiness event with timestamp"""
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "ear_value": float(ear_value),
            "session_duration": (datetime.datetime.now() - self.session_start).total_seconds()
        }
        self.drowsy_events.append(event)
        
    def save_session_log(self):
        """Save session statistics to log file"""
        session_data = {
            "session_id": self.session_start.isoformat(),
            "duration_seconds": (datetime.datetime.now() - self.session_start).total_seconds(),
            "total_frames": self.total_frames,
            "drowsy_frames": self.drowsy_frames,
            "drowsy_events": len(self.drowsy_events),
            "drowsiness_percentage": (self.drowsy_frames / max(self.total_frames, 1)) * 100,
            "events": self.drowsy_events,
            "ear_stats": {
                "mean": float(np.mean(self.ear_history)) if self.ear_history else 0,
                "min": float(np.min(self.ear_history)) if self.ear_history else 0,
                "max": float(np.max(self.ear_history)) if self.ear_history else 0
            }
        }
        
        # Load existing logs
        logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(session_data)
        
        # Save updated logs
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
            
    def process_frame(self, frame, play_sound=True, show_contours=True):
        """Process a single frame and return annotated frame with detection results"""
        results = {
            "drowsy": False,
            "ear": 0.0,
            "faces_detected": 0,
            "alert_triggered": False
        }
        
        self.total_frames += 1
        
        # Resize frame
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        subjects = self.detect(gray, 0)
        
        results["faces_detected"] = len(subjects)
        
        for subject in subjects:
            shape = self.predict(gray, subject)
            shape = face_utils.shape_to_np(shape)
            leftEye = shape[self.lStart:self.lEnd]
            rightEye = shape[self.rStart:self.rEnd]
            
            leftEAR = self.eye_aspect_ratio(leftEye)
            rightEAR = self.eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            
            results["ear"] = ear
            self.ear_history.append(ear)
            
            # Draw eye contours if requested
            if show_contours:
                leftEyeHull = cv2.convexHull(leftEye)
                rightEyeHull = cv2.convexHull(rightEye)
                cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
                cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
            
            # Check for drowsiness
            if ear < self.thresh:
                self.flag += 1
                self.drowsy_frames += 1
                results["drowsy"] = True
                
                if self.flag >= self.frame_check:
                    results["alert_triggered"] = True
                    
                    # Draw alert text
                    cv2.putText(frame, "****************ALERT!****************", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, "****************ALERT!****************", (10, 325),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Play sound if enabled and available
                    if play_sound and os.path.exists(self.music_path):
                        try:
                            mixer.music.play()
                        except:
                            pass
                    
                    # Log event (only once per continuous drowsy period)
                    if self.flag == self.frame_check:
                        self.log_drowsy_event(ear)
            else:
                self.flag = 0
            
            # Display EAR value
            cv2.putText(frame, f"EAR: {ear:.3f}", (300, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                       
        return frame, results
    
    def get_session_stats(self):
        """Get current session statistics"""
        current_time = datetime.datetime.now()
        duration = (current_time - self.session_start).total_seconds()
        
        return {
            "session_duration": duration,
            "total_frames": self.total_frames,
            "drowsy_frames": self.drowsy_frames,
            "drowsy_events": len(self.drowsy_events),
            "drowsiness_percentage": (self.drowsy_frames / max(self.total_frames, 1)) * 100,
            "current_ear": self.ear_history[-1] if self.ear_history else 0,
            "avg_ear": np.mean(self.ear_history) if self.ear_history else 0
        }
        
    def load_historical_logs(self):
        """Load historical session logs"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []