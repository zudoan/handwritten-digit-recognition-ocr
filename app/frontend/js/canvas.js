/**
 * Canvas Studio - Bộ vẽ số tương tác cao cấp & Nhận diện thời gian thực
 */

class DrawingStudio {
  constructor() {
    this.canvas = document.getElementById("digitCanvas");
    this.wrapper = document.querySelector(".canvas-box-wrapper");
    this.ctx = this.canvas.getContext("2d");
    
    this.isDrawing = false;
    this.mode = "brush"; // "brush" hoặc "eraser"
    this.brushSize = 22;
    this.strokesHistory = [];
    this.autoPredictTimer = null;
    this.autoPredictEnabled = true;
    this.compareAllEnabled = false;
    this.lastPoint = null;

    this.initCanvasSize();
    this.bindEvents();
    this.renderEmptyProbabilities();
  }

  initCanvasSize() {
    // Độ phân giải nội bộ chuẩn (320x320)
    const rect = this.wrapper.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = 320;
    this.height = 320;

    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);

    this.clear(false);
  }

  bindEvents() {
    window.addEventListener("resize", () => {
      // Giữ nét vẽ khi resize
      const imgData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
      this.initCanvasSize();
      this.ctx.putImageData(imgData, 0, 0);
    });

    // Mouse events
    this.canvas.addEventListener("mousedown", (e) => this.startDrawing(e));
    window.addEventListener("mousemove", (e) => this.draw(e));
    window.addEventListener("mouseup", () => this.stopDrawing());

    // Touch events cho điện thoại/máy tính bảng
    this.canvas.addEventListener("touchstart", (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      this.startDrawing(touch);
    }, { passive: false });

    window.addEventListener("touchmove", (e) => {
      if (this.isDrawing) {
        e.preventDefault();
        const touch = e.touches[0];
        this.draw(touch);
      }
    }, { passive: false });

    window.addEventListener("touchend", () => this.stopDrawing());

    // Controls
    const strokeRange = document.getElementById("brushSizeRange");
    if (strokeRange) {
      strokeRange.addEventListener("input", (e) => {
        this.brushSize = parseInt(e.target.value);
        document.getElementById("brushSizeVal").textContent = `${this.brushSize}px`;
      });
    }

    const btnBrush = document.getElementById("btnToolBrush");
    const btnEraser = document.getElementById("btnToolEraser");
    if (btnBrush && btnEraser) {
      btnBrush.addEventListener("click", () => {
        this.mode = "brush";
        btnBrush.classList.add("active");
        btnEraser.classList.remove("active");
      });
      btnEraser.addEventListener("click", () => {
        this.mode = "eraser";
        btnEraser.classList.add("active");
        btnBrush.classList.remove("active");
      });
    }

    const btnClear = document.getElementById("btnClearCanvas");
    if (btnClear) {
      btnClear.addEventListener("click", () => this.clear(true));
    }

    const btnUndo = document.getElementById("btnUndoCanvas");
    if (btnUndo) {
      btnUndo.addEventListener("click", () => this.undo());
    }

    const btnPredict = document.getElementById("btnPredictCanvas");
    if (btnPredict) {
      btnPredict.addEventListener("click", () => this.predict(true));
    }

    const chkAuto = document.getElementById("chkAutoPredict");
    if (chkAuto) {
      chkAuto.addEventListener("change", (e) => {
        this.autoPredictEnabled = e.target.checked;
      });
    }

    const chkCompareAll = document.getElementById("chkCompareAll");
    if (chkCompareAll) {
      chkCompareAll.addEventListener("change", (e) => {
        this.compareAllEnabled = e.target.checked;
        const compSection = document.getElementById("comparisonCardSection");
        if (compSection) {
          compSection.style.display = this.compareAllEnabled ? "block" : "none";
        }
        if (this.hasDrawing()) {
          this.predict();
        }
      });
    }
  }

  getCanvasCoordinates(e) {
    const rect = this.canvas.getBoundingClientRect();
    const scaleX = this.width / rect.width;
    const scaleY = this.height / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY
    };
  }

  startDrawing(e) {
    this.isDrawing = true;
    this.wrapper.classList.add("drawing");
    this.saveState();
    
    const pt = this.getCanvasCoordinates(e);
    this.lastPoint = pt;

    this.ctx.beginPath();
    this.ctx.arc(pt.x, pt.y, this.brushSize / 2, 0, Math.PI * 2);
    this.ctx.fillStyle = this.mode === "brush" ? "#ffffff" : "#000000";
    this.ctx.fill();
  }

  draw(e) {
    if (!this.isDrawing) return;
    const currentPoint = this.getCanvasCoordinates(e);

    this.ctx.beginPath();
    this.ctx.moveTo(this.lastPoint.x, this.lastPoint.y);
    
    // Nối bằng quadratic curve để nét vẽ mượt mà không bị gãy góc
    const midPoint = {
      x: (this.lastPoint.x + currentPoint.x) / 2,
      y: (this.lastPoint.y + currentPoint.y) / 2
    };
    this.ctx.quadraticCurveTo(this.lastPoint.x, this.lastPoint.y, midPoint.x, midPoint.y);

    this.ctx.strokeStyle = this.mode === "brush" ? "#ffffff" : "#000000";
    this.ctx.lineWidth = this.brushSize;
    this.ctx.lineCap = "round";
    this.ctx.lineJoin = "round";
    this.ctx.stroke();

    this.lastPoint = currentPoint;
  }

  stopDrawing() {
    if (!this.isDrawing) return;
    this.isDrawing = false;
    this.wrapper.classList.remove("drawing");

    // Kích hoạt nhận diện tự động sau 350ms
    if (this.autoPredictEnabled && this.hasDrawing()) {
      clearTimeout(this.autoPredictTimer);
      this.autoPredictTimer = setTimeout(() => {
        this.predict(false);
      }, 350);
    }
  }

  saveState() {
    if (this.strokesHistory.length > 20) {
      this.strokesHistory.shift();
    }
    const dpr = window.devicePixelRatio || 1;
    this.strokesHistory.push(this.ctx.getImageData(0, 0, this.width * dpr, this.height * dpr));
  }

  undo() {
    if (this.strokesHistory.length > 0) {
      const prevState = this.strokesHistory.pop();
      this.ctx.putImageData(prevState, 0, 0);
      if (this.hasDrawing()) {
        this.predict();
      } else {
        this.resetResultsUI();
      }
    } else {
      this.clear(false);
    }
  }

  clear(resetUI = true) {
    this.ctx.fillStyle = "#000000";
    this.ctx.fillRect(0, 0, this.width, this.height);
    this.strokesHistory = [];
    if (resetUI) {
      this.resetResultsUI();
    }
  }

  hasDrawing() {
    // Kiểm tra xem canvas có pixel nào khác màu đen không
    const dpr = window.devicePixelRatio || 1;
    const imgData = this.ctx.getImageData(0, 0, this.width * dpr, this.height * dpr);
    const data = imgData.data;
    for (let i = 0; i < data.length; i += 4) {
      if (data[i] > 30 || data[i + 1] > 30 || data[i + 2] > 30) {
        return true;
      }
    }
    return false;
  }

  async predict(force = false) {
    if (!this.hasDrawing()) {
      this.resetResultsUI();
      return;
    }

    const currentModel = window.appState ? window.appState.currentModelId : "standard_cnn";
    const dataUrl = this.canvas.toDataURL("image/png");

    // Đổi màu hiển thị tạm thời sang trạng thái đang phân tích
    const digitEl = document.getElementById("predDigit");
    if (digitEl && force) {
      digitEl.style.opacity = "0.5";
    }

    try {
      const res = await ApiService.predictCanvas(dataUrl, currentModel, this.compareAllEnabled);
      if (res && res.success) {
        this.renderResults(res);
      }
    } catch (err) {
      console.error("Lỗi suy luận canvas:", err);
    } finally {
      if (digitEl) {
        digitEl.style.opacity = "1";
      }
    }
  }

  renderResults(data) {
    const result = data.primary_result || data.result;
    if (!result) return;

    // 1. Chữ số lớn
    const digitEl = document.getElementById("predDigit");
    if (digitEl) {
      digitEl.textContent = result.predicted_digit;
    }

    // 2. Độ tin cậy
    const confValEl = document.getElementById("confidenceVal");
    const confBarEl = document.getElementById("confidenceBar");
    if (confValEl && confBarEl) {
      confValEl.textContent = `${result.confidence.toFixed(1)}%`;
      confBarEl.style.width = `${result.confidence}%`;
    }

    // 3. Tên mô hình & Độ trễ
    const modelTagEl = document.getElementById("activeModelBadge");
    if (modelTagEl) {
      modelTagEl.textContent = `${result.model_name} (${result.badge || ''})`;
    }
    const latencyEl = document.getElementById("inferenceLatencyVal");
    if (latencyEl) {
      latencyEl.textContent = `${result.latency_ms} ms`;
    }

    // 4. Ảnh AI Receptive Field 28x28
    const previewImg = document.getElementById("receptiveFieldImg");
    if (previewImg && data.preview_image) {
      previewImg.src = data.preview_image;
    }

    // 5. Cột xác suất 10 chữ số
    if (result.probabilities) {
      this.renderProbabilitiesList(result.probabilities, result.predicted_digit);
    }

    // 6. Bảng đối sánh 5 mô hình (nếu bật)
    if (data.comparison && this.compareAllEnabled) {
      this.renderComparisonTable(data.comparison);
    }

    // Lưu vào lịch sử
    if (window.HistoryManager) {
      window.HistoryManager.addRecord({
        source: "canvas",
        digit: result.predicted_digit,
        confidence: result.confidence,
        model: result.model_name,
        thumbnail: data.preview_image || this.canvas.toDataURL("image/png")
      });
    }
  }

  renderProbabilitiesList(probabilities, winnerDigit) {
    const container = document.getElementById("probBarsContainer");
    if (!container) return;

    let html = "";
    probabilities.forEach((p) => {
      const isWinner = p.digit === winnerDigit;
      html += `
        <div class="prob-bar-row">
          <span class="prob-digit-tag ${isWinner ? 'highlight' : ''}">${p.digit}</span>
          <div class="prob-track">
            <div class="prob-fill ${isWinner ? 'winner' : ''}" style="width: ${p.probability}%"></div>
          </div>
          <span class="prob-value ${isWinner ? 'winner' : ''}">${p.probability.toFixed(1)}%</span>
        </div>
      `;
    });
    container.innerHTML = html;
  }

  renderEmptyProbabilities() {
    const emptyProbs = Array.from({ length: 10 }, (_, i) => ({ digit: i, probability: 0 }));
    this.renderProbabilitiesList(emptyProbs, -1);
  }

  renderComparisonTable(comparisonList) {
    const tbody = document.getElementById("compareTableBody");
    if (!tbody) return;

    let html = "";
    comparisonList.forEach((item) => {
      if (item.error) {
        html += `
          <tr>
            <td><strong>${item.model_name}</strong></td>
            <td colspan="4" style="color: var(--accent-rose);">${item.error}</td>
          </tr>
        `;
      } else {
        html += `
          <tr>
            <td><strong>${item.model_name}</strong></td>
            <td><span class="badge-winner">${item.predicted_digit}</span></td>
            <td><strong>${item.confidence.toFixed(1)}%</strong></td>
            <td><span class="mono">${item.latency_ms} ms</span></td>
            <td><span class="mono">${item.model_specs.size_mb} MB</span></td>
          </tr>
        `;
      }
    });
    tbody.innerHTML = html;
  }

  resetResultsUI() {
    const digitEl = document.getElementById("predDigit");
    if (digitEl) digitEl.textContent = "-";

    const confValEl = document.getElementById("confidenceVal");
    const confBarEl = document.getElementById("confidenceBar");
    if (confValEl && confBarEl) {
      confValEl.textContent = "0.0%";
      confBarEl.style.width = "0%";
    }

    const latencyEl = document.getElementById("inferenceLatencyVal");
    if (latencyEl) latencyEl.textContent = "0.00 ms";

    this.renderEmptyProbabilities();
  }
}

// Khởi tạo toàn cục khi DOM sẵn sàng
document.addEventListener("DOMContentLoaded", () => {
  window.drawingStudio = new DrawingStudio();
});
