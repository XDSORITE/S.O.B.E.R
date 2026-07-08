import cv2

# Initialize the camera. 0 is usually the built-in webcam.
cap = cv2.VideoCapture(0)

# Check if the camera opened correctly
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()

    # If the frame was not grabbed correctly, break the loop
    if not ret:
        print("Error: Can't receive frame.")
        break

    # Display the resulting frame in a window named 'Webcam Feed'
    cv2.imshow('Webcam Feed', frame)

    # Press 'q' on the keyboard to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera resource and close all windows
cap.release()
cv2.destroyAllWindows()