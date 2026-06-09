import os
# Force PyTorch to use the CPU network backend
os.environ["TORCH_DISTRIBUTED_BACKEND"] = "gloo"

from ultralytics import YOLO

def main():
    model = YOLO("yolo11n.pt")
    model.train(
        data="data/data.yaml", 
        epochs=50, 
        imgsz=640,
        device="cpu"  # Explicitly tell YOLO to stay on the CPU
    )

if __name__ == "__main__":
    main()