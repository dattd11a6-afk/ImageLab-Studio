"""
ImageLab Studio - Image Analyzer (Động cơ phân tích định lượng quang học)
Xây dựng theo chuẩn Đề tài 6: Phân tích Histogram 256 mức xám, trích xuất chỉ số thống kê cường độ sáng,
đo lường hiện tượng bão hòa Clipping, định lượng mật độ biên Sobel và chẩn đoán quy luật xử lý ảnh.

Hệ thống cung cấp các đại lượng phân tích học thuật:
1. Histogram 256 bins & Định lý bảo toàn tổng pixel: sum(H) = W x H.
2. Thống kê mức xám: Mean (mu), Standard Deviation (sigma), Median, Dynamic Range.
3. Đo lường Clipping & Suy hao chi tiết: Black Clipping (I=0), White Clipping (I=255), Shadows (<30), Highlights (>225).
4. Entropy thông tin Shannon: Đo lường mức độ phong phú và độ bất định của phân bố mức xám.
5. Thống kê biên Sobel & Định lý bất biến quang học: grad(I + beta) = grad(I).
"""
from typing import Dict, Any, Tuple, Optional
import numpy as np
import cv2
from app.core.image_processor import ImageProcessor


class ImageAnalyzer:
    """
    Động cơ phân tích định lượng ảnh số (Quantitative Image Analysis Engine):
    - Tính toán biểu đồ tần suất Histogram 256 mức xám trên kênh đơn và từng kênh màu B-G-R
    - Trích xuất hệ thống số liệu thống kê quang học: Mean, Median, Std Dev, Min, Max, Dynamic Range, Shannon Entropy
    - Phân tích hiện tượng bão hòa phơi sáng: Tỷ lệ bết tối (0), Cháy sáng (255), Vùng tối (<30), Vùng sáng (>225)
    - Định lượng vi phân biên Sobel: Gradient trung bình, Gradient cực đại, Mật độ biên (Edge Density)
    - Tự động sinh nhận định khoa học và chẩn đoán bản chất biến đổi quang học của ảnh
    """

    @classmethod
    def compute_histogram_256(cls, gray_image: np.ndarray) -> np.ndarray:
        """
        Tính toán biểu đồ tần suất Histogram 256 mức xám cho ảnh xám 8-bit.

        Cơ sở lý thuyết toán học:
        - Histogram là hàm phân bố rời rạc H(k) đếm số lượng điểm ảnh có mức xám chính xác bằng k:
              H(k) = count { (x, y) | I(x, y) = k },   k thuộc đoạn [0, 255]
        - ĐỊNH LÝ BẢO TOÀN SỐ ĐIỂM ẢNH:
          Tổng tích lũy của tất cả 256 cột trong Histogram luôn luôn bằng chính xác tổng số điểm ảnh của bức ảnh:
              sum_{k=0}^{255} H(k) = W * H (Width x Height)
          Nếu tổng này sai lệch dù chỉ 1 đơn vị, thuật toán phân tích đã bị lỗi bộ nhớ hoặc tính toán sai.

        Args:
            gray_image (np.ndarray): Mảng ma trận điểm ảnh kênh đơn 2 chiều (uint8).

        Returns:
            np.ndarray: Mảng 1 chiều chứa đúng 256 số nguyên (int64) đại diện cho số lượng pixel tại mỗi mức xám [0..255].
        """
        if len(gray_image.shape) != 2:
            gray_image = ImageProcessor.to_grayscale(gray_image)

        # Sử dụng hàm cv2.calcHist tối ưu hóa bằng C++ để đếm tần suất 256 bin từ mức 0 đến 256
        hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
        return hist.ravel().astype(np.int64)

    @classmethod
    def compute_color_histograms(cls, bgr_image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Tính toán biểu đồ tần suất Histogram cho từng kênh màu riêng biệt (Blue, Green, Red)
        và kênh độ chói tổng hợp (Grayscale Luminance).

        Args:
            bgr_image (np.ndarray): Ma trận ảnh màu 3 kênh BGR hoặc ảnh xám đơn kênh (uint8).

        Returns:
            Dict[str, np.ndarray]: Từ điển chứa 4 mảng Histogram 256 phần tử:
                - "b": Kênh Blue (Xanh dương)
                - "g": Kênh Green (Xanh lá)
                - "r": Kênh Red (Đỏ)
                - "gray": Kênh mức xám tổng hợp (Luminance Y)
        """
        if len(bgr_image.shape) == 2 or (len(bgr_image.shape) == 3 and bgr_image.shape[2] == 1):
            gray = ImageProcessor.to_grayscale(bgr_image)
            h = cls.compute_histogram_256(gray)
            return {"gray": h, "b": h, "g": h, "r": h}

        # Tính riêng từng kênh màu trong không gian BGR
        b_hist = cv2.calcHist([bgr_image], [0], None, [256], [0, 256]).ravel().astype(np.int64)
        g_hist = cv2.calcHist([bgr_image], [1], None, [256], [0, 256]).ravel().astype(np.int64)
        r_hist = cv2.calcHist([bgr_image], [2], None, [256], [0, 256]).ravel().astype(np.int64)

        # Tính kênh độ chói Grayscale Luminance theo chuẩn ITU-R BT.601
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        gray_hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel().astype(np.int64)

        return {
            "b": b_hist,
            "g": g_hist,
            "r": r_hist,
            "gray": gray_hist
        }

    @classmethod
    def compute_intensity_stats(cls, gray_image: np.ndarray) -> Dict[str, float]:
        """
        Tính toán hệ thống chỉ số thống kê quang học định lượng trên không gian mức xám của bức ảnh.

        Ý nghĩa vật lý và công thức của các chỉ số:
        1. Mean (Cường độ sáng trung bình mu):
              mu = (1 / N) * sum(I(x, y))
           Đo lường độ sáng tổng thể của ảnh. Khi tăng beta, mu tăng tuyến tính; khi giảm beta, mu giảm.
        2. Standard Deviation (Độ lệch chuẩn sigma):
              sigma = sqrt( (1 / N) * sum((I(x, y) - mu)^2) )
           Đo lường độ phân tán (dispersion) của mức xám quanh giá trị trung bình. Trong xử lý ảnh,
           độ lệch chuẩn sigma chính là thước đo toán học chuẩn mực của ĐỘ TƯƠNG PHẢN (Contrast).
           - Tăng tương phản (alpha > 1.0) -> mức xám giãn ra -> sigma tăng.
           - Giảm tương phản (alpha < 1.0) -> mức xám co cụm về 127.5 -> sigma giảm.
        3. Median (Trung vị mức xám):
           Giá trị mức xám nằm ở vị trí phân vị 50%, chia bức ảnh thành hai nửa có số pixel bằng nhau.
           Khác với Mean, Median không bị ảnh hưởng mạnh bởi một số ít điểm ảnh ngoại lai (outliers/cháy sáng).
        4. Min, Max và Dynamic Range (Dải động quang học):
              Dynamic Range = Max - Min
           Khoảng cách giữa mức xám tối nhất và sáng nhất có mặt trong ảnh.
        5. Hiện tượng Clipping (Bão hòa phơi sáng):
           - Black Clipping (I = 0): Tỷ lệ phần trăm điểm ảnh bị mất chi tiết do quá tối (bết đen/underexposed).
           - White Clipping (I = 255): Tỷ lệ phần trăm điểm ảnh bị bão hòa sáng (cháy trắng/overexposed).
           - Total Clipping = Black Clipping + White Clipping.
        6. Shannon Entropy (Độ hỗn loạn thông tin):
              H = - sum_{k=0}^{255} p(k) * log2(p(k))   với p(k) = H(k) / N
           Đo lường lượng thông tin trung bình chứa trong mỗi pixel (đơn vị: bits/pixel).
           - Ảnh có độ tương phản tốt, phân bố đều các mức xám sẽ có Entropy cao (tối đa 8.0 bits).
           - Ảnh bị suy thoái, bão hòa clipping nặng hoặc bị san phẳng tương phản sẽ có Entropy giảm mạnh.

        Args:
            gray_image (np.ndarray): Ảnh xám 8-bit đầu vào (uint8).

        Returns:
            Dict[str, float]: Từ điển chứa toàn bộ các chỉ số thống kê quang học.
        """
        if len(gray_image.shape) != 2:
            gray_image = ImageProcessor.to_grayscale(gray_image)

        total_pixels = int(gray_image.size)
        if total_pixels == 0:
            raise ValueError("Ma trận điểm ảnh rỗng (tổng số pixel = 0)")

        # Tính toán các chỉ số cơ bản thông qua NumPy vectorization
        mean_val = float(np.mean(gray_image))
        median_val = float(np.median(gray_image))
        std_val = float(np.std(gray_image))
        min_val = int(np.min(gray_image))
        max_val = int(np.max(gray_image))
        dynamic_range = max_val - min_val

        # Sử dụng Histogram 256 bins để tính nhanh các tỷ lệ phân vị và clipping
        hist = cls.compute_histogram_256(gray_image)

        # Điểm ảnh bão hòa ở hai đầu cực trị 0 và 255
        count_black = int(hist[0])
        count_white = int(hist[255])
        clip_black_pct = (count_black / total_pixels) * 100.0
        clip_white_pct = (count_white / total_pixels) * 100.0
        clip_total_pct = ((count_black + count_white) / total_pixels) * 100.0

        # Vùng bóng tối (Shadows: mức xám < 30)
        dark_count = int(np.sum(hist[:30]))
        dark_pct = (dark_count / total_pixels) * 100.0

        # Vùng nổi bật sáng (Highlights: mức xám > 225)
        highlight_count = int(np.sum(hist[226:]))
        highlight_pct = (highlight_count / total_pixels) * 100.0

        # Tính Shannon Entropy: H = - sum(p * log2(p))
        probs = hist.astype(np.float64) / total_pixels
        non_zero = probs[probs > 0]
        entropy = float(-np.sum(non_zero * np.log2(non_zero)))

        return {
            "mean": mean_val,
            "median": median_val,
            "std": std_val,
            "min": float(min_val),
            "max": float(max_val),
            "dynamic_range": float(dynamic_range),
            "dark_pct": dark_pct,
            "highlight_pct": highlight_pct,
            "clip_black_pct": clip_black_pct,
            "clip_white_pct": clip_white_pct,
            "clip_under_pct": clip_black_pct,
            "clip_over_pct": clip_white_pct,
            "clip_total_pct": clip_total_pct,
            "entropy": entropy,
            "total_pixels": total_pixels
        }

    @classmethod
    def compute_sobel_stats(
        cls,
        magnitude_map: np.ndarray,
        threshold: float = 50.0,
        strong_threshold: float = 100.0
    ) -> Dict[str, float]:
        """
        Tính toán các chỉ số thống kê đặc trưng cấu trúc biên từ bản đồ độ lớn Gradient Sobel.

        Cơ sở lý thuyết:
        - Mean Gradient: Cường độ biến thiên mức xám trung bình trên toàn bộ bề mặt ảnh.
          Phản ánh độ "sắc nét" (sharpness) tổng thể.
        - Max Gradient: Độ dốc mức xám lớn nhất đo được tại các cạnh biên sắc nhọn nhất.
        - Edge Density (Mật độ điểm biên %): Tỷ lệ phần trăm các điểm ảnh có |G| >= threshold.
          Đo lường mức độ phong phú chi tiết hình học của vật thể trong ảnh.
        - Strong Edge Density (%): Tỷ lệ phần trăm các điểm biên rõ rệt có |G| >= strong_threshold.

        ĐỊNH LÝ BẤT BIẾN QUANG HỌC KHI ĐIỀU CHỈNH ĐỘ SÁNG (BRIGHTNESS INVARIANCE THEOREM):
        - Xét phép biến đổi độ sáng tuyến tính: I_new(x, y) = I(x, y) + beta.
        - Đạo hàm không gian theo hướng X và Y:
              d(I_new) / dx = d(I + beta) / dx = dI / dx + d(beta) / dx = dI / dx + 0 = Gx
              d(I_new) / dy = d(I + beta) / dy = dI / dy + d(beta) / dy = dI / dy + 0 = Gy
        - Suy ra: Gradient Magnitude |G_new| = sqrt(Gx^2 + Gy^2) = |G_old|.
        - KẾT LUẬN KHOA HỌC: Việc kéo thanh trượt Brightness (Beta) KHÔNG LÀM THAY ĐỔI bản đồ biên Sobel
          (ngoại trừ các điểm ảnh bị bão hòa clipping vào 0 hoặc 255).
          Chỉ có thanh trượt Contrast (Alpha) và Gamma mới làm thay đổi độ lớn Gradient biên.

        Args:
            magnitude_map (np.ndarray): Mảng 2 chiều float32 chứa giá trị độ lớn Gradient.
            threshold (float): Ngưỡng lọc phát hiện biên cạnh tổng quát (mặc định: 50.0).
            strong_threshold (float): Ngưỡng lọc phát hiện biên cạnh mạnh (mặc định: 100.0).

        Returns:
            Dict[str, float]: Từ điển chứa mean_gradient, max_gradient, edge_density, strong_edge_density.
        """
        total_pixels = int(magnitude_map.size)
        if total_pixels == 0:
            raise ValueError("Bản đồ độ lớn Gradient rỗng (total_pixels = 0)")

        mean_grad = float(np.mean(magnitude_map))
        max_grad = float(np.max(magnitude_map))

        # Đếm số lượng điểm ảnh vượt ngưỡng biên
        edge_pixels = int(np.count_nonzero(magnitude_map >= threshold))
        strong_pixels = int(np.count_nonzero(magnitude_map >= strong_threshold))

        # Tính tỷ lệ phần trăm mật độ biên trên tổng số điểm ảnh
        edge_density = (edge_pixels / total_pixels) * 100.0
        strong_edge_density = (strong_pixels / total_pixels) * 100.0

        return {
            "mean_gradient": mean_grad,
            "max_gradient": max_grad,
            "edge_density": edge_density,
            "strong_edge_density": strong_edge_density,
            "threshold": float(threshold),
            "strong_threshold": float(strong_threshold)
        }

    @classmethod
    def compare_images(
        cls,
        orig_image: np.ndarray,
        adj_image: np.ndarray,
        sobel_threshold: float = 50.0
    ) -> Dict[str, Any]:
        """
        Quy trình phân tích so sánh định lượng toàn diện giữa Ảnh gốc và Ảnh đã xử lý.
        Tính toán song song tất cả các chỉ số quang học, thống kê độ lệch Delta (Δ = Adjusted - Original),
        và tự động sinh hệ thống nhận định học thuật hỗ trợ bảo vệ đồ án.

        Args:
            orig_image (np.ndarray): Ma trận ảnh gốc ban đầu.
            adj_image (np.ndarray): Ma trận ảnh sau điều chỉnh tham số.
            sobel_threshold (float): Ngưỡng lọc biên Sobel phục vụ tính Edge Density.

        Returns:
            Dict[str, Any]: Gói dữ liệu so sánh toàn diện bao gồm:
                - "stats_original": Bộ chỉ số quang học ảnh gốc
                - "stats_adjusted": Bộ chỉ số quang học ảnh đã chỉnh
                - "sobel_original": Thống kê biên Sobel ảnh gốc
                - "sobel_adjusted": Thống kê biên Sobel ảnh đã chỉnh
                - "deltas": Độ lệch chênh lệch của tất cả các chỉ số (Δ = Adjusted - Original)
                - "hist_original": Histogram 256 mức xám ảnh gốc
                - "hist_adjusted": Histogram 256 mức xám ảnh đã chỉnh
                - "diagnosis": Nhận định khoa học về quy luật xử lý ảnh
        """
        gray_orig = ImageProcessor.to_grayscale(orig_image)
        gray_adj = ImageProcessor.to_grayscale(adj_image)

        # 1. Tính toán Histogram 256 bins cho hai ảnh độc lập
        hist_orig = cls.compute_histogram_256(gray_orig)
        hist_adj = cls.compute_histogram_256(gray_adj)

        # 2. Tính toán thống kê cường độ sáng cho hai ảnh
        stats_orig = cls.compute_intensity_stats(gray_orig)
        stats_adj = cls.compute_intensity_stats(gray_adj)

        # 3. Tính toán đạo hàm không gian Sobel trên ma trận float32
        _, _, mag_orig = ImageProcessor.compute_sobel_raw(gray_orig)
        _, _, mag_adj = ImageProcessor.compute_sobel_raw(gray_adj)

        sobel_orig = cls.compute_sobel_stats(mag_orig, threshold=sobel_threshold)
        sobel_adj = cls.compute_sobel_stats(mag_adj, threshold=sobel_threshold)

        # 4. Tính toán độ chênh lệch Delta (Δ = Adjusted - Original)
        deltas = {
            "delta_mean": stats_adj["mean"] - stats_orig["mean"],
            "delta_median": stats_adj["median"] - stats_orig["median"],
            "delta_std": stats_adj["std"] - stats_orig["std"],
            "delta_dynamic_range": stats_adj["dynamic_range"] - stats_orig["dynamic_range"],
            "delta_clipping": stats_adj["clip_total_pct"] - stats_orig["clip_total_pct"],
            "delta_clip_black": stats_adj["clip_black_pct"] - stats_orig["clip_black_pct"],
            "delta_clip_white": stats_adj["clip_white_pct"] - stats_orig["clip_white_pct"],
            "delta_entropy": stats_adj["entropy"] - stats_orig["entropy"],
            "delta_mean_gradient": sobel_adj["mean_gradient"] - sobel_orig["mean_gradient"],
            "delta_max_gradient": sobel_adj["max_gradient"] - sobel_orig["max_gradient"],
            "delta_edge_density": sobel_adj["edge_density"] - sobel_orig["edge_density"],
            "delta_strong_edge": sobel_adj["strong_edge_density"] - sobel_orig["strong_edge_density"],
        }

        # 5. Sinh nhận định và chẩn đoán định tính dựa trên các định luật quang học
        diagnosis = cls._generate_diagnostic_insights(stats_orig, stats_adj, deltas, sobel_orig, sobel_adj)

        return {
            "stats_original": stats_orig,
            "stats_adjusted": stats_adj,
            "sobel_original": sobel_orig,
            "sobel_adjusted": sobel_adj,
            "deltas": deltas,
            "hist_original": hist_orig,
            "hist_adjusted": hist_adj,
            "diagnosis": diagnosis
        }

    @staticmethod
    def _generate_diagnostic_insights(
        s_orig: Dict[str, float],
        s_adj: Dict[str, float],
        deltas: Dict[str, float],
        sob_orig: Dict[str, float],
        sob_adj: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Tự động tạo lập các câu nhận định và phân tích sư phạm dựa trên quy luật thị giác và toán học xử lý ảnh.

        Args:
            s_orig (Dict[str, float]): Thống kê ảnh gốc.
            s_adj (Dict[str, float]): Thống kê ảnh đã chỉnh.
            deltas (Dict[str, float]): Độ lệch chênh lệch.
            sob_orig (Dict[str, float]): Thống kê Sobel ảnh gốc.
            sob_adj (Dict[str, float]): Thống kê Sobel ảnh đã chỉnh.

        Returns:
            Dict[str, str]: Từ điển chứa các đoạn nhận định chẩn đoán bằng tiếng Việt có dấu.
        """
        # 1. Nhận định về Độ sáng và Dịch chuyển Histogram (Histogram Shift)
        d_mean = deltas["delta_mean"]
        if abs(d_mean) < 0.5:
            brightness_note = "Độ sáng trung bình giữ nguyên (Histogram không dịch chuyển đáng kể)."
        elif d_mean > 0:
            brightness_note = f"Histogram dịch PHẢI (+{d_mean:.1f} mức xám): Ảnh có xu hướng TĂNG SÁNG tổng thể."
        else:
            brightness_note = f"Histogram dịch TRÁI ({d_mean:.1f} mức xám): Ảnh có xu hướng GIẢM SÁNG (tối hơn)."

        # 2. Nhận định về Độ tương phản và Độ phân tán quanh tâm 127.5 (Contrast Dispersion)
        d_std = deltas["delta_std"]
        if abs(d_std) < 0.5:
            contrast_note = "Độ tương phản (độ lệch chuẩn σ) gần như không đổi."
        elif d_std > 0:
            contrast_note = (
                f"Độ rộng phân bố MỞ RỘNG (+{d_std:.1f}): Độ tương phản tăng, mức xám giãn ra xa tâm 127.5. "
                "Vùng sáng sáng hơn, vùng tối tối hơn."
            )
        else:
            contrast_note = (
                f"Độ rộng phân bố THU HẸP ({d_std:.1f}): Độ tương phản giảm, các mức xám co cụm về mức trung bình 127.5."
            )

        # 3. Nhận định về Hiện tượng Clipping & Bảo toàn chi tiết
        black_clip = s_adj["clip_black_pct"]
        white_clip = s_adj["clip_white_pct"]
        total_clip = s_adj["clip_total_pct"]

        if total_clip < 0.05:
            clipping_note = "Bảo toàn chi tiết xuất sắc: Không có hiện tượng clipping (cháy sáng hay bết tối)."
            clipping_status = "Optimal"
        elif total_clip < 2.0:
            clipping_note = f"Mức clipping nhẹ ({total_clip:.1f}%): Chi tiết được bảo toàn tốt ở hầu hết dải động."
            clipping_status = "Good"
        elif total_clip < 8.0:
            clipping_note = (
                f"Cảnh báo clipping ({total_clip:.1f}% tổng: Bết tối={black_clip:.1f}%, Cháy sáng={white_clip:.1f}%): "
                "Xuất hiện hiện tượng mất thông tin ở biên dải động [0, 255]."
            )
            clipping_status = "Warning"
        else:
            clipping_note = (
                f"Cảnh báo bão hòa nghiêm trọng ({total_clip:.1f}% pixel): Bết tối (0)={black_clip:.1f}%, "
                f"Cháy sáng (255)={white_clip:.1f}%. Mất hoàn toàn chi tiết vân bề mặt."
            )
            clipping_status = "Danger"

        # 4. Nhận định về Bản chất toán học Gradient Sobel & Bất biến quang học
        d_grad = deltas["delta_mean_gradient"]
        d_edge_dens = deltas["delta_edge_density"]
        if abs(d_grad) < 0.2 and abs(d_edge_dens) < 0.2:
            sobel_note = (
                "Cường độ biên không đổi. Chú ý lý thuyết: Dịch chuyển độ sáng tuyến tính (Beta) không làm thay đổi đạo hàm "
                "(∇(I + β) = ∇I). Chỉ có Contrast (Alpha) và Gamma mới làm thay đổi gradient biên."
            )
        elif d_grad > 0:
            sobel_note = (
                f"Gradient biên TĂNG (+{d_grad:.1f}, mật độ biên +{d_edge_dens:.1f}%): Cạnh sắc nét hơn, "
                "độ tương phản vi mô được nâng cao do hệ số Contrast α hoặc Gamma làm dốc biên."
            )
        else:
            sobel_note = (
                f"Gradient biên GIẢM ({d_grad:.1f}, mật độ biên {d_edge_dens:.1f}%): Cạnh bị mờ hóa hoặc dải tương phản vi mô bị co lại."
            )

        return {
            "brightness_note": brightness_note,
            "contrast_note": contrast_note,
            "clipping_note": clipping_note,
            "clipping_status": clipping_status,
            "sobel_note": sobel_note
        }
