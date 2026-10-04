#!/usr/bin/env python
import sys
import os

# Add backend to path
sys.path.insert(0, r'C:\Users\abhishek\Downloads\ai-based soc\backend')

# Connect to MongoDB first
from backend.database.mongodb import connect_mongo, close_mongo
connect_mongo()

# Now start the server
if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8001, reload=False)