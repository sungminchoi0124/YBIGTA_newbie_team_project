import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo_url = os.getenv("MONGO_URL")

if not mongo_url:
    raise ValueError("MONGO_URL is not set in .env")

mongo_client = MongoClient(mongo_url)
mongo_db = mongo_client["ybigta_reviews"]
