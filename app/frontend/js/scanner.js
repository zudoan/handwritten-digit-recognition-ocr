/**
 * Scanner Studio - Quét ảnh tài liệu & Nhận diện chuỗi chữ số viết tay (OCR)
 */

class DocumentScanner {
  constructor() {
    this.uploadZone = document.getElementById("ocrUploadZone");
    this.fileInput = document.getElementById("ocrFileInput");
    this.annotatedImg = document.getElementById("ocrAnnotatedImg");
    this.extractedTextEl = document.getElementById("ocrExtractedText");
    this.digitsCountEl = document.getElementById("ocrDigitsCount");
    this.avgConfidenceEl = document.getElementById("ocrAvgConfidence");
    this.ocrLatencyEl = document.getElementById("ocrLatency");
    this.segmentedListEl = document.getElementById("ocrSegmentedList");
    this.scanBtn = document.getElementById("btnTriggerScan");
    this.samplesContainer = document.getElementById("ocrSamplesList");

    this.currentFile = null;
    this.currentBase64 = null;

    this.bindEvents();
    this.loadSampleImages();
  }

  bindEvents() {
    if (!this.uploadZone) return;

    // Click mở file dialog
    this.uploadZone.addEventListener("click", () => this.fileInput.click());

    // File input change
    this.fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        this.handleFileSelected(e.target.files[0]);
      }
    });

    // Drag and drop
    this.uploadZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      this.uploadZone.classList.add("dragover");
    });

    this.uploadZone.addEventListener("dragleave", () => {
      this.uploadZone.classList.remove("dragover");
    });

    this.uploadZone.addEventListener("drop", (e) => {
      e.preventDefault();
      this.uploadZone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        this.handleFileSelected(e.dataTransfer.files[0]);
      }
    });

    // Nút kích hoạt quét lại
    if (this.scanBtn) {
      this.scanBtn.addEventListener("click", () => this.scan());
    }
  }

  async loadSampleImages() {
    try {
      const res = await ApiService.getSampleImages();
      if (res && res.samples && res.samples.length > 0) {
        let html = "";
        res.samples.forEach((s) => {
          html += `
            <button class="sample-chip" data-url="${s.url}" data-name="${s.name}">
              <i class="fa-solid fa-image"></i> ${s.name}
            </button>
          `;
        });
        if (this.samplesContainer) {
          this.samplesContainer.innerHTML = html;
          // Gắn sự kiện click mẫu
          this.samplesContainer.querySelectorAll(".sample-chip").forEach((chip) => {
            chip.addEventListener("click", () => {
              const url = chip.getAttribute("data-url");
              this.loadSampleFromUrl(url);
            });
          });
        }
      }
    } catch (e) {
      console.warn("Không thể tải danh sách ảnh mẫu:", e);
    }
  }

  async loadSampleFromUrl(url) {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const file = new File([blob], "sample.png", { type: "image/png" });
      this.handleFileSelected(file);
    } catch (e) {
      console.error("Lỗi tải ảnh mẫu:", e);
    }
  }

  handleFileSelected(file) {
    this.currentFile = file;
    this.currentBase64 = null;

    // Xem trước ảnh gốc
    const reader = new FileReader();
    reader.onload = (e) => {
      if (this.annotatedImg) {
        this.annotatedImg.src = e.target.result;
        this.annotatedImg.style.display = "block";
      }
      // Tự động quét luôn
      this.scan();
    };
    reader.readAsDataURL(file);
  }

  async scan() {
    if (!this.currentFile && !this.currentBase64) {
      alert("Vui lòng chọn hoặc kéo thả một hình ảnh trước!");
      return;
    }

    const currentModel = window.appState ? window.appState.currentModelId : "standard_cnn";
    this.showLoading(true);

    try {
      const data = await ApiService.scanImage({
        file: this.currentFile,
        base64: this.currentBase64,
        modelId: currentModel
      });

      if (data && data.success) {
        this.renderScanResults(data);
      }
    } catch (err) {
      console.error("Lỗi quét OCR:", err);
      alert("Lỗi khi quét ảnh OCR: " + err.message);
    } finally {
      this.showLoading(false);
    }
  }

  renderScanResults(data) {
    // 1. Ảnh có gắn nhãn Bounding Boxes
    if (this.annotatedImg && data.annotated_image) {
      this.annotatedImg.src = data.annotated_image;
      this.annotatedImg.style.display = "block";
    }

    // 2. Chuỗi chữ số nhận diện
    if (this.extractedTextEl) {
      this.extractedTextEl.textContent = data.full_text || "Không phát hiện chữ số";
    }

    // 3. Thông số tổng quát
    if (this.digitsCountEl) {
      this.digitsCountEl.textContent = data.total_detected;
    }
    if (this.avgConfidenceEl) {
      this.avgConfidenceEl.textContent = `${data.avg_confidence}%`;
    }
    if (this.ocrLatencyEl) {
      this.ocrLatencyEl.textContent = `${data.latency_ms} ms`;
    }

    // 4. Danh sách các chữ số đã bóc tách
    if (this.segmentedListEl && data.digits) {
      let html = "";
      data.digits.forEach((d) => {
        html += `
          <div class="digit-card-pill">
            <img src="${d.thumbnail}" alt="Số ${d.digit}" />
            <span class="pill-value">${d.digit}</span>
            <span class="pill-conf">${d.confidence.toFixed(1)}%</span>
          </div>
        `;
      });
      this.segmentedListEl.innerHTML = html;
    }

    // Lưu vào lịch sử
    if (window.HistoryManager && data.full_text) {
      window.HistoryManager.addRecord({
        source: "ocr",
        digit: data.full_text,
        confidence: data.avg_confidence,
        model: data.model_used,
        thumbnail: data.annotated_image
      });
    }
  }

  showLoading(loading) {
    if (this.scanBtn) {
      this.scanBtn.disabled = loading;
      this.scanBtn.innerHTML = loading
        ? `<i class="fa-solid fa-spinner fa-spin"></i> Đang quét AI...`
        : `<i class="fa-solid fa-bolt"></i> Quét Lại Ngay`;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.documentScanner = new DocumentScanner();
});
