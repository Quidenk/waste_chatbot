from pymongo import MongoClient

label = 'biological'

# Kết nối MongoDB
client = MongoClient("mongodb://localhost:27017")  # Đổi nếu MongoDB chạy trên server khác
db = client['waste_management']  # Database name
collection = db['solutions']  # Collection name

solution_data = collection.find_one({"type": label})
solution = solution_data["description"] if solution_data else "Chưa có thông tin xử lý loại rác này."

print("solution_data :", solution_data["description"])