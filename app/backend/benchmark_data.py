"""
Dữ liệu đối chuẩn (Benchmark Metrics) cho 5 họ kiến trúc nhận diện chữ số viết tay.
Trích xuất từ quá trình huấn luyện và đánh giá trên tập dữ liệu chuẩn MNIST (60.000 train / 10.000 test).
"""

BENCHMARK_MODELS = {
    "standard_cnn": {
        "id": "standard_cnn",
        "name": "Standard CNN (Classic Deep CNN)",
        "short_name": "Standard CNN",
        "filename": "2_Standard_CNN.keras",
        "badge": "🥇 Best Accuracy",
        "accuracy": 99.01,
        "loss": 0.0312,
        "parameters": 431914,
        "model_size_mb": 5.01,
        "latency_ms": 0.180,
        "training_time_s": 99.9,
        "error_count_10k": 99,
        "f1_score": 0.9901,
        "architecture_type": "Convolutional Neural Network",
        "summary": "Kiến trúc CNN chuẩn mực với 2 khối Conv2D + BatchNorm + MaxPooling2D + Dropout. Đạt độ chính xác cao nhất (99.01%) nhờ khả năng nắm bắt đặc trưng cục bộ (edges, loops) xuất sắc.",
        "pros": ["Độ chính xác cao nhất (99.01%)", "Độ ổn định vượt trội trên dữ liệu nét vẽ méo", "Chuẩn mực công nghiệp"],
        "cons": ["Kích thước lớn nhất (5.01 MB)", "Số tham số cao hơn đáng kể (431K params)"],
        "recommended_for": "Ứng dụng máy chủ xử lý tài liệu, OCR ngân hàng, hệ thống yêu cầu độ tin cậy tuyệt đối."
    },
    "mini_resnet": {
        "id": "mini_resnet",
        "name": "Mini-ResNet (Residual CNN)",
        "short_name": "Mini-ResNet",
        "filename": "3_Mini_ResNet.keras",
        "badge": "🚀 Skip Connections",
        "accuracy": 98.11,
        "loss": 0.0587,
        "parameters": 82058,
        "model_size_mb": 1.04,
        "latency_ms": 0.240,
        "training_time_s": 161.6,
        "error_count_10k": 189,
        "f1_score": 0.9811,
        "architecture_type": "Residual Neural Network",
        "summary": "Tích hợp cơ chế đường tắt (Skip / Shortcut Connection) theo phong cách ResNet kinh điển. Giúp luồng gradient truyền mượt mà, chỉ cần 82K tham số (bằng 1/5 Standard CNN) mà vẫn đạt 98.11% accuracy.",
        "pros": ["Không bị triệt tiêu gradient (vanishing gradient)", "Số tham số chỉ bằng 1/5 Standard CNN", "Dung lượng nhỏ (1.04 MB)"],
        "cons": ["Độ trễ suy luận nhỉnh hơn do phân nhánh đường tắt"],
        "recommended_for": "Ứng dụng cần mô hình sâu, khả năng mở rộng sang tập dữ liệu lớn phức tạp."
    },
    "mobile_cnn": {
        "id": "mobile_cnn",
        "name": "Mobile-Separable CNN (MobileNet Style)",
        "short_name": "Mobile-Separable CNN",
        "filename": "4_Mobile_Separable_CNN.keras",
        "badge": "⚡ Ultra Lightweight",
        "accuracy": 95.94,
        "loss": 0.1206,
        "parameters": 21418,
        "model_size_mb": 0.31,
        "latency_ms": 0.175,
        "training_time_s": 169.7,
        "error_count_10k": 406,
        "f1_score": 0.9594,
        "architecture_type": "Depthwise Separable CNN",
        "summary": "Sử dụng Depthwise Separable Convolution kết hợp GlobalAveragePooling2D. Cực kỳ tối ưu với dung lượng vỏn vẹn 0.31 MB và 21K tham số (nhẹ hơn 16 lần so với Standard CNN).",
        "pros": ["Siêu nhẹ: chỉ 0.31 MB và 21.418 tham số", "Tốc độ nhanh, tiêu tốn ít RAM/bộ nhớ", "Lý tưởng cho thiết bị biên"],
        "cons": ["Độ chính xác thấp hơn một chút (95.94%) do giảm mạnh sức chứa mạng"],
        "recommended_for": "Ứng dụng Web chạy trực tiếp trên Client (TensorFlow.js), Mobile App, vi điều khiển IoT (ESP32, Raspberry Pi)."
    },
    "mlp": {
        "id": "mlp",
        "name": "MLP Baseline (Multilayer Perceptron)",
        "short_name": "MLP Baseline",
        "filename": "1_MLP_Baseline.keras",
        "badge": "⏱️ Fast Training",
        "accuracy": 97.78,
        "loss": 0.0702,
        "parameters": 236682,
        "model_size_mb": 2.75,
        "latency_ms": 0.099,
        "training_time_s": 7.2,
        "error_count_10k": 222,
        "f1_score": 0.9778,
        "architecture_type": "Fully Connected Network",
        "summary": "Mạng nơ-ron truyền thẳng (Fully Connected) truyền thống với 2 tầng ẩn (256, 128) + BatchNorm + Dropout. Huấn luyện siêu tốc (7.2 giây) nhưng mất thông tin không gian 2D.",
        "pros": ["Huấn luyện cực nhanh (7.2s)", "Thời gian suy luận nhanh (0.099 ms)", "Dễ cài đặt"],
        "cons": ["Mất tương quan không gian 2D do Flatten", "Nhạy cảm khi nét vẽ bị lệch tâm hoặc đổi tỉ lệ", "Tốn nhiều tham số ở lớp đầu"],
        "recommended_for": "Baseline chuẩn để đối chiếu hiệu quả của các kiến trúc tích chập nâng cao."
    },
    "vit": {
        "id": "vit",
        "name": "Mini Vision Transformer (ViT)",
        "short_name": "Mini ViT",
        "filename": "5_Mini_ViT.keras",
        "badge": "🤖 Transformer Attention",
        "accuracy": 96.52,
        "loss": 0.1052,
        "parameters": 71818,
        "model_size_mb": 0.95,
        "latency_ms": 0.304,
        "training_time_s": 81.4,
        "error_count_10k": 348,
        "f1_score": 0.9652,
        "architecture_type": "Vision Transformer (Self-Attention)",
        "summary": "Chia ảnh thành 49 patches (4x4) và áp dụng 2 tầng Transformer Encoder với cơ chế Multi-Head Self-Attention. Cho thấy khả năng nắm bắt quan hệ toàn cục hiện đại.",
        "pros": ["Cơ chế Self-Attention nắm bắt quan hệ toàn cục", "Kiến trúc tiên tiến của thị giác máy tính hiện đại", "Không phụ thuộc vào kích thước Receptive Field"],
        "cons": ["Thiếu inductive bias cục bộ nên cần nhiều dữ liệu pretrain hơn CNN", "Độ trễ cao hơn do tính toán ma trận Attention"],
        "recommended_for": "Nghiên cứu học thuật, trình diễn khả năng ứng dụng Transformer vào bài toán thị giác máy tính."
    }
}

# Bảng xếp hạng sắp xếp theo Accuracy
BENCHMARK_LEADERBOARD = sorted(
    BENCHMARK_MODELS.values(),
    key=lambda x: x["accuracy"],
    reverse=True
)
