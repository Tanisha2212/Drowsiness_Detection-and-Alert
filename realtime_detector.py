import cv2
import argparse
from drowsiness_detector import DrowsinessDetector
import time

def main():
    parser = argparse.ArgumentParser(description='Real-time Drowsiness Detection')
    parser.add_argument('--thresh', type=float, default=0.25, help='EAR threshold for drowsiness')
    parser.add_argument('--frame_check', type=int, default=20, help='Consecutive frames to trigger alert')
    parser.add_argument('--model', type=str, default='models/shape_predictor_68_face_landmarks.dat', 
                       help='Path to facial landmark model')
    parser.add_argument('--music', type=str, default='music.wav', help='Path to alert sound file')
    parser.add_argument('--camera', type=int, default=0, help='Camera index')
    parser.add_argument('--video', type=str, help='Path to input video file (optional)')
    parser.add_argument('--output', type=str, help='Path to save output video (optional)')
    parser.add_argument('--auto_stop', type=int, help='Auto stop after N seconds (for integration)')
    
    args = parser.parse_args()
    
    # Initialize detector
    try:
        detector = DrowsinessDetector(
            thresh=args.thresh,
            frame_check=args.frame_check,
            model_path=args.model,
            music_path=args.music
        )
        print("✓ Drowsiness detector initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing detector: {e}")
        return
    
    # Initialize video capture
    if args.video:
        cap = cv2.VideoCapture(args.video)
        print(f"✓ Processing video: {args.video}")
    else:
        cap = cv2.VideoCapture(args.camera)
        print(f"✓ Using camera: {args.camera}")
    
    if not cap.isOpened():
        print("✗ Error: Could not open video source")
        return
    
    # Get video properties
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Initialize video writer if output specified
    out = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(args.output, fourcc, fps, (450, int(450 * height / width)))
        print(f"✓ Output will be saved to: {args.output}")
    
    print("\n" + "="*50)
    print("DROWSINESS DETECTION STARTED")
    print("="*50)
    print("Controls:")
    print("- Press 'q' to quit")
    print("- Press 's' to show current statistics")
    print("- Press 'r' to reset session")
    print("="*50 + "\n")
    
    frame_count = 0
    start_time = time.time()
    auto_stop_time = start_time + args.auto_stop if args.auto_stop else None
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                if args.video:
                    print("✓ Video processing completed")
                    break
                else:
                    print("✗ Error reading from camera")
                    break
            
            frame_count += 1
            current_time = time.time()
            
            # Auto stop check for integration mode
            if auto_stop_time and current_time > auto_stop_time:
                print(f"✓ Auto-stopped after {args.auto_stop} seconds")
                break
            
            # Process frame
            processed_frame, results = detector.process_frame(frame, play_sound=not args.video)
            
            # Add frame info
            cv2.putText(processed_frame, f"Frame: {frame_count}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            if results["faces_detected"] == 0:
                cv2.putText(processed_frame, "No face detected", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Show frame
            cv2.imshow("Drowsiness Detection", processed_frame)
            
            # Save frame if output specified
            if out:
                out.write(processed_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("s"):
                stats = detector.get_session_stats()
                print("\n" + "-"*30)
                print("CURRENT SESSION STATS:")
                print(f"Duration: {stats['session_duration']:.1f} seconds")
                print(f"Total frames: {stats['total_frames']}")
                print(f"Drowsy frames: {stats['drowsy_frames']}")
                print(f"Drowsiness %: {stats['drowsiness_percentage']:.2f}%")
                print(f"Drowsy events: {stats['drowsy_events']}")
                print(f"Current EAR: {stats['current_ear']:.3f}")
                print(f"Average EAR: {stats['avg_ear']:.3f}")
                print("-"*30 + "\n")
            elif key == ord("r"):
                detector.reset_session()
                print("✓ Session reset")
    
    except KeyboardInterrupt:
        print("\n✓ Detection stopped by user")
    
    finally:
        # Calculate final statistics
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "="*50)
        print("SESSION SUMMARY")
        print("="*50)
        
        stats = detector.get_session_stats()
        print(f"Total duration: {total_time:.1f} seconds")
        print(f"Frames processed: {frame_count}")
        print(f"Average FPS: {frame_count/total_time:.1f}")
        print(f"Drowsy frames: {stats['drowsy_frames']}")
        print(f"Drowsiness percentage: {stats['drowsiness_percentage']:.2f}%")
        print(f"Drowsy events detected: {stats['drowsy_events']}")
        
        if stats['drowsy_events'] > 0:
            print(f"Average EAR during session: {stats['avg_ear']:.3f}")
            print("⚠️  Drowsiness detected during session!")
        else:
            print("✅ No drowsiness detected - Good session!")
        
        # Save session log
        try:
            detector.save_session_log()
            print(f"✓ Session logged to: {detector.log_file}")
        except Exception as e:
            print(f"✗ Error saving log: {e}")
        
        print("="*50)
        
        # Cleanup
        cap.release()
        if out:
            out.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()