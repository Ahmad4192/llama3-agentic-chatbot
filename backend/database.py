import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "llama3_chatbot_db")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users_collection = db["users"]
sessions_collection = db["sessions"]
interactions_collection = db["interactions"]


def init_db():
    users_collection.create_index("email", unique=True)
    sessions_collection.create_index("session_id", unique=True)
    interactions_collection.create_index([("session_id", 1), ("turn_number", 1)])
