
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import cv2
from ultralytics import YOLO
from pymongo import MongoClient
import torch
from torchvision import transforms
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms
import random
import socket

port = int(os.environ.get("PORT", 5000))
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Kết nối MongoDB
client = MongoClient("mongodb+srv://anhb2113304:anhb2113304@cluster0.uaksfyf.mongodb.net/waste_management?retryWrites=true&w=majority&appName=Cluster0")
db = client['waste_management']
collection = db['solutions']

print(">>>>>collection:", collection)

yolo_model = YOLO("D:/Niên Luận Ngành/app_mobile_2/WasteChatbot/model_trained/model_yolov11_50_32_416 (1)/weights/best.pt")
mobilenet_model = models.mobilenet_v2(pretrained=False)
mobilenet_model.classifier[1] = nn.Linear(mobilenet_model.last_channel, 6)  # sửa 6 nếu bạn có số lớp khác
mobilenet_model.load_state_dict(torch.load("D:/Niên Luận Ngành/app_mobile_2/WasteChatbot/model_trained/mobilenet/mobilenet_test.pth", map_location=torch.device('cpu')))
mobilenet_model.eval()
mobilenet_labels = ["battery", "biological", "glass", "metal", "paper", "plastic"]

# Transform ảnh cho MobileNet
mobilenet_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

def classify_with_mobilenet(image_path):
    img = Image.open(image_path).convert("RGB")
    img_tensor = mobilenet_transform(img).unsqueeze(0)

    with torch.no_grad():
        outputs = mobilenet_model(img_tensor)
        probs = torch.nn.functional.softmax(outputs[0], dim=0)
        class_id = torch.argmax(probs).item()
        label = mobilenet_labels[class_id]
        confidence = round(probs[class_id].item() * 100, 2)

    return label, confidence

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({"error": "Không tìm thấy ảnh!"}), 400

    file = request.files['image']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    img = cv2.imread(filepath)
    results = yolo_model(filepath)
    predictions = []

    for result in results:
        for i, box in enumerate(result.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            cropped_img = img[y1:y2, x1:x2]
            cropped_filename = f"detected_{i}_{filename}"
            cropped_filepath = os.path.join(OUTPUT_FOLDER, cropped_filename)
            cv2.imwrite(cropped_filepath, cropped_img)

            # Phân loại bằng MobileNet
            label, confidence = classify_with_mobilenet(cropped_filepath)
            print(f"Label classified: {label}, Confidence: {confidence}%")

            # Truy vấn MongoDB
            solution_data = collection.find_one({"type": label})
            solution = solution_data["description"] if solution_data else "Chưa có thông tin xử lý loại rác này."

            predictions.append({
                "label": label,
                "confidence": confidence,
                "image": f"http://{request.host}/output/{cropped_filename}",
                "solution": solution
            })

    os.remove(filepath)
    return jsonify({"predictions": predictions})

@app.route('/output/<filename>', methods=['GET'])
def get_detected_image(filename):
    file_path = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='image/jpeg')
    return jsonify({"error": "Ảnh không tồn tại"}), 404

@app.route('/get_solution', methods=['POST'])
def get_solution():
    data = request.get_json()
    waste_type = data.get("type")
    solution_data = collection.find_one({"type": waste_type})
    if solution_data:
        return jsonify({"solution": solution_data["description"]})
    else:
        return jsonify({"solution": "Chưa có thông tin xử lý loại rác này."})

responses_collection = db["responses"]  

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get("message", "").lower()

    if not user_message:
        return jsonify({"response": "Vui lòng nhập nội dung tin nhắn!"}), 400

    
    responses = list(responses_collection.find())

    for response in responses:
        intents = [i.lower() for i in response.get("intent", [])]

        
        if any(intent in user_message for intent in intents):
            answers = response.get("answers", [])
            if answers:
                return jsonify({"response": random.choice(answers)})

    
    default_response = responses_collection.find_one({"intent": "default"})
    if default_response:
        return jsonify({"response": random.choice(default_response.get("answers", []))})

    return jsonify({"response": "Tôi không hiểu. Bạn có thể hỏi lại không?"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)