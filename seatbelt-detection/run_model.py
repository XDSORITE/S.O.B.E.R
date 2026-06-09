import os
import sys
from ultralytics import YOLO
from cProfile import run
model_location=YOLO("yolo11n.pt")

def run_inference_on_images(image_paths):
    print(f"found {len(image_paths)} image(s), running inference...")
    for image_path in image_paths:
        image_file_name = os.path.basename(image_path)
        print(f"\n--- processing: {image_file_name} ---")
        inference_results = model_location(image_path)
        for single_result in inference_results:
            detected_boxes = single_result.boxes
            if detected_boxes is None or len(detected_boxes) == 0:
                print("  no detections")
                continue
            for detected_box in detected_boxes:
                class_id = int(detected_box.cls[0])
                confidence_score = float(detected_box.conf[0])
                class_label = model_location.names[class_id]
                bounding_box_coords = detected_box.xyxy[0].tolist()
                print(f"  detected: {class_label} | confidence: {confidence_score:.2f} | box: {[round(coord, 1) for coord in bounding_box_coords]}")                                                                                       
        single_result.save(filename=image_path.replace(".", "_result."))
        print(f"  saved annotated result")
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_model.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]
    image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(image_path):
        print(f"Error: File '{filename}' not found in current directory")
        sys.exit(1)
    run_inference_on_images([image_path])