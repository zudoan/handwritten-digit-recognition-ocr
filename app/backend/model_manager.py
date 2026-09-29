"""
Quản lý vòng đời, nạp và thực thi suy luận (Inference) cho cả 5 mô hình Deep Learning.
"""

import os
import time
import numpy as np
import tensorflow as tf
import keras
from keras import layers
from app.backend.benchmark_data import BENCHMARK_MODELS

# Định nghĩa Custom Layer phục vụ nạp mô hình Mini-ViT
@keras.saving.register_keras_serializable(package="Custom", name="PatchExtractAndEmbed")
class PatchExtractAndEmbed(layers.Layer):
    """Cắt ảnh thành các patch kích thước patch_size x patch_size và chiếu tuyến tính sang d_model"""
    def __init__(self, patch_size=4, d_model=64, **kwargs):
        super().__init__(**kwargs)
        self.patch_size = patch_size
        self.d_model = d_model
        self.num_patches = (28 // patch_size) ** 2
        self.projection = layers.Dense(d_model)
        self.position_embedding = layers.Embedding(input_dim=self.num_patches, output_dim=d_model)

    def call(self, images):
        batch_size = tf.shape(images)[0]
        patches = tf.image.extract_patches(
            images=images,
            sizes=[1, self.patch_size, self.patch_size, 1],
            strides=[1, self.patch_size, self.patch_size, 1],
            rates=[1, 1, 1, 1],
            padding="VALID",
        )
        patch_dims = patches.shape[-1]
        patches = tf.reshape(patches, [batch_size, self.num_patches, patch_dims])
        encoded_patches = self.projection(patches)
        positions = tf.range(start=0, limit=self.num_patches, delta=1)
        encoded_patches = encoded_patches + self.position_embedding(positions)
        return encoded_patches

    def get_config(self):
        config = super().get_config()
        config.update({
            "patch_size": self.patch_size,
            "d_model": self.d_model,
        })
        return config


class ModelManager:
    """Quản lý các mô hình AI và thực hiện suy luận đa kiến trúc"""
    
    def __init__(self, models_dir=None):
        self.loaded_models = {}
        self.default_model_id = "standard_cnn"
        
        # Danh sách các thư mục tiềm năng chứa mô hình
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidate_dirs = [
            models_dir if models_dir else None,
            os.path.join(base_dir, "models", "saved_models_benchmark"),
            os.path.join(base_dir, "models"),
            os.path.join(base_dir, "saved_models_benchmark"),
            "saved_models_benchmark",
            "models"
        ]
        self.models_dir = next((os.path.abspath(d) for d in candidate_dirs if d and os.path.exists(d)), "saved_models_benchmark")

    def find_model_path(self, filename: str) -> str:
        """Tìm đường dẫn tệp mô hình trong các vị trí cấu hình"""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidates = [
            os.path.join(self.models_dir, filename),
            os.path.join(base_dir, "models", "saved_models_benchmark", filename),
            os.path.join(base_dir, "models", filename),
            os.path.join(base_dir, "saved_models_benchmark", filename),
            os.path.join(base_dir, filename),
            filename
        ]
        for p in candidates:
            if os.path.exists(p):
                return os.path.abspath(p)
        return os.path.join(self.models_dir, filename)

    def load_model(self, model_id: str):
        """Nạp một mô hình cụ thể vào bộ nhớ RAM"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]
            
        if model_id not in BENCHMARK_MODELS:
            model_id = self.default_model_id
            
        meta = BENCHMARK_MODELS[model_id]
        model_path = self.find_model_path(meta["filename"])
        
        # Nếu là mô hình tốt nhất, có thể dùng file best_handwritten_model.keras
        if not os.path.exists(model_path) and model_id == "standard_cnn":
            model_path = self.find_model_path("best_handwritten_model.keras")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy file mô hình tại {model_path}")

        print(f"[MODEL] Dang nap mo hinh: {meta['name']} tu {model_path}...")
        
        custom_objects = {"PatchExtractAndEmbed": PatchExtractAndEmbed}
        with keras.saving.custom_object_scope(custom_objects):
            model = keras.models.load_model(model_path, custom_objects=custom_objects)
            
        # Khởi động (Warm-up) để các lần suy luận sau đạt tốc độ tối đa
        dummy_input = np.zeros((1, 28, 28, 1), dtype=np.float32)
        _ = model.predict(dummy_input, verbose=0)
        
        self.loaded_models[model_id] = model
        print(f"[OK] Nap thanh cong mo hinh [{model_id}] ({model.count_params()} params)!")
        return model

    def preload_all(self):
        """Khởi động và nạp sẵn tất cả 5 mô hình để phục vụ chức năng so sánh tức thì"""
        print("[INIT] Dang nap san tat ca 5 mo hinh Deep Learning...")
        for m_id in BENCHMARK_MODELS.keys():
            try:
                self.load_model(m_id)
            except Exception as e:
                print(f"[WARN] Khong the nap mo hinh {m_id}: {e}")

    def predict_single(self, input_tensor: np.ndarray, model_id: str = "standard_cnn") -> dict:
        """
        Dự đoán chữ số từ tensor (1, 28, 28, 1) với một mô hình chỉ định.
        Trả về: digit, confidence, probabilities list, latency_ms, model_info.
        """
        if model_id not in BENCHMARK_MODELS:
            model_id = self.default_model_id
            
        model = self.load_model(model_id)
        meta = BENCHMARK_MODELS[model_id]
        
        start_time = time.perf_counter()
        preds = model.predict(input_tensor, verbose=0)[0]
        latency_ms = (time.perf_counter() - start_time) * 1000
        
        predicted_digit = int(np.argmax(preds))
        confidence = float(preds[predicted_digit]) * 100.0
        
        # Danh sách phân bố xác suất cho cả 10 chữ số
        probabilities = [
            {
                "digit": int(i),
                "probability": float(round(p * 100.0, 2))
            }
            for i, p in enumerate(preds)
        ]
        # Sắp xếp top các số có xác suất cao nhất
        top_candidates = sorted(probabilities, key=lambda x: x["probability"], reverse=True)
        
        return {
            "model_id": model_id,
            "model_name": meta["short_name"],
            "badge": meta["badge"],
            "predicted_digit": predicted_digit,
            "confidence": round(confidence, 2),
            "latency_ms": round(latency_ms, 2),
            "probabilities": probabilities,
            "top_candidates": top_candidates[:3],
            "model_specs": {
                "accuracy": meta["accuracy"],
                "parameters": meta["parameters"],
                "size_mb": meta["model_size_mb"]
            }
        }

    def predict_all_models(self, input_tensor: np.ndarray) -> list:
        """
        Chạy đầu vào đồng thời qua cả 5 kiến trúc để đối sánh kết quả trực tiếp.
        """
        results = []
        for m_id in BENCHMARK_MODELS.keys():
            try:
                res = self.predict_single(input_tensor, m_id)
                results.append(res)
            except Exception as e:
                meta = BENCHMARK_MODELS[m_id]
                results.append({
                    "model_id": m_id,
                    "model_name": meta["short_name"],
                    "error": str(e)
                })
        return results


# Khởi tạo singleton manager
model_manager = ModelManager()
