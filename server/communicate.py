
import pandas as pd
from pymongo import MongoClient

import json

def safe_parse(x):
    try:
        # Thay thế xuống dòng bằng ký hiệu JSON hợp lệ
        clean_x = x.replace('\n', '\\n')
        return json.loads(clean_x)
    except Exception as e:
        print("Lỗi khi parse:", x)
        print(e)
        return []

# Kết nối MongoDB
client = MongoClient("mongodb+srv://anhb2113304:anhb2113304@cluster0.uaksfyf.mongodb.net/waste_management?retryWrites=true&w=majority&appName=Cluster0")
db = client["waste_management"]  # Đổi tên database thành "waste_management"

# Đọc file Excel
file_path = "D:/Niên Luận Ngành/reponses_excel/reponses.xlsx"
xls = pd.ExcelFile(file_path)

# ======== UPDATE responses_collection (câu trả lời chatbot) =========
df_responses = pd.read_excel(xls, "responses_collection")
df_responses["answers"] = df_responses["answers"].apply(lambda x: eval(x))  # Chuyển chuỗi JSON về list
df_responses["intent"] = df_responses["intent"].apply(lambda x: eval(x))  # Chuyển chuỗi JSON về list
responses_data = df_responses.to_dict(orient="records")

for doc in responses_data:
    db.responses.update_one(
        {"intent": doc["intent"]},  # Điều kiện nhận diện bản ghi
        {"$set": doc},              # Dữ liệu cần cập nhật
        upsert=True                 # Thêm mới nếu chưa có
    )

# ======== UPDATE solutions_collection (giải pháp xử lý rác) =========
df_solutions = pd.read_excel(xls, "solutions_collection")
solutions_data = df_solutions.to_dict(orient="records")

for doc in solutions_data:
    db.solutions.update_one(
        {"type": doc["type"]},      # Giả sử mỗi "type" là duy nhất
        {"$set": doc},              # Cập nhật nội dung
        upsert=True                 # Thêm mới nếu chưa có
    )

print("Dữ liệu đã được cập nhật thành công vào MongoDB!")
