"""
FastAPI Backend Server cho Hệ thống Nhận diện & Quét Chữ số Viết tay Đa Kiến trúc.
Cung cấp API RESTful cho Canvas vẽ trực tiếp, OCR quét tài liệu, Webcam và Bảng đối chuẩn.
"""

import os
import glob
import base64
import cv2
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

from app.backend.benchmark_data import BENCHMARK_MODELS, BENCHMARK_LEADERBOARD
from app.backend.model_manager import model_manager
from app.backend.image_processing import (
    decode_base64_image,
    preprocess_digit_image,
    encode_cv2_to_base64
)
from app.backend.scanner_ocr import scan_and_recognize_digits


# Schema dữ liệu yêu cầu
class CanvasPredictRequest(BaseModel):
    image: str                      # Chuỗi Base64 Data URI của Canvas
    model_id: Optional[str] = "standard_cnn"
    compare_all: Optional[bool] = False


class ImageBase64ScanRequest(BaseModel):
    image: str                      # Chuỗi Base64 ảnh tài liệu / ảnh chụp
    model_id: Optional[str] = "standard_cnn"


# Vòng đời ứng dụng (Lifespan event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi động trước mô hình mặc định (Standard CNN)
    print("[SERVER BOOT] Khoi tao may chu AI Vision...")
    try:
        model_manager.load_model("standard_cnn")
    except Exception as e:
        print(f"[WARN] Chua the preload Standard CNN: {e}")
    yield
    print("[SERVER SHUTDOWN] Dang dong may chu...")


app = FastAPI(
    title="Handwritten Digit Recognition & OCR Multi-Architecture Platform",
    description="Hệ thống AI nhận diện chữ số viết tay và quét ảnh tài liệu với 5 họ kiến trúc Deep Learning",
    version="2.0.0",
    lifespan=lifespan
)

# Cấu hình CORS mở để frontend kết nối mượt mà từ bất kỳ host/port nào
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thư mục gốc dự án
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FRONTEND_DIR = os.path.join(BASE_DIR, "app", "frontend")
STATIC_DIR = os.path.join(BASE_DIR, "app", "static")


# ====================================================================
# API ENDPOINTS
# ====================================================================

@app.get("/api/health")
async def health_check():
    """Kiểm tra tình trạng hoạt động của máy chủ và các mô hình đã nạp"""
    import tensorflow as tf
    import keras
    return {
        "status": "online",
        "message": "AI Vision Server đang hoạt động ổn định",
        "tensorflow_version": tf.__version__,
        "keras_version": keras.__version__,
        "loaded_models": list(model_manager.loaded_models.keys()),
        "available_models_count": len(BENCHMARK_MODELS)
    }


@app.get("/api/models")
async def get_models():
    """Lấy danh sách tất cả các mô hình có sẵn kèm thông số kỹ thuật"""
    return {
        "default_model": model_manager.default_model_id,
        "models": list(BENCHMARK_MODELS.values())
    }


@app.get("/api/benchmark")
async def get_benchmark_report():
    """Lấy dữ liệu đối chuẩn chi tiết cho bảng so sánh và biểu đồ Chart.js"""
    chart_data = {
        "labels": [m["short_name"] for m in BENCHMARK_LEADERBOARD],
        "accuracies": [m["accuracy"] for m in BENCHMARK_LEADERBOARD],
        "parameters": [m["parameters"] for m in BENCHMARK_LEADERBOARD],
        "model_sizes_mb": [m["model_size_mb"] for m in BENCHMARK_LEADERBOARD],
        "latencies_ms": [m["latency_ms"] for m in BENCHMARK_LEADERBOARD],
        "training_times_s": [m["training_time_s"] for m in BENCHMARK_LEADERBOARD],
    }
    return {
        "leaderboard": BENCHMARK_LEADERBOARD,
        "chart_data": chart_data
    }


@app.get("/api/sample-images")
async def get_sample_images():
    """Lấy danh sách ảnh mẫu có sẵn để người dùng test nhanh chức năng OCR"""
    samples_dir = os.path.join(STATIC_DIR, "samples")
    samples = []
    
    if os.path.exists(samples_dir):
        for f in os.listdir(samples_dir):
            if f.endswith((".png", ".jpg", ".jpeg")):
                samples.append({
                    "name": f.replace(".png", "").replace("_", " ").title(),
                    "filename": f,
                    "url": f"/static/samples/{f}"
                })
    return {"samples": samples}


