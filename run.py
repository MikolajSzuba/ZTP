import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import uvicorn
import traceback
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    try:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="trace")
    except Exception as e:
        traceback.print_exc()
