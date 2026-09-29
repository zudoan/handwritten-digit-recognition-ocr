"""
====================================================================
NEURALVISION STUDIO - AI VISION & OCR SERVER RUNNER
====================================================================
CLI launcher with arguments parsing, automatic LAN IP resolution,
and optional browser startup.
"""

import os
import sys
import socket
import argparse
import webbrowser
import threading
import time

# Đảm bảo mã hóa UTF-8 cho console đầu ra
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def get_local_ip() -> str:
    """Lấy địa chỉ IP nội bộ trong mạng LAN / Wi-Fi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Kiểm tra cổng mạng có đang bị chiếm dụng không"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def open_browser(url: str, delay: float = 1.5):
    """Mở trình duyệt sau khi máy chủ đã sẵn sàng"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass

def parse_args():
    parser = argparse.ArgumentParser(
        description="NeuralVision Studio - High-Performance AI Vision & OCR Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Địa chỉ host ràng buộc (0.0.0.0 cho tất cả card mạng)")
    parser.add_argument("--port", type=int, default=8080, help="Cổng dịch vụ HTTP")
    parser.add_argument("--reload", action="store_true", help="Bật chế độ tự động reload khi phát triển (development)")
    parser.add_argument("--no-browser", action="store_true", help="Không tự động mở trình duyệt web khi khởi động")
    return parser.parse_args()

def main():
    args = parse_args()
    port = args.port

    # Kiểm tra cổng và tự động gợi ý cổng kế tiếp nếu bị bận
    if is_port_in_use(port):
        alt_port = port + 1
        while is_port_in_use(alt_port):
            alt_port += 1
        print(f"[CANH BAO] Cong {port} dang duoc su dung boi ung dung khac.")
        print(f"[THAY DOI] Tu dong chuyen sang cong trong: {alt_port}")
        port = alt_port

    local_ip = get_local_ip()
    local_url = f"http://localhost:{port}"
    lan_url = f"http://{local_ip}:{port}"

    print("=" * 80)
    print("   NEURALVISION STUDIO - DEEP LEARNING BENCHMARK & OCR PLATFORM")
    print("=" * 80)
    print(f"  [>] Local Access:       {local_url}")
    print(f"  [>] Network (LAN/Wi-Fi): {lan_url}")
    print(f"  [>] API Documentation:  {local_url}/docs")
    print(f"  [>] Health Status:      {local_url}/api/health")
    print("=" * 80)
    print("  [*] Model san sang: Standard CNN (99.01%), ResNet, MobileNet, MLP, ViT")
    print("  [*] Nhan Ctrl + C de dung may chu bat cu luc nao.")
    print("=" * 80)

    if not args.no_browser:
        threading.Thread(target=open_browser, args=(local_url,), daemon=True).start()

    import uvicorn
    uvicorn.run(
        "app.backend.main:app",
        host=args.host,
        port=port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
