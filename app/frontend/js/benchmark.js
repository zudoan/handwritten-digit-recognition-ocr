/**
 * Benchmark Dashboard - Trực quan hóa & So sánh Chuyên sâu 5 Họ Kiến trúc Deep Learning
 */

class BenchmarkHub {
  constructor() {
    this.charts = {};
    this.data = null;
  }

  async init() {
    try {
      this.data = await ApiService.getBenchmark();
      if (this.data) {
        this.renderKPIs();
        this.renderCharts();
        this.renderArchitectureCards();
      }
    } catch (e) {
      console.error("Lỗi khởi tạo Benchmark Hub:", e);
    }
  }

  renderKPIs() {
    if (!this.data || !this.data.leaderboard) return;
    const leaderboard = this.data.leaderboard;

    const bestAccModel = leaderboard[0];
    const lightestModel = [...leaderboard].sort((a, b) => a.model_size_mb - b.model_size_mb)[0];
    const fastestModel = [...leaderboard].sort((a, b) => a.latency_ms - b.latency_ms)[0];

    const kpiAccEl = document.getElementById("kpiBestAccuracy");
    if (kpiAccEl) kpiAccEl.textContent = `${bestAccModel.accuracy}%`;

    const kpiSizeEl = document.getElementById("kpiLightestSize");
    if (kpiSizeEl) kpiSizeEl.textContent = `${lightestModel.model_size_mb} MB`;

    const kpiLatEl = document.getElementById("kpiFastestLatency");
    if (kpiLatEl) kpiLatEl.textContent = `${fastestModel.latency_ms} ms`;
  }

  renderCharts() {
    if (!window.Chart || !this.data || !this.data.chart_data) return;
    const cData = this.data.chart_data;

    // 1. Biểu đồ Độ chính xác (Accuracy Bar Chart)
    const accCanvas = document.getElementById("benchmarkAccuracyChart");
    if (accCanvas) {
      if (this.charts.acc) this.charts.acc.destroy();
      this.charts.acc = new Chart(accCanvas, {
        type: "bar",
        data: {
          labels: cData.labels,
          datasets: [{
            label: "Test Accuracy (%)",
            data: cData.accuracies,
            backgroundColor: [
              "rgba(56, 189, 248, 0.8)",
              "rgba(99, 102, 241, 0.8)",
              "rgba(16, 185, 129, 0.8)",
              "rgba(168, 85, 247, 0.8)",
              "rgba(245, 158, 11, 0.8)"
            ],
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => `Độ chính xác: ${ctx.raw}%`
              }
            }
          },
          scales: {
            y: {
              min: 94,
              max: 100,
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#94a3b8" }
            },
            x: {
              grid: { display: false },
              ticks: { color: "#94a3b8" }
            }
          }
        }
      });
    }

    // 2. Biểu đồ Trade-off: Tốc độ suy luận (ms) vs Độ chính xác (%)
    const tradeoffCanvas = document.getElementById("benchmarkTradeoffChart");
    if (tradeoffCanvas) {
      if (this.charts.tradeoff) this.charts.tradeoff.destroy();
      
      const scatterPoints = this.data.leaderboard.map((m) => ({
        x: m.latency_ms,
        y: m.accuracy,
        r: Math.max(6, Math.min(22, Math.sqrt(m.parameters / 800))),
        modelName: m.short_name,
        params: m.parameters,
        size: m.model_size_mb
      }));

      this.charts.tradeoff = new Chart(tradeoffCanvas, {
        type: "bubble",
        data: {
          datasets: [{
            label: "Mô hình",
            data: scatterPoints,
            backgroundColor: "rgba(56, 189, 248, 0.6)",
            borderColor: "#38bdf8",
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => {
                  const p = ctx.raw;
                  return `${p.modelName}: Acc=${p.y}%, Trễ=${p.x}ms, Size=${p.size}MB`;
                }
              }
            }
          },
          scales: {
            x: {
              title: { display: true, text: "Độ trễ suy luận (ms / mẫu)", color: "#94a3b8" },
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#94a3b8" }
            },
            y: {
              title: { display: true, text: "Độ chính xác Test Accuracy (%)", color: "#94a3b8" },
              min: 95,
              max: 100,
              grid: { color: "rgba(255, 255, 255, 0.05)" },
              ticks: { color: "#94a3b8" }
            }
          }
        }
      });
    }
  }

  renderArchitectureCards() {
    const container = document.getElementById("architectureCardsContainer");
    if (!container || !this.data || !this.data.leaderboard) return;

    let html = "";
    this.data.leaderboard.forEach((m, idx) => {
      html += `
        <div class="arch-card">
          <div class="arch-card-header">
            <div>
              <span class="model-badge">${m.badge}</span>
              <h4 class="arch-title" style="margin-top: 6px;">${idx + 1}. ${m.name}</h4>
            </div>
            <div style="text-align: right;">
              <span style="font-size: 1.3rem; font-weight: 800; color: var(--accent-cyan); font-family: var(--font-mono);">${m.accuracy}%</span>
              <div style="font-size: 0.7rem; color: var(--text-dim);">Test Accuracy</div>
            </div>
          </div>
          
          <div class="arch-metrics-pills">
            <span class="mini-pill"><i class="fa-solid fa-microchip"></i> ${m.parameters.toLocaleString()} params</span>
            <span class="mini-pill"><i class="fa-solid fa-hard-drive"></i> ${m.model_size_mb} MB</span>
            <span class="mini-pill"><i class="fa-solid fa-stopwatch"></i> ${m.latency_ms} ms</span>
            <span class="mini-pill"><i class="fa-solid fa-circle-exclamation"></i> Lỗi: ${m.error_count_10k}/10k</span>
          </div>

          <p class="arch-desc">${m.summary}</p>

          <div style="font-size: 0.75rem; border-top: 1px solid var(--border-subtle); padding-top: 10px; margin-top: auto;">
            <div style="color: #34d399; margin-bottom: 4px;"><strong>✓ Ưu điểm:</strong> ${m.pros.join(", ")}</div>
            <div style="color: #f87171; margin-bottom: 4px;"><strong>✗ Hạn chế:</strong> ${m.cons.join(", ")}</div>
            <div style="color: var(--text-muted);"><strong>🎯 Khuyến nghị:</strong> ${m.recommended_for}</div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.benchmarkHub = new BenchmarkHub();
});