@app.post("/api/predict/canvas")
async def predict_canvas(payload: CanvasPredictRequest):
    """
    Dự đoán nét vẽ từ Canvas:
    - Tiền xử lý theo chuẩn MNIST (trọng tâm, căn giữa, 28x28)
    - Dự đoán với mô hình đã chọn HOẶC chạy đồng thời cả 5 mô hình để so sánh
    """
    if not payload.image:
        raise HTTPException(status_code=400, detail="Thiếu dữ liệu ảnh canvas!")

    try:
        # Giải mã ảnh canvas
        gray_img = decode_base64_image(payload.image)
        
        # Tiền xử lý MNIST chuẩn
        input_tensor, preview_base64 = preprocess_digit_image(gray_img)

        # Chế độ so sánh cả 5 mô hình
        if payload.compare_all:
            all_results = model_manager.predict_all_models(input_tensor)
            primary_res = next((r for r in all_results if r.get("model_id") == payload.model_id), all_results[0])
            return {
                "success": True,
                "preview_image": preview_base64,
                "primary_result": primary_res,
                "comparison": all_results
            }
        else:
            # Chế độ đơn mô hình
            result = model_manager.predict_single(input_tensor, payload.model_id)
            return {
                "success": True,
                "preview_image": preview_base64,
                "result": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý dự đoán: {str(e)}")


from fastapi import Request

@app.post("/api/scan/image")
async def scan_uploaded_image(
    request: Request,
    file: Optional[UploadFile] = File(None),
    model_id: Optional[str] = Form("standard_cnn"),
    image_base64: Optional[str] = Form(None)
):
    """
    Quét ảnh tài liệu tải lên (Multi-digit OCR Scanner):
    - Hỗ trợ cả Multipart Form-data (File upload) và JSON body (Base64)
    - Tự động bóc tách các chữ số riêng biệt
    - Nhận diện toàn bộ chuỗi số
    - Trả về ảnh có gắn bounding boxes và nhãn dự đoán trực quan
    """
    try:
        img_bgr = None
        content_type = request.headers.get("content-type", "")

        # 1. Trường hợp gửi JSON
        if "application/json" in content_type:
            body = await request.json()
            b64_str = body.get("image") or body.get("image_base64")
            m_id = body.get("model_id", "standard_cnn")
            if not b64_str:
                raise HTTPException(status_code=400, detail="Thiếu trường image hoặc image_base64 trong JSON!")
            gray = decode_base64_image(b64_str)
            img_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            return scan_and_recognize_digits(img_bgr, model_id=m_id)

        # 2. Trường hợp gửi Multipart Form-data
        if file is not None:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        elif image_base64 is not None:
            gray = decode_base64_image(image_base64)
            img_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Vui lòng cung cấp file ảnh hoặc chuỗi Base64 hợp lệ!")

        # Quét và nhận diện
        scan_result = scan_and_recognize_digits(img_bgr, model_id=model_id or "standard_cnn")
        return scan_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi quét ảnh OCR: {str(e)}")


@app.post("/api/scan/webcam")
async def scan_webcam_snapshot(payload: ImageBase64ScanRequest):
    """Quét ảnh chụp từ Webcam trực tiếp"""
    try:
        gray = decode_base64_image(payload.image)
        img_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        scan_result = scan_and_recognize_digits(img_bgr, model_id=payload.model_id)
        return scan_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý ảnh webcam: {str(e)}")


# ====================================================================
# PHỤC VỤ STATIC ASSETS & GIAO DIỆN WEB (SPA)
# ====================================================================

# Mount thư mục static phục vụ ảnh mẫu
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Mount thư mục frontend phục vụ css, js, assets
if os.path.exists(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
    if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        """Phục vụ trang chủ Frontend SPA"""
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({"message": "Frontend chưa được khởi tạo. Vui lòng kiểm tra app/frontend/index.html"})
