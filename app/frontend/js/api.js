/**
 * API Service Client giao tiếp với FastAPI Backend
 */

const API_BASE = window.location.origin;

const ApiService = {
  /**
   * Kiểm tra sức khỏe máy chủ
   */
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      return await res.json();
    } catch (err) {
      console.error("Health check error:", err);
      return { status: "offline", error: err.message };
    }
  },

  /**
   * Lấy danh sách 5 kiến trúc mô hình và thông số
   */
  async getModels() {
    try {
      const res = await fetch(`${API_BASE}/api/models`);
      return await res.json();
    } catch (err) {
      console.error("Get models error:", err);
      return { models: [] };
    }
  },

  /**
   * Lấy dữ liệu đối chuẩn Benchmark & Biểu đồ
   */
  async getBenchmark() {
    try {
      const res = await fetch(`${API_BASE}/api/benchmark`);
      return await res.json();
    } catch (err) {
      console.error("Get benchmark error:", err);
      return null;
    }
  },

  /**
   * Lấy danh sách ảnh mẫu kiểm thử OCR
   */
  async getSampleImages() {
    try {
      const res = await fetch(`${API_BASE}/api/sample-images`);
      return await res.json();
    } catch (err) {
      console.error("Get samples error:", err);
      return { samples: [] };
    }
  },

  /**
   * Dự đoán chữ số vẽ từ Canvas
   */
  async predictCanvas(imageBase64, modelId = "standard_cnn", compareAll = false) {
    const res = await fetch(`${API_BASE}/api/predict/canvas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: imageBase64,
        model_id: modelId,
        compare_all: compareAll
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Lỗi khi dự đoán canvas");
    }
    return await res.json();
  },

  /**
   * Quét và nhận diện ảnh tài liệu OCR (File hoặc Base64)
   */
  async scanImage({ file, base64, modelId = "standard_cnn" }) {
    let res;
    if (file) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_id", modelId);
      res = await fetch(`${API_BASE}/api/scan/image`, {
        method: "POST",
        body: formData
      });
    } else if (base64) {
      const formData = new FormData();
      formData.append("image_base64", base64);
      formData.append("model_id", modelId);
      res = await fetch(`${API_BASE}/api/scan/image`, {
        method: "POST",
        body: formData
      });
    } else {
      throw new Error("Không có ảnh để quét!");
    }

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Lỗi khi quét ảnh OCR");
    }
    return await res.json();
  },

  /**
   * Quét ảnh chụp từ Webcam
   */
  async scanWebcam(imageBase64, modelId = "standard_cnn") {
    const res = await fetch(`${API_BASE}/api/scan/webcam`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image: imageBase64,
        model_id: modelId
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Lỗi khi quét webcam");
    }
    return await res.json();
  }
};
