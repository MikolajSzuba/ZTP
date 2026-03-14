import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from data.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT * FROM products'))
        for row in result:
            print(row)
    print("CONNECTION OK")
except Exception as e:
    print(f"ERROR: {e}")
