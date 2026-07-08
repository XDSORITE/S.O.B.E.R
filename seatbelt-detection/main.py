import sys
from ultralytics import YOLO
from PIL import Image
path_of_image=sys.argv[1]
model=YOLO("best.pt")
img =Image.open(path_of_image).convert("RGB")
results=model(img)

for result in results:
    if result.boxes is None or len(result.boxes) == 0:
        print("no detections")
    else:
        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            label = YOLO("best.pt").names[class_id]
            coords = [round(c, 1) for c in box.xyxy[0].tolist()]
            print(f"detected: {label} | confidence: {confidence:.2f} | box: {coords}")
    result.save(filename=path_of_image.rsplit(".", 1)[0] + "_result." + path_of_image.rsplit(".", 1)[-1])
    print("saved annotated result")