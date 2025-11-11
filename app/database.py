from pymongo import MongoClient

MONGO_URI = "mongodb://root:root_password@localhost:27017/?authSource=admin"
DB_NAME = "oms_test_db"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
orders_collection = db["orders"]
