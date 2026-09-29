/**
 * Main Application Orchestrator: Quản lý Tabs, Model Selector, Lịch sử & Âm thanh
 */

window.appState = {
  currentModelId: "standard_cnn",
  currentTab: "canvas",
  soundEnabled: true
};

// Web Audio API Synthesizer (Hiệu ứng âm thanh tinh tế không cần file mp3)
class SoundFX {
  constructor() {
    this.ctx = null;
  }
  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }
  playBeep(freq = 600, duration = 0.08) {
    if (!window.appState.soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {}
  }
}
const sfx = new SoundFX();


// History Management (Lịch sử dự đoán lưu tại LocalStorage)
const HistoryManager = {
  storageKey: "neuralvision_history_v2",

  getRecords() {
    try {
      const raw = localStorage.getItem(this.storageKey);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  },

  addRecord(item) {
    const records = this.getRecords();
    const newRecord = {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      date: new Date().toLocaleDateString("vi-VN"),
      source: item.source || "canvas",
      digit: item.digit,
      confidence: item.confidence,
      model: item.model,
      thumbnail: item.thumbnail
    };
    records.unshift(newRecord);
    // Giữ tối đa 40 bản ghi gần nhất
    if (records.length > 40) records.pop();
    localStorage.setItem(this.storageKey, JSON.stringify(records));
    this.renderHistoryGrid();
  },

  clear() {
    localStorage.removeItem(this.storageKey);
    this.renderHistoryGrid();
  },

  renderHistoryGrid() {
    const container = document.getElementById("historyGridContainer");
    if (!container) return;

    const records = this.getRecords();
    if (records.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 48px; color: var(--text-dim);">
          <i class="fa-solid fa-clock-rotate-left" style="font-size: 36px; margin-bottom: 12px; opacity: 0.5;"></i>
          <p>Chưa có lịch sử nhận diện nào. Hãy vẽ trên Canvas hoặc Quét ảnh để ghi lại kết quả!</p>
        </div>
      `;
      return;
    }

    let html = "";
    records.forEach((r) => {
      html += `
        <div class="history-item-card">
          <div class="history-thumb">
            <img src="${r.thumbnail}" alt="Số ${r.digit}" />
          </div>
          <div class="history-meta">
            <div>
              <span class="history-pred-digit">${r.digit}</span>
              <div style="font-size: 0.7rem; color: var(--accent-cyan); font-weight: 600;">${r.confidence ? r.confidence.toFixed(1) + '%' : ''}</div>
            </div>
            <div style="text-align: right;">
              <span class="mini-pill" style="font-size: 0.65rem;">${r.source.toUpperCase()}</span>
              <div class="history-time">${r.timestamp}</div>
            </div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  },

  exportJSON() {
    const records = this.getRecords();
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(records, null, 2));
    const a = document.createElement("a");
    a.setAttribute("href", dataStr);
    a.setAttribute("download", `neuralvision_history_${Date.now()}.json`);
    a.click();
  },

  exportCSV() {
    const records = this.getRecords();
    if (records.length === 0) return alert("Không có dữ liệu lịch sử để xuất!");
    let csv = "ID,ThoiGian,Ngay,Nguon,ChuSo,DoTinCey,MoHinh\n";
    records.forEach((r) => {
      csv += `${r.id},"${r.timestamp}","${r.date}","${r.source}","${r.digit}",${r.confidence},"${r.model}"\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.setAttribute("href", url);
    a.setAttribute("download", `neuralvision_history_${Date.now()}.csv`);
    a.click();
  }
};
window.HistoryManager = HistoryManager;


// Khởi tạo Ứng dụng khi DOM sẵn sàng
document.addEventListener("DOMContentLoaded", async () => {
  // 1. Quản lý chuyển đổi Tabs
  const tabButtons = document.querySelectorAll(".nav-tab-btn");
  const tabViews = document.querySelectorAll(".tab-view");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetTab = btn.getAttribute("data-tab");
      window.appState.currentTab = targetTab;
      sfx.playBeep(800, 0.04);

      tabButtons.forEach((b) => b.classList.remove("active"));
      tabViews.forEach((v) => v.classList.remove("active"));

      btn.classList.add("active");
      const targetView = document.getElementById(`view-${targetTab}`);
      if (targetView) targetView.classList.add("active");

      // Nếu chuyển sang tab Benchmark, khởi tạo biểu đồ Chart.js
      if (targetTab === "benchmark" && window.benchmarkHub) {
        window.benchmarkHub.init();
      }
      // Nếu rời tab Webcam, tự động dừng camera để tiết kiệm tài nguyên
      if (targetTab !== "webcam" && window.webcamScanner && window.webcamScanner.isCameraActive) {
        window.webcamScanner.stopCamera();
      }
    });
  });

  // 2. Đồng bộ Model Selector
  const modelSelect = document.getElementById("globalModelSelect");
  if (modelSelect) {
    modelSelect.addEventListener("change", (e) => {
      window.appState.currentModelId = e.target.value;
      sfx.playBeep(700, 0.05);

      // Nếu đang vẽ thì dự đoán lại với mô hình mới
      if (window.drawingStudio && window.drawingStudio.hasDrawing()) {
        window.drawingStudio.predict();
      }
    });
  }

  // 3. Sound Toggle Button
  const btnSound = document.getElementById("btnToggleSound");
  if (btnSound) {
    btnSound.addEventListener("click", () => {
      window.appState.soundEnabled = !window.appState.soundEnabled;
      btnSound.innerHTML = window.appState.soundEnabled
        ? `<i class="fa-solid fa-volume-high"></i>`
        : `<i class="fa-solid fa-volume-xmark"></i>`;
    });
  }

  // 4. Modal Hướng dẫn / Thông tin hệ thống
  const btnInfo = document.getElementById("btnOpenInfoModal");
  const modal = document.getElementById("infoModal");
  const btnCloseModal = document.getElementById("btnCloseModal");

  if (btnInfo && modal) {
    btnInfo.addEventListener("click", () => modal.classList.add("open"));
  }
  if (btnCloseModal && modal) {
    btnCloseModal.addEventListener("click", () => modal.classList.remove("open"));
  }
  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.remove("open");
    });
  }

  // 5. Nút điều khiển Lịch sử
  const btnClearHist = document.getElementById("btnClearHistory");
  const btnExportJSON = document.getElementById("btnExportJSON");
  const btnExportCSV = document.getElementById("btnExportCSV");

  if (btnClearHist) btnClearHist.addEventListener("click", () => HistoryManager.clear());
  if (btnExportJSON) btnExportJSON.addEventListener("click", () => HistoryManager.exportJSON());
  if (btnExportCSV) btnExportCSV.addEventListener("click", () => HistoryManager.exportCSV());

  // Hiển thị lịch sử ban đầu
  HistoryManager.renderHistoryGrid();

  // 6. Kiểm tra trạng thái máy chủ (Polling Server Health)
  async function updateHealth() {
    const health = await ApiService.checkHealth();
    const serverDot = document.getElementById("serverHealthDot");
    const serverTxt = document.getElementById("serverHealthTxt");
    if (health && health.status === "online") {
      if (serverDot) serverDot.style.backgroundColor = "var(--accent-emerald)";
      if (serverTxt) serverTxt.textContent = "Máy chủ AI: Online (Cổng 8000)";
    } else {
      if (serverDot) serverDot.style.backgroundColor = "var(--accent-rose)";
      if (serverTxt) serverTxt.textContent = "Máy chủ: Mất kết nối";
    }
  }
  updateHealth();
  setInterval(updateHealth, 15000);
});
