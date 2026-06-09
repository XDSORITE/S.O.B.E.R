from ultralytics import YOLO
import sys
from datetime import datetime

class Logger:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    def flush(self):
        pass

if __name__ == "__main__":
    # Save output to file and terminal
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"training_output_{timestamp}.txt"
    sys.stdout = Logger(log_file)
    model = YOLO("yolo11n.pt")
    results = model.train(
        data="data/data.yaml",
        epochs=50,
        imgsz=640,
        device="cpu"
    )
    print(f"\n\nTraining output saved to: {log_file}")