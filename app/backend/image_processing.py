"""
Tiền xử lý ảnh chuyên sâu theo chuẩn MNIST:
- Cắt biên tự động (Bounding Box extraction)
- Co giãn giữ tỉ lệ (Aspect Ratio Preserved Resize vào khung 20x20)
- Định vị trọng tâm (Center of Mass shift vào giữa ma trận 28x28)
- Chuẩn hóa khoảng giá trị pixel [0.0, 1.0]
"""

import re
import io
import base64
import numpy as np
import cv2
from PIL import Image

def decode_base64_image(base64_str: str) -> np.ndarray:
    """Giải mã chuỗi Base64 Data URL thành ảnh OpenCV BGR/Grayscale"""
    if "," in base64_str:
        base64_str = base64_str.split(",", 1)[1]
    
    img_bytes = base64.b64decode(base64_str)
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    
    # Chuyển đổi sang mảng numpy
    img_np = np.array(img_pil)
    
    # Xử lý kênh alpha nếu vẽ trên canvas trong suốt
    if img_np.shape[-1] == 4:
        r, g, b, a = cv2.split(img_np)
        # Nền trắng mặc định
        background = np.ones_like(r) * 255
        alpha_factor = a.astype(float) / 255.0
        gray = (alpha_factor * cv2.cvtColor(img_np[:, :, :3], cv2.COLOR_RGB2GRAY) + (1.0 - alpha_factor) * background).astype(np.uint8)
    else:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
    return gray


def center_of_mass_shift(img_28x28: np.ndarray) -> np.ndarray:
    """Dịch chuyển ảnh 28x28 sao cho trọng tâm độ sáng (Center of Mass) nằm ở tâm (14, 14)"""
    total_mass = np.sum(img_28x28)
    if total_mass == 0:
        return img_28x28

    y_indices, x_indices = np.indices(img_28x28.shape)
    cy = np.sum(y_indices * img_28x28) / total_mass
    cx = np.sum(x_indices * img_28x28) / total_mass

    shift_y = int(round(14.0 - cy))
    shift_x = int(round(14.0 - cx))

    # Giới hạn dịch chuyển để không đẩy nét vẽ ra ngoài biên
    shift_y = max(-6, min(6, shift_y))
    shift_x = max(-6, min(6, shift_x))

    M = np.float32([[1, 0, shift_x], [0, 1, shift_y]])
    shifted = cv2.warpAffine(img_28x28, M, (28, 28), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return shifted


def preprocess_digit_image(gray_img: np.ndarray) -> tuple[np.ndarray, str]:
    """
    Tiền xử lý ảnh chữ số:
    1. Đảm bảo chữ số màu trắng trên nền đen (như tập MNIST).
    2. Cắt vùng chứa nét vẽ (crop bounding box).
    3. Co giãn về kích thước tối đa 20x20 (giữ nguyên tỉ lệ góc/cạnh).
    4. Đặt vào khung đen 28x28.
    5. Căn giữa theo trọng tâm độ sáng (Center of Mass).
    6. Chuẩn hóa pixel về [0.0, 1.0].
    
    Trả về:
    - input_tensor: mảng (1, 28, 28, 1) float32
    - preview_base64: chuỗi data URI của ảnh 28x28 phóng to để trực quan hóa
    """
    # Tự động phát hiện nền trắng chữ đen -> Đảo ngược màu
    # Nếu giá trị trung bình 4 góc > 127 thì nền đang là màu trắng/sáng
    h, w = gray_img.shape
    corners = [gray_img[0, 0], gray_img[0, -1], gray_img[-1, 0], gray_img[-1, -1]]
    if np.mean(corners) > 127:
        gray_img = cv2.bitwise_not(gray_img)

    # Khử nhiễu nhẹ
    gray_img = cv2.GaussianBlur(gray_img, (3, 3), 0)

    # Tìm ngưỡng Otsu để xác định vùng nét vẽ
    _, thresh = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Tìm bounding box của nét vẽ
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) > 0:
        # Lấy bounding box bao trọn tất cả nét vẽ
        x_min, y_min = w, h
        x_max, y_max = 0, 0
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + cw)
            y_max = max(y_max, y + ch)

        digit_crop = gray_img[y_min:y_max, x_min:x_max]
    else:
        digit_crop = gray_img

    ch, cw = digit_crop.shape
    if ch == 0 or cw == 0:
        # Trường hợp canvas trống rỗng
        clean_28 = np.zeros((28, 28), dtype=np.float32)
    else:
        # Co giãn vừa khít khung 20x20 giữ nguyên tỉ lệ
        if ch > cw:
            new_h = 20
            new_w = max(1, int(round((cw * 20.0) / ch)))
        else:
            new_w = 20
            new_h = max(1, int(round((ch * 20.0) / cw)))

        resized_digit = cv2.resize(digit_crop, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Đặt vào tâm khung 28x28
        canvas_28 = np.zeros((28, 28), dtype=np.uint8)
        start_y = (28 - new_h) // 2
        start_x = (28 - new_w) // 2
        canvas_28[start_y:start_y + new_h, start_x:start_x + new_w] = resized_digit

        # Căn trọng tâm (Center of mass)
        clean_28 = center_of_mass_shift(canvas_28).astype(np.float32) / 255.0

    # Reshape thành (1, 28, 28, 1) cho Keras model
    input_tensor = np.expand_dims(np.expand_dims(clean_28, axis=-1), axis=0)

    # Tạo ảnh preview Base64 phóng to (140x140) để hiển thị trực quan trên giao diện
    preview_img = (clean_28 * 255.0).astype(np.uint8)
    preview_large = cv2.resize(preview_img, (140, 140), interpolation=cv2.INTER_NEAREST)
    _, buffer = cv2.imencode(".png", preview_large)
    preview_base64 = "data:image/png;base64," + base64.b64encode(buffer).decode("utf-8")

    return input_tensor, preview_base64


def encode_cv2_to_base64(cv2_img: np.ndarray, format=".jpg") -> str:
    """Chuyển mảng OpenCV sang chuỗi data URI Base64"""
    _, buffer = cv2.imencode(format, cv2_img)
    return f"data:image/{format[1:]};base64," + base64.b64encode(buffer).decode("utf-8")
