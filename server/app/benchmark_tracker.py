import os
import json
import time
from datetime import datetime

# Adjust path so benchmark folder is inside server/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARK_DIR = os.path.join(BASE_DIR, "benchmark")
os.makedirs(BENCHMARK_DIR, exist_ok=True)

class BenchmarkTracker:
    def __init__(self, name: str):
        self.name = name
        self.steps = []
        self.start_time = None
        self.total_time = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.total_time = time.perf_counter() - self.start_time
        self.save()

    def step(self, step_name: str):
        return BenchmarkStep(self, step_name)

    def save(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.name}_{timestamp}.json"
        path = os.path.join(BENCHMARK_DIR, filename)
        with open(path, "w") as f:
            json.dump({
                "name": self.name,
                "total_time_seconds": self.total_time,
                "steps": self.steps
            }, f, indent=2)

class BenchmarkStep:
    def __init__(self, tracker, step_name):
        self.tracker = tracker
        self.step_name = step_name
        self.start = None

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start
        self.tracker.steps.append({
            "step": self.step_name,
            "time_seconds": duration
        })