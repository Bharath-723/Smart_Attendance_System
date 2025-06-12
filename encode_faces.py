import face_recognition
import pickle
import os
import cv2

def encode_faces():
    """Generate face encodings from known face images."""
    known_faces_dir = os.path.join("data", "known_faces")
    encodings_path = os.path.join("data", "encodings.pkl")
    
    known_encodings = []
    known_names = []
    
    # Walk through known faces directory
    for person_dir in os.listdir(known_faces_dir):
        person_path = os.path.join(known_faces_dir, person_dir)
        if not os.path.isdir(person_path):
            continue
            
        # Process each image in person's directory
        for image_file in os.listdir(person_path):
            if not image_file.endswith(('.jpg', '.jpeg', '.png')):
                continue
                
            image_path = os.path.join(person_path, image_file)
            
            try:
                # Load image and get face encoding
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                
                if face_encodings:
                    known_encodings.append(face_encodings[0])
                    known_names.append(person_dir)
                    print(f"Encoded {image_path}")
                else:
                    print(f"No face found in {image_path}")
                    
            except Exception as e:
                print(f"Error processing {image_path}: {str(e)}")
    
    # Save encodings
    if known_encodings:
        with open(encodings_path, "wb") as f:
            pickle.dump((known_encodings, known_names), f)
        print(f"Saved {len(known_encodings)} face encodings")
    else:
        print("No face encodings generated")

if __name__ == "__main__":
    encode_faces() 