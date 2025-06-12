import cv2
import os
import sys
import time
from datetime import datetime

def create_dataset(name):
    # Create directory for storing face images
    dataset_dir = os.path.join("data", "known_faces", name)
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Load face detection classifier
    cascade_path = os.path.join(os.path.dirname(cv2.__file__), 'data', 'haarcascade_frontalface_default.xml')
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("Error: Could not load face cascade classifier")
        return
    
    count = 0
    print(f"Starting face capture for {name}")
    print("Press SPACE to capture an image, ESC to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame")
            break
            
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangle around faces and store the first face coordinates
        face_coords = None
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            if face_coords is None:  # Store only the first face
                face_coords = (x, y, w, h)
        
        # Display count
        cv2.putText(frame, f"Captured: {count}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Show the frame
        cv2.imshow('Face Capture', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # Press SPACE to capture
        if key == 32:  # SPACE key
            if len(faces) == 1 and face_coords is not None:  # Only capture if exactly one face is detected
                x, y, w, h = face_coords
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                face_img = frame[y:y+h, x:x+w]
                img_path = os.path.join(dataset_dir, f"{name}_{timestamp}_{count}.jpg")
                cv2.imwrite(img_path, face_img)
                count += 1
                print(f"Captured image {count}")
            else:
                print("Please ensure only one face is visible in the frame")
        
        # Press ESC to quit
        elif key == 27:  # ESC key
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"Face capture complete. {count} images saved in {dataset_dir}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python capture_faces.py <person_name>")
        sys.exit(1)
    
    name = sys.argv[1]
    create_dataset(name) 