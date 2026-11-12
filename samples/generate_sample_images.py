"""
ImageLab Studio - Sample Test Image Generator
Generates synthetic benchmark images for testing Brightness, Contrast, Gamma, and Sobel edge detection.
"""
import os
import numpy as np
import cv2


def generate_samples(output_dir: str = "samples"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. Test Pattern (600x800) with gradient ramps, step wedges, and geometric edges
    h, w = 600, 800
    pattern = np.full((h, w, 3), 40, dtype=np.uint8)

    # Grayscale step wedge (16 discrete levels from 0 to 255)
    wedge_h = 60
    num_steps = 16
    step_w = w // num_steps
    for i in range(num_steps):
        level = int(i * (255 / (num_steps - 1)))
        pattern[30:30+wedge_h, i*step_w:(i+1)*step_w] = (level, level, level)

    # Smooth continuous gradient ramp (0 to 255)
    grad_ramp = np.linspace(0, 255, w, dtype=np.uint8)
    pattern[110:110+wedge_h, :] = np.tile(grad_ramp, (wedge_h, 1))[:, :, None]

    # Geometric test shapes (circles, rectangles with distinct edges)
    cv2.circle(pattern, (200, 280), 70, (220, 200, 100), -1)
    cv2.circle(pattern, (200, 280), 72, (255, 255, 255), 2)

    cv2.rectangle(pattern, (350, 210), (500, 350), (70, 180, 240), -1)
    cv2.rectangle(pattern, (348, 208), (502, 352), (255, 255, 255), 2)

    # High frequency edge bars (for Sobel edge detection)
    bar_y = 400
    for i in range(0, 700, 20):
        cv2.line(pattern, (50 + i, bar_y), (50 + i, bar_y + 80), (240, 240, 240), 2)
        cv2.line(pattern, (60 + i, bar_y), (60 + i, bar_y + 80), (30, 30, 30), 2)

    # Text label
    cv2.putText(pattern, "ImageLab Studio Test Pattern (600x800)", (50, 550), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (240, 240, 240), 2)

    cv2.imwrite(os.path.join(output_dir, "test_pattern.png"), pattern)

    # 2. Low Light Scene (Simulated night / shadow image)
    low_light = pattern.astype(np.float32) * 0.25 + 5.0
    low_light = np.clip(low_light, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "low_light_sample.jpg"), low_light, [cv2.IMWRITE_JPEG_QUALITY, 95])

    # 3. Low Contrast / Hazy Scene (Pushed into narrow midtone range [90, 160])
    hazy = pattern.astype(np.float32) * 0.28 + 90.0
    hazy = np.clip(hazy, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(output_dir, "low_contrast_hazy.jpg"), hazy, [cv2.IMWRITE_JPEG_QUALITY, 95])

    print(f"Sample images successfully generated in '{output_dir}/'")


if __name__ == "__main__":
    generate_samples()
