# src/attendance_system.py
import cv2
import pickle
import os
import time
from datetime import datetime
from database import mark_attendance, add_contact, get_contact_info
from alerts import send_notifications, send_teacher_report
import json
import re
import numpy as np
try:
    import face_recognition
except ImportError:
    print("face_recognition library is required. Please install it with 'pip install face_recognition'.")
    exit(1)

# Initialize paths
encodings_path = os.path.join("data", "encodings.pkl")
known_faces_dir = os.path.join("data", "known_faces")

# Load OpenCV's face detector and recognizer
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')  # type: ignore

# Try to import scheduler, but make it optional
scheduler = None
BackgroundScheduler = None
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    print("Warning: APScheduler not available. Daily reports will not be scheduled.")
    SCHEDULER_AVAILABLE = False

# Add this after the other global variables at the top
already_notified = {}  # Track which students have been notified about already marked attendance

def validate_phone(phone):
    # Accepts +91 followed by 10 digits
    return bool(re.match(r"^\+91\d{10}$", phone))

def validate_email(email):
    # Basic email validation
    return bool(re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email))

def capture_new_face():
    """Capture new face images and add to the system."""
    name = input("Enter person's full name: ").strip().title()

    # Parent phone validation
    while True:
        parent_phone = input("Enter parent's phone (+91 followed by 10 digits): ").strip()
        if validate_phone(parent_phone):
            break
        print("Error: Phone must be in the format +91 followed by 10 digits (e.g., +919876543210).")

    # Email validation
    while True:
        email = input("Enter email address: ").strip().lower()
        if validate_email(email):
            break
        print("Error: Invalid email format. Example: john.doe@example.com")

    # Create directory for new person
    person_dir = os.path.join(known_faces_dir, name)
    os.makedirs(person_dir, exist_ok=True)

    # Capture face images
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    count = 0
    face_samples = []

    print("Press SPACE to capture images. Press ESC when done.")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        # Draw rectangle around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        cv2.imshow("Capture Faces", frame)
        key = cv2.waitKey(1)

        if key == 32:  # SPACE key
            if len(faces) == 1:  # Only capture if exactly one face is detected
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))
                face_samples.append(face_roi)
                
                # Save the image
                img_path = os.path.join(person_dir, f"{name}_{count}.jpg")
                cv2.imwrite(img_path, frame)
                print(f"Saved: {img_path}")
                count += 1
            else:
                print("Please position exactly one face in the frame")
        elif key == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()

    if face_samples:
        # Add contact info to database
        add_contact(name, parent_phone, email)
        print(f"\n✅ Added {name} with {count} images")
        # Do NOT update encodings.pkl here. Only images and DB are updated.
    else:
        print("No face samples captured. Please try again.")


def load_encodings():
    """Load existing face encodings or initialize new."""
    try:
        with open(encodings_path, "rb") as f:
            known_encodings, known_names = pickle.load(f)
        print("Loaded existing face encodings")
    except FileNotFoundError:
        known_encodings = []
        known_names = []
        print("No existing encodings found. Starting fresh.")
    return known_encodings, known_names


def schedule_daily_reports():
    """Schedule daily reports at 16:30"""
    if not SCHEDULER_AVAILABLE or BackgroundScheduler is None:
        print("Skipping report scheduling - APScheduler not available")
        return

    global scheduler
    scheduler = BackgroundScheduler()

    with open('data/teachers.json') as f:
        teachers = json.load(f)['teachers']

    for teacher in teachers:
        if 'report_time' in teacher:
            hour, minute = map(int, teacher['report_time'].split(':'))
            scheduler.add_job(
                send_teacher_report,
                'cron',
                args=[teacher],
                hour=hour,
                minute=minute
            )

    scheduler.start()
    print("Daily reports scheduled successfully")


def initialize_camera():
    """Initialize camera with retry logic."""
    max_retries = 3
    for i in range(max_retries):
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                print(f"Failed to open camera (attempt {i+1}/{max_retries})")
                cap.release()
                continue
                
            # Test camera by reading a frame
            ret, frame = cap.read()
            if not ret or frame is None:
                print(f"Failed to read from camera (attempt {i+1}/{max_retries})")
                cap.release()
                continue
                
            print("Camera initialized successfully")
            return cap
            
        except Exception as e:
            print(f"Camera error (attempt {i+1}/{max_retries}): {str(e)}")
            if i < max_retries - 1:
                time.sleep(1)  # Wait before retrying
                
    raise RuntimeError("Failed to initialize camera after multiple attempts")


def process_frame(frame, known_face_encodings, known_face_names):
    """Detect faces and recognize using face_recognition encodings."""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
    return face_locations, face_encodings


def main():
    """Main function to run the attendance system"""
    # Initialize database
    from database import init_db
    init_db()
    
    # Schedule daily reports
    schedule_daily_reports()
    
    # Load known faces
    known_face_encodings, known_face_names = load_encodings()
    if not known_face_encodings:
        print("No known faces found. Please add some faces first.")
        return

    # Initialize camera
    video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not video_capture.isOpened():
        print("Failed to open camera")
        return
    print("Camera initialized successfully")

    # Process every 3rd frame to reduce CPU usage
    frame_count = 0
    last_attendance = {}  # Track last attendance hour for each person
    
    try:
        while True:
            ret, frame = video_capture.read()
            if not ret:
                print("Failed to grab frame")
                break

            frame_count += 1
            if frame_count % 3 != 0:  # Process every 3rd frame
                continue

            # Validate frame format
            if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
                print("Invalid frame format")
                continue

            # Process the frame
            face_locations, face_encodings = process_frame(frame, known_face_encodings, known_face_names)

            # Process each face found in the frame
            current_hour = datetime.now().hour
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Compare with known faces
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                name = "Unknown"
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_face_names[best_match_index]

                # Initialize label for display
                label = "Unknown - Press A to add"
                
                if name != "Unknown":
                    # First check if already marked for this hour
                    is_already_marked = (name in last_attendance and last_attendance[name] == current_hour)
                    
                    if is_already_marked:
                        # Already marked for this hour - just show message once
                        if name not in already_notified or already_notified[name] != current_hour:
                            print(f"ℹ️ Attendance already marked for {name} for {current_hour}:00")
                            already_notified[name] = current_hour
                        label = f"{name} (Already Marked)"
                    else:
                        # New attendance for this hour
                        mark_attendance(name)
                        last_attendance[name] = current_hour
                        print(f"✅ Marked attendance for {name} for {current_hour}:00")
                        # Only send notification for new attendance
                        send_notifications(name)
                        label = name
                        # Reset notification status for this student
                        if name in already_notified:
                            del already_notified[name]

                # Draw box and label
                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.putText(frame, label, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 1)

            # Display the frame
            cv2.imshow("Face Attendance System (Q=Quit | A=Add New)", frame)

            # Check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Quit
                break
            elif key == ord('a'):  # Add new person
                # Release camera temporarily
                video_capture.release()
                cv2.destroyAllWindows()
                
                # Capture new face
                capture_new_face()
                
                # Reload encodings
                known_face_encodings, known_face_names = load_encodings()
                
                # Reinitialize camera
                video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not video_capture.isOpened():
                    print("Failed to reopen camera")
                    break

            # Add a small delay to reduce CPU usage
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nSystem shutdown")
    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        if scheduler:
            scheduler.shutdown()


if __name__ == "__main__":
    main()