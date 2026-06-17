# scripts/run_all.py
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.main import run_pipeline

if __name__ == '__main__':
    run_pipeline()
