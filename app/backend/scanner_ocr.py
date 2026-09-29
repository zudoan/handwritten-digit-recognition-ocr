"""
Bộ xử lý quét ảnh tài liệu & bóc tách nhận diện chuỗi chữ số viết tay (Multi-digit OCR Scanner).
Tự động phát hiện vị trí các chữ số trong ảnh, cắt vùng, chuẩn hóa và gán nhãn dự đoán trực quan.
"""

import time
import numpy as np
import cv2
from app.backend.image_processing import (
    center_of_mass_shift,
    encode_cv2_to_base64
)
from app.backend.model_manager import model_manager

def scan_and_recognize_digits(
    img_bgr: np.ndarray,
    model_id: str = "standard_cnn",
    min_area: int = 40,
    confidence_threshold: float = 20.0
) -> dict:
    """
    Quét toàn bộ ảnh đầu vào, phát hiện tất cả các chữ số viết tay, 
    nhận diện và vẽ bounding boxes kèm nhãn lên ảnh kết quả.
    """
    start_time = time.perf_counter()
    original_h, original_w = img_bgr.shape[:2]
    
    # 1. Chuyển sang ảnh xám
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 2. Khử nhiễu & Làm nổi bật nét viết
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Tự động xác định nền sáng chữ tối hay nền tối chữ sáng
    corners = [blurred[0, 0], blurred[0, -1], blurred[-1, 0], blurred[-1, -1]]
    is_light_bg = np.mean(corners) > 127
    
    if is_light_bg:
        # Nền giấy trắng chữ đen: Phân ngưỡng nhị phân đảo
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 15, 6
        )
    else:
        # Nền tối chữ sáng
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 3. Phép giãn nở (Dilation) nhẹ để nối liền các nét vẽ đứt đoạn
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    dilated = cv2.dilate(thresh, kernel, iterations=1)

    # 4. Tìm các đường viền (Contours) của chữ số
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    candidate_boxes = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        aspect_ratio = float(h) / max(w, 1)
        
        # Lọc bỏ nhiễu hạt quá nhỏ hoặc khung viền quá to
        if area < min_area:
            continue
        if w > original_w * 0.9 and h > original_h * 0.9:
            continue
        # Bỏ các nét ngang dài bất thường hoặc mảnh như sợi chỉ viền
        if h < 8 or w < 4:
            continue
            
        candidate_boxes.append((x, y, w, h, cnt))

    # 5. Sắp xếp các chữ số theo thứ tự đọc (Từ trên xuống dưới, từ trái sang phải)
    # Gom cụm theo dòng nếu có nhiều dòng
    if not candidate_boxes:
        # Không tìm thấy chữ số riêng biệt -> Thử dự đoán toàn bộ ảnh như 1 số duy nhất
        candidate_boxes = [(0, 0, original_w, original_h, None)]

    # Sắp xếp đơn giản từ trái sang phải
    candidate_boxes.sort(key=lambda b: (b[1] // 40, b[0]))

    annotated_img = img_bgr.copy()
    detected_digits = []
    
    # Bảng màu rực rỡ để vẽ các bounding box phân biệt
    palette = [
        (255, 105, 180),  # Neon Pink
        (50, 205, 50),    # Lime Green
        (30, 144, 255),   # Dodger Blue
        (255, 165, 0),    # Orange
        (138, 43, 226),   # Violet
        (0, 255, 255),    # Cyan
        (255, 215, 0),    # Gold
        (240, 128, 128),  # Coral
    ]

    for idx, (x, y, w, h, cnt) in enumerate(candidate_boxes):
        # Mở rộng nhẹ padding xung quanh chữ số (10%)
        pad_x = max(2, int(w * 0.15))
        pad_y = max(2, int(h * 0.15))
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(original_w, x + w + pad_x)
        y2 = min(original_h, y + h + pad_y)

        digit_roi = thresh[y1:y2, x1:x2]
        ch, cw = digit_roi.shape
        if ch == 0 or cw == 0:
            continue

        # Đưa vào khung 20x20 giữ tỉ lệ
        if ch > cw:
            new_h = 20
            new_w = max(1, int(round((cw * 20.0) / ch)))
        else:
            new_w = 20
            new_h = max(1, int(round((ch * 20.0) / cw)))

        resized_digit = cv2.resize(digit_roi, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Đặt vào tâm 28x28
        canvas_28 = np.zeros((28, 28), dtype=np.uint8)
        sy = (28 - new_h) // 2
        sx = (28 - new_w) // 2
        canvas_28[sy:sy + new_h, sx:sx + new_w] = resized_digit

        # Dịch chuyển trọng tâm
        clean_28 = center_of_mass_shift(canvas_28).astype(np.float32) / 255.0
        input_tensor = np.expand_dims(np.expand_dims(clean_28, axis=-1), axis=0)

        # Thực thi mô hình AI
        pred_res = model_manager.predict_single(input_tensor, model_id)
        pred_digit = pred_res["predicted_digit"]
        confidence = pred_res["confidence"]

        if confidence < confidence_threshold and len(candidate_boxes) > 1:
            continue

        color = palette[idx % len(palette)]
        
        # Vẽ bounding box phong cách hiện đại (bo góc & đường viền nổi)
        cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2, cv2.LINE_AA)
        
        # Vẽ tag nhãn phía trên
        label_text = f"{pred_digit} ({int(confidence)}%)"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, min(0.7, h / 60.0))
        thickness = 1
        (label_w, label_h), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
        
        tag_y1 = max(0, y - label_h - 6)
        tag_y2 = y
        tag_x1 = x
        tag_x2 = x + label_w + 8
        cv2.rectangle(annotated_img, (tag_x1, tag_y1), (tag_x2, tag_y2), color, -1)
        # Chữ đen trên nền màu sáng
        cv2.putText(
            annotated_img, label_text, (tag_x1 + 4, tag_y2 - 3),
            font, font_scale, (0, 0, 0), thickness, cv2.LINE_AA
        )

        # Tạo preview thumbnail của chữ số này
        crop_colored = img_bgr[y1:y2, x1:x2]
        thumb_b64 = encode_cv2_to_base64(crop_colored, format=".png")

        detected_digits.append({
            "order": idx + 1,
            "digit": pred_digit,
            "confidence": confidence,
            "box": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
            "thumbnail": thumb_b64,
            "probabilities": pred_res["probabilities"]
        })

    # Ghép chuỗi số được nhận diện
    full_text = "".join([str(d["digit"]) for d in detected_digits])
    avg_confidence = float(np.mean([d["confidence"] for d in detected_digits])) if detected_digits else 0.0
    total_time_ms = (time.perf_counter() - start_time) * 1000

    annotated_b64 = encode_cv2_to_base64(annotated_img, format=".jpg")

    return {
        "success": True,
        "full_text": full_text,
        "total_detected": len(detected_digits),
        "avg_confidence": round(avg_confidence, 2),
        "latency_ms": round(total_time_ms, 2),
        "model_used": model_id,
        "annotated_image": annotated_b64,
        "digits": detected_digits
    }
