"""
ImageLab Studio - Image Processor (Động cơ xử lý ảnh cốt lõi)
Xây dựng theo chuẩn Đề tài 6: Điều chỉnh độ sáng, độ tương phản và hiệu chỉnh Gamma;
kết hợp phân tích Histogram và phát hiện biên bằng toán tử vi phân Sobel.

Hệ thống xử lý tuân thủ các nguyên lý khoa học thị giác máy tính:
1. Độ sáng (Brightness): Dịch chuyển tịnh tiến mức xám theo hằng số Beta.
2. Độ tương phản (Contrast): Co giãn phân bố mức xám quanh tâm đối xứng 127.5 theo hệ số Alpha.
3. Hiệu chỉnh Gamma (Gamma Correction): Biến đổi phi tuyến phi tập trung qua bảng tra cứu Look-Up Table (LUT) 256 phần tử.
4. Phát hiện biên Sobel: Đạo hàm không gian bậc nhất theo hướng X và Y, tính độ lớn Gradient Magnitude
   với thang đo chuẩn hóa thống nhất (Unified Shared Scale) phục vụ so sánh công bằng trước và sau xử lý.
"""
from typing import Tuple, Optional, Dict, Any
import numpy as np
import cv2


class ImageProcessor:
    """
    Động cơ xử lý ảnh số chuyên sâu, thực thi các thuật toán biến đổi không gian điểm ảnh:
    - Công thức điều chỉnh Độ sáng & Tương phản bảo toàn trung vị:
      I_out = clip(alpha * (I_in - 127.5) + 127.5 + beta, 0, 255)
    - Hiệu chỉnh Gamma phi tuyến bằng bảng tra cứu LUT (Look-Up Table) O(1)
    - Phát hiện biên vi phân đa thành phần Sobel (Gx, Gy, Gradient Magnitude, Bản đồ nhị phân)
      sử dụng tỷ lệ chuẩn hóa chung (Unified Shared Scale) chống sai lệch quang học.
    """

    @staticmethod
    def apply_brightness_contrast(
        image: np.ndarray,
        brightness: float = 0.0,
        contrast: float = 1.0
    ) -> np.ndarray:
        """
        Điều chỉnh độ sáng và độ tương phản của ảnh số với tâm tương phản đặt tại mức xám trung bình 127.5.

        Cơ sở lý thuyết toán học:
        - Phép biến đổi tương phản cổ điển I_out = alpha * I_in + beta thường làm toàn bộ ảnh bị dịch sáng
          hoặc tối cục bộ khi tăng tương phản vì gốc co giãn đặt tại 0.
        - Công thức chuẩn hóa lấy tâm mức xám trung vị 127.5:
              I_out = clip(alpha * (I_in - 127.5) + 127.5 + beta, 0, 255)
          Trong đó:
            * alpha (Contrast): Hệ số co giãn độ dốc tương phản quanh 127.5.
              - alpha > 1.0: Kéo giãn khoảng cách giữa vùng tối và vùng sáng (tăng tương phản).
              - alpha < 1.0: Nén khoảng cách về gần 127.5 (giảm tương phản, ảnh trở nên phẳng/xám).
              - alpha = 1.0: Giữ nguyên độ tương phản gốc.
            * beta (Brightness): Lượng dịch chuyển tịnh tiến đều trên toàn bộ không gian mức xám.
              - beta > 0: Toàn bộ phổ Histogram dịch sang phải (ảnh sáng hơn).
              - beta < 0: Toàn bộ phổ Histogram dịch sang trái (ảnh tối hơn).
            * clip(..., 0, 255): Ràng buộc giá trị điểm ảnh trong miền [0, 255] của kiểu dữ liệu uint8,
              ngăn ngừa hiện tượng tràn số (integer wrap-around) nguy hiểm trong máy tính (ví dụ: 256 biến thành 0).

        Args:
            image (np.ndarray): Mảng ma trận điểm ảnh đầu vào (BGR hoặc Grayscale kiểu uint8).
            brightness (float): Độ dời mức sáng beta trong khoảng [-100.0, 100.0] (mặc định: 0.0).
            contrast (float): Hệ số khuếch đại tương phản alpha trong khoảng [0.0, 3.0] (mặc định: 1.0).

        Returns:
            np.ndarray: Ma trận ảnh sau điều chỉnh kiểu uint8 cùng kích thước với ảnh gốc.

        Raises:
            ValueError: Khi ảnh đầu vào là None hoặc rỗng (kích thước = 0).
        """
        if image is None or image.size == 0:
            raise ValueError("Ảnh đầu vào không hợp lệ hoặc ma trận rỗng (None/Empty)")

        alpha = float(contrast)
        beta = float(brightness)

        # Tối ưu hóa: Nếu tham số giữ nguyên giá trị mặc định (alpha=1.0, beta=0.0), trả về bản sao ngay lập tức
        if np.isclose(alpha, 1.0, atol=1e-5) and np.isclose(beta, 0.0, atol=1e-5):
            return image.copy()

        # Ép kiểu sang float32 để tính toán dấu phẩy động chính xác cao, tránh tràn số tức thời
        img_float = image.astype(np.float32)

        # Thực thi phép biến đổi ma trận vector hóa (Vectorized NumPy Computation):
        # 1. Trừ 127.5 để dịch tâm mức xám về gốc tọa độ 0
        # 2. Nhân với alpha để co giãn khoảng cách tương phản
        # 3. Cộng lại 127.5 để hoàn trả về không gian mức xám chuẩn
        # 4. Cộng beta để tịnh tiến độ sáng
        adjusted = alpha * (img_float - 127.5) + 127.5 + beta

        # Cắt gọt giá trị (Clipping) về đoạn đóng [0.0, 255.0] để bảo toàn tính toàn vẹn quang học
        clipped = np.clip(adjusted, 0.0, 255.0)

        # Chuyển đổi định dạng số nguyên không dấu 8-bit chuẩn hiển thị hình ảnh
        return clipped.astype(np.uint8)

    @staticmethod
    def get_gamma_lut(gamma: float) -> np.ndarray:
        """
        Khởi tạo bảng tra cứu Look-Up Table (LUT) 256 phần tử cho thuật toán hiệu chỉnh Gamma phi tuyến.

        Cơ sở lý thuyết toán học:
        - Hiệu chỉnh Gamma tuân theo quy luật hàm lũy thừa phi tuyến (Power Law Transform):
              I_gamma = 255 * (I_in / 255) ^ (1 / gamma)
        - Tại sao phải sử dụng bảng tra cứu LUT thay vì tính trực tiếp trên từng pixel ảnh?
          * Một bức ảnh Full HD (1920x1080) có ~2,073,600 pixel (hoặc ~6.2 triệu giá trị trên 3 kênh màu).
          * Phép tính lũy thừa float pow() cực kỳ tốn chi phí chu kỳ xung nhịp CPU.
          * Tuy nhiên, không gian mức xám 8-bit chỉ có đúng 256 giá trị rời rạc khả dĩ từ 0 đến 255.
          * Do đó, ta tính trước kết quả cho 256 giá trị này vào một mảng LUT 1D kích thước 256 bytes (O(1)).
          * Khi áp dụng vào ảnh, hàm cv2.LUT chỉ thực hiện tra cứu bộ nhớ theo chỉ số (Direct Memory Addressing),
            giảm thời gian tính toán từ hàng chục mili-giây xuống dưới 1 mili-giây, đạt tốc độ thời gian thực 60fps+.

        Ý nghĩa vật lý của tham số Gamma:
        - gamma > 1.0 (ví dụ 1.5, 2.0): Nâng sáng vùng tối (Shadows) và vùng trung tính (Midtones)
          mà KHÔNG làm cháy sáng vùng cực sáng (Highlights). Điểm 0 và 255 luôn được bảo toàn: 0^k = 0, 1^k = 1.
        - gamma < 1.0 (ví dụ 0.5, 0.7): Nén sáng vùng tối, làm ảnh sâu hơn, tăng độ bão hòa vùng tối.
        - gamma = 1.0: Phép biến đổi đồng nhất (Identity transform: I_out = I_in).

        Args:
            gamma (float): Hệ số mũ Gamma trong khoảng [0.10, 3.00] (yêu cầu nghiêm ngặt gamma > 0).

        Returns:
            np.ndarray: Mảng 1 chiều 256 phần tử kiểu uint8 chứa các giá trị tra cứu ánh xạ [0..255].

        Raises:
            ValueError: Khi gamma <= 0 (không xác định trong phép chia 1/gamma).
        """
        if gamma <= 0:
            raise ValueError("Hệ số Gamma phải là một số thực dương nghiêm ngặt (gamma > 0)")

        # Nếu gamma xấp xỉ 1.0, trả về bảng đồng nhất [0, 1, 2, ..., 255]
        if np.isclose(gamma, 1.0, atol=1e-4):
            return np.arange(256, dtype=np.uint8)

        inv_gamma = 1.0 / float(gamma)
        # Chuẩn hóa 256 mức xám về miền thực [0.0, 1.0]
        indices = np.arange(256, dtype=np.float32) / 255.0
        # Áp dụng hàm lũy thừa và co giãn lại về biên độ [0.0, 255.0]
        lut_values = np.power(indices, inv_gamma) * 255.0
        # Cắt gọt và ép kiểu về uint8
        lut = np.clip(lut_values, 0.0, 255.0).astype(np.uint8)
        return lut

    @classmethod
    def apply_gamma(cls, image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
        """
        Áp dụng hiệu chỉnh Gamma phi tuyến lên toàn bộ ma trận ảnh thông qua bảng tra cứu LUT.

        Args:
            image (np.ndarray): Ảnh đầu vào (BGR hoặc Grayscale uint8).
            gamma (float): Tham số Gamma trong khoảng [0.10, 3.00] (mặc định: 1.00).

        Returns:
            np.ndarray: Ảnh sau khi hiệu chỉnh Gamma phi tuyến kiểu uint8.
        """
        if image is None or image.size == 0:
            raise ValueError("Ảnh đầu vào không hợp lệ hoặc ma trận rỗng")

        if np.isclose(gamma, 1.0, atol=1e-4):
            return image.copy()

        # Tạo bảng tra cứu LUT 256 phần tử
        lut = cls.get_gamma_lut(gamma)
        # Tra cứu song song tối ưu hóa bằng tập lệnh SIMD/AVX của OpenCV
        return cv2.LUT(image, lut)

    @classmethod
    def process_pipeline(
        cls,
        original_image: np.ndarray,
        brightness: float = 0.0,
        contrast: float = 1.0,
        gamma: float = 1.0
    ) -> np.ndarray:
        """
        Quy trình xử lý ảnh hoàn chỉnh (Enhancement Pipeline):
        Ảnh gốc (Original Image)
        → Bước 1: Điều chỉnh Độ sáng và Độ tương phản có tâm đối xứng
        → Bước 2: Hiệu chỉnh phi tuyến Gamma qua bảng LUT
        → Ảnh hoàn thiện (Adjusted Image).

        NGUYÊN TẮC BẤT BIẾN KHOA HỌC:
        Luôn luôn xử lý từ ma trận ảnh gốc (Original Image) được lưu trữ bất biến trong bộ nhớ.
        Tuyệt đối không áp dụng chồng chéo (compounding) lên ảnh đã qua chỉnh sửa trước đó.
        Lý do: Phép biến đổi rời rạc trên kiểu uint8 bị suy hao thông tin do làm tròn (Quantization Error).
        Nếu áp dụng liên tiếp nhiều lần, sai số tích lũy sẽ phá hủy cấu trúc phổ Histogram của ảnh.

        Args:
            original_image (np.ndarray): Ma trận ảnh gốc bất biến (BGR hoặc Grayscale uint8).
            brightness (float): Tham số độ sáng beta trong khoảng [-100.0, 100.0].
            contrast (float): Tham số độ tương phản alpha trong khoảng [0.00, 3.00].
            gamma (float): Tham số gamma trong khoảng [0.10, 3.00].

        Returns:
            np.ndarray: Ảnh sau khi hoàn tất toàn bộ chuỗi xử lý (uint8).
        """
        if original_image is None or original_image.size == 0:
            raise ValueError("Ảnh gốc đầu vào rỗng hoặc không tồn tại")

        # Bước 1: Tuyến tính hóa độ sáng và tương phản quanh tâm 127.5
        step1 = cls.apply_brightness_contrast(original_image, brightness=brightness, contrast=contrast)

        # Bước 2: Biến đổi phi tuyến Gamma bảo toàn hai đầu dải động
        step2 = cls.apply_gamma(step1, gamma=gamma)

        return step2

    @staticmethod
    def to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Chuyển đổi ma trận ảnh từ định dạng màu BGR hoặc kênh đơn sang ảnh xám 8-bit Grayscale (uint8).

        Cơ sở lý thuyết chuyển đổi màu:
        - Mắt người có độ nhạy không đồng đều với các bước sóng ánh sáng: nhạy nhất với màu xanh lá cây (Green),
          tiếp theo là màu đỏ (Red) và kém nhạy nhất với màu xanh dương (Blue).
        - Công thức chuẩn hóa quốc tế ITU-R BT.601 (được OpenCV triển khai trong cv2.COLOR_BGR2GRAY):
              Y = 0.299 * R + 0.587 * G + 0.114 * B
        - Kết quả tạo ra kênh độ chói quang học (Luminance) phản ánh đúng cảm nhận độ sáng thực tế của thị giác người.

        Args:
            image (np.ndarray): Ảnh nguồn (2 chiều Grayscale, hoặc 3 chiều BGR/BGRA).

        Returns:
            np.ndarray: Ma trận ảnh xám 2 chiều kiểu uint8 (kích thước H x W).

        Raises:
            ValueError: Khi cấu trúc chiều của mảng không được hỗ trợ.
        """
        if image is None or image.size == 0:
            raise ValueError("Ảnh đầu vào không hợp lệ hoặc ma trận rỗng")

        if len(image.shape) == 2:
            return image.copy()
        elif len(image.shape) == 3 and image.shape[2] == 1:
            return image[:, :, 0].copy()
        elif len(image.shape) == 3 and image.shape[2] >= 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError(f"Cấu trúc kích thước ảnh không được hỗ trợ: {image.shape}")

    @classmethod
    def compute_sobel_raw(
        cls,
        gray_image: np.ndarray,
        ksize: int = 3
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Tính toán các thành phần đạo hàm không gian bậc nhất theo toán tử Sobel dưới định dạng dấu phẩy động 32-bit (float32).

        Cơ sở lý thuyết toán học:
        - Toán tử vi phân Sobel tính gần đúng đạo hàm riêng của hàm cường độ ảnh I(x, y):
          * Đạo hàm theo phương ngang X (Sobel X): Gx = I * Kx
            với nhân chập Kx = [[-1, 0, +1],
                                [-2, 0, +2],
                                [-1, 0, +1]]
            Đại diện cho các cạnh biên thẳng đứng (Vertical Edges).
          * Đạo hàm theo phương dọc Y (Sobel Y): Gy = I * Ky
            với nhân chập Ky = [[-1, -2, -1],
                                [ 0,  0,  0],
                                [+1, +2, +1]]
            Đại diện cho các cạnh biên nằm ngang (Horizontal Edges).
        - Độ lớn vectơ Gradient (Gradient Magnitude):
              |G| = sqrt(Gx^2 + Gy^2)
          Đo lường cường độ biến thiên đột ngột của mức xám tại từng điểm ảnh.

        Lưu ý kỹ thuật:
        Bắt buộc tính toán dưới định dạng cv2.CV_32F (float32). Nếu tính trực tiếp trên uint8,
        các đạo hàm âm (ví dụ mức xám chuyển từ sáng sang tối: 50 - 200 = -150) sẽ bị cắt cụt về 0,
        làm mất hoàn toàn 50% thông tin biên cạnh của ảnh.

        Args:
            gray_image (np.ndarray): Ảnh xám 8-bit (uint8).
            ksize (int): Kích thước nhân lọc chập Sobel (mặc định: 3x3).

        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]: Bộ ba ma trận float32 (Gx, Gy, Gradient Magnitude).
        """
        if len(gray_image.shape) != 2:
            gray_image = cls.to_grayscale(gray_image)

        # Tính đạo hàm riêng theo hướng X và Y với độ chính xác float32
        gx = cv2.Sobel(gray_image, cv2.CV_32F, 1, 0, ksize=ksize)
        gy = cv2.Sobel(gray_image, cv2.CV_32F, 0, 1, ksize=ksize)

        # Tính độ lớn Gradient Magnitude: |G| = sqrt(Gx^2 + Gy^2)
        magnitude = cv2.magnitude(gx, gy)

        return gx, gy, magnitude

    @classmethod
    def compute_all_sobel_components(
        cls,
        orig_image: np.ndarray,
        adj_image: np.ndarray,
        threshold: float = 50.0
    ) -> Dict[str, Any]:
        """
        Tính toán toàn bộ bộ 8 thành phần phân tích so sánh biên Sobel giữa Ảnh gốc và Ảnh đã xử lý:
        1. Ảnh xám gốc (Original Grayscale)
        2. Ảnh xám đã chỉnh (Adjusted Grayscale)
        3. Sobel X gốc (chuẩn hóa tỷ lệ chung, tâm mức xám 128)
        4. Sobel X đã chỉnh (chuẩn hóa tỷ lệ chung, tâm mức xám 128)
        5. Sobel Y gốc (chuẩn hóa tỷ lệ chung, tâm mức xám 128)
        6. Sobel Y đã chỉnh (chuẩn hóa tỷ lệ chung, tâm mức xám 128)
        7. Độ lớn Gradient gốc (Gradient Magnitude với thang đo chung)
        8. Độ lớn Gradient đã chỉnh (Gradient Magnitude với thang đo chung)

        NGUYÊN TẮC SO SÁNH CÔNG BẰNG (UNIFIED SHARED SCALE):
        - Nếu chuẩn hóa độc lập từng ảnh (ảnh nào chia cho max của ảnh đó), ảnh có biên yếu sẽ bị
          khuếch đại giả tạo cho sáng bằng ảnh biên mạnh, làm sai lệch nhận định khoa học.
        - Hệ thống áp dụng một hệ số co giãn chung duy nhất:
              shared_scale = 255.0 / max(max_G_original, max_G_adjusted, 1.0) (nếu max_G > 255)
        - Nhờ đó, nếu việc tăng độ tương phản làm tăng độ dốc biên thì ảnh biên sau điều chỉnh
          sẽ sáng rõ hơn một cách trung thực và khách quan.

        Args:
            orig_image (np.ndarray): Ma trận ảnh gốc ban đầu.
            adj_image (np.ndarray): Ma trận ảnh sau khi đã tinh chỉnh thông số.
            threshold (float): Ngưỡng phân tách biên nhị phân (mặc định: 50.0).

        Returns:
            Dict[str, Any]: Từ điển chứa ma trận hình ảnh hiển thị (uint8) và các số liệu thống kê gốc (float32).
        """
        gray_orig = cls.to_grayscale(orig_image)
        gray_adj = cls.to_grayscale(adj_image)

        gx_o, gy_o, mag_o = cls.compute_sobel_raw(gray_orig)
        gx_a, gy_a, mag_a = cls.compute_sobel_raw(gray_adj)

        # Xác định độ lớn cực đại Gradient trên cả hai bức ảnh để xây dựng thang đo chung
        max_mag = max(float(np.max(mag_o)), float(np.max(mag_a)), 1.0)
        shared_scale = 255.0 / max_mag if max_mag > 255.0 else 1.0

        # Chuẩn hóa Sobel X và Y:
        # Với nhân Sobel 3x3, giá trị cực đại lý thuyết là 4 * 255 = 1020.
        # Ta đặt tâm tại 128 (đạo hàm = 0 là màu xám trung tính), đạo hàm dương sáng hơn, đạo hàm âm tối hơn.
        s_xy = 127.0 / 1020.0
        vis_gx_o = np.clip(128.0 + gx_o * s_xy, 0.0, 255.0).astype(np.uint8)
        vis_gx_a = np.clip(128.0 + gx_a * s_xy, 0.0, 255.0).astype(np.uint8)

        vis_gy_o = np.clip(128.0 + gy_o * s_xy, 0.0, 255.0).astype(np.uint8)
        vis_gy_a = np.clip(128.0 + gy_a * s_xy, 0.0, 255.0).astype(np.uint8)

        # Chuẩn hóa bản đồ độ lớn Gradient Magnitude theo thang đo chung thống nhất
        vis_mag_o = np.clip(mag_o * shared_scale, 0.0, 255.0).astype(np.uint8)
        vis_mag_a = np.clip(mag_a * shared_scale, 0.0, 255.0).astype(np.uint8)

        # Phân ngưỡng nhị phân (Binary Edge Mask) cùng một ngưỡng threshold để so sánh mật độ biên
        bin_o = (mag_o >= threshold).astype(np.uint8) * 255
        bin_a = (mag_a >= threshold).astype(np.uint8) * 255

        return {
            "gray_orig": gray_orig,
            "gray_adj": gray_adj,
            "sobel_x_orig": vis_gx_o,
            "sobel_x_adj": vis_gx_a,
            "sobel_y_orig": vis_gy_o,
            "sobel_y_adj": vis_gy_a,
            "mag_orig": vis_mag_o,
            "mag_adj": vis_mag_a,
            "binary_orig": bin_o,
            "binary_adj": bin_a,
            "raw_mag_orig": mag_o,
            "raw_mag_adj": mag_a,
            "raw_gx_orig": gx_o,
            "raw_gx_adj": gx_a,
            "raw_gy_orig": gy_o,
            "raw_gy_adj": gy_a,
            "shared_scale": float(shared_scale),
            "max_gradient_orig": float(np.max(mag_o)),
            "max_gradient_adj": float(np.max(mag_a)),
            "mean_gradient_orig": float(np.mean(mag_o)),
            "mean_gradient_adj": float(np.mean(mag_a)),
            "threshold": float(threshold)
        }

    @classmethod
    def compare_sobel_dual(
        cls,
        orig_image: np.ndarray,
        adj_image: np.ndarray,
        mode: str = "magnitude",
        threshold: float = 50.0
    ) -> Tuple[np.ndarray, np.ndarray, dict]:
        """
        Hàm tiện ích trích xuất cặp ảnh so sánh theo chế độ hiển thị mong muốn kèm theo siêu dữ liệu quang học.

        Args:
            orig_image (np.ndarray): Ảnh gốc.
            adj_image (np.ndarray): Ảnh đã chỉnh sửa.
            mode (str): Chế độ hiển thị ("magnitude", "x", "y", "binary", "gray").
            threshold (float): Ngưỡng lọc biên cho bản đồ nhị phân.

        Returns:
            Tuple[np.ndarray, np.ndarray, dict]: Cặp ảnh trực quan hóa (Ảnh gốc, Ảnh đã chỉnh) và từ điển siêu dữ liệu.
        """
        data = cls.compute_all_sobel_components(orig_image, adj_image, threshold=threshold)

        if mode == "x":
            vis_o = data["sobel_x_orig"]
            vis_a = data["sobel_x_adj"]
        elif mode == "y":
            vis_o = data["sobel_y_orig"]
            vis_a = data["sobel_y_adj"]
        elif mode == "binary":
            vis_o = data["binary_orig"]
            vis_a = data["binary_adj"]
        elif mode == "gray":
            vis_o = data["gray_orig"]
            vis_a = data["gray_adj"]
        else:  # magnitude
            vis_o = data["mag_orig"]
            vis_a = data["mag_adj"]

        metadata = {
            "mode": mode,
            "threshold": threshold,
            "max_gradient_orig": data["max_gradient_orig"],
            "max_gradient_adj": data["max_gradient_adj"],
            "mean_gradient_orig": data["mean_gradient_orig"],
            "mean_gradient_adj": data["mean_gradient_adj"],
            "shared_scale": data["shared_scale"],
            "mag_orig_raw": data["raw_mag_orig"],
            "mag_adj_raw": data["raw_mag_adj"]
        }

        return vis_o, vis_a, metadata
