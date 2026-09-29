/**
 * Webcam Scanner - Quét chữ số viết tay trực tiếp qua Camera
 */

class WebcamScanner {
  constructor() {
    this.video = document.getElementById("webcamVideo");
    this.btnStart = document.getElementById("btnStartWebcam");
    this.btnCapture = document.getElementById("btnCaptureWebcam");
    this.statusEl = document.getElementById("webcamStatus");
    this.resultContainer = document.getElementById("webcamResultCard");
    this.resultDigitEl = document.getElementById("webcamPredDigit");
    this.resultConfEl = document.getElementById("webcamPredConf");

    this.stream = null;
    this.isCameraActive = false;

    this.bindEvents();
  }

  bindEvents() {
    if (!this.btnStart) return;

    this.btnStart.addEventListener("click", () => {
      if (this.isCameraActive) {
        this.stopCamera();
      } else {
        this.startCamera();
      }
    });

    if (this.btnCapture) {
      this.btnCapture.addEventListener("click", () => this.captureAndScan());
    }
  }

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: "environment"
        }
      });
      this.video.srcObject = this.stream;
      this.video.play();
      this.isCameraActive = true;

      this.btnStart.innerHTML = `<i class="fa-solid fa-video-slash"></i> Tắt Camera`;
      this.btnStart.classList.add("btn-secondary");
      this.btnStart.classList.remove("btn-primary");
      if (this.btnCapture) this.btnCapture.disabled = false;
      if (this.statusEl) this.statusEl.textContent = "Camera đang hoạt động. Căn chỉnh chữ số vào khung ngắm.";
    } catch (err) {
      console.error("Lỗi khởi tạo Webcam:", err);
      alert("Không thể truy cập Camera. Vui lòng cấp quyền truy cập thiết bị!");
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach((track) => track.stop());
      this.stream = null;
    }
    this.video.srcObject = null;
    this.isCameraActive = false;

    this.btnStart.innerHTML = `<i class="fa-solid fa-camera"></i> Bật Camera`;
    this.btnStart.classList.add("btn-primary");
    this.btnStart.classList.remove("btn-secondary");
    if (this.btnCapture) this.btnCapture.disabled = true;
    if (this.statusEl) this.statusEl.textContent = "Camera đang tắt.";
  }

  async captureAndScan() {
    if (!this.isCameraActive) return;

    // Chụp khung hình từ video sang Canvas ẩn
    const canvas = document.createElement("canvas");
    canvas.width = this.video.videoWidth || 640;
    canvas.height = this.video.videoHeight || 480;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(this.video, 0, 0, canvas.width, canvas.height);

    const base64Data = canvas.toDataURL("image/jpeg", 0.9);
    const currentModel = window.appState ? window.appState.currentModelId : "standard_cnn";

    this.btnCapture.disabled = true;
    this.btnCapture.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Đang phân tích...`;

    try {
      const data = await ApiService.scanWebcam(base64Data, currentModel);
      if (data && data.success) {
        if (this.resultContainer) this.resultContainer.style.display = "block";
        if (this.resultDigitEl) this.resultDigitEl.textContent = data.full_text || "-";
        if (this.resultConfEl) this.resultConfEl.textContent = `Độ tin cậy: ${data.avg_confidence}% (Thời gian: ${data.latency_ms}ms)`;

        if (window.HistoryManager && data.full_text) {
          window.HistoryManager.addRecord({
            source: "webcam",
            digit: data.full_text,
            confidence: data.avg_confidence,
            model: data.model_used,
            thumbnail: data.annotated_image
          });
        }
      }
    } catch (err) {
      console.error("Lỗi scan webcam:", err);
      alert("Lỗi phân tích hình ảnh webcam: " + err.message);
    } finally {
      this.btnCapture.disabled = false;
      this.btnCapture.innerHTML = `<i class="fa-solid fa-bolt"></i> Chụp & Nhận Diện`;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.webcamScanner = new WebcamScanner();
});
