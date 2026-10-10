"""
Image Preprocessing Pipeline (Phase 3: OCR Optimization)

Applies a sequence of computer-vision techniques to a certificate image
before it is sent to Tesseract, so that OCR accuracy is maximised
regardless of how the original photo/scan was taken:

    1. Grayscale conversion
    2. Contrast enhancement (CLAHE)
    3. Adaptive thresholding / binarization
    4. Noise removal (denoising)
    5. Deskewing (auto-rotate tilted documents)
    6. Resolution scaling (upscale small images for better OCR)
"""

import cv2
import numpy as np


def _to_grayscale(img: np.ndarray) -> np.ndarray:
    if len(img.shape) == 3:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img


def _enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE (Contrast Limited Adaptive Histogram Equalization)."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _denoise(gray: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(gray, h=10)


def _binarize(gray: np.ndarray) -> np.ndarray:
    """Adaptive thresholding handles uneven lighting better than a fixed one."""
    return cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )


def _deskew(img: np.ndarray) -> np.ndarray:
    """Detects and corrects a tilted / rotated document."""
    coords = np.column_stack(np.where(img < 255))
    if coords.shape[0] < 20:
        return img  # not enough foreground pixels to reliably deskew
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    else:
        angle = -angle if angle != 0 else 0
    # Skip deskew if the detected angle is negligible (avoids noise rotation)
    if abs(angle) < 0.3:
        return img
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        img, matrix, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def _upscale_if_small(img: np.ndarray, min_width: int = 1500) -> np.ndarray:
    """Tesseract performs best around 300 DPI; upscale small images."""
    h, w = img.shape[:2]
    if w < min_width:
        scale = min_width / w
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return img


def preprocess_image(image_path: str, for_ocr: bool = True) -> np.ndarray:
    """
    Runs the full preprocessing pipeline on an image file and returns
    the processed image (as a numpy array) ready for Tesseract.

    Args:
        image_path: path to the source image on disk.
        for_ocr: if True, returns a binarized black & white image tuned
                 for OCR; if False, returns a lightly cleaned color-safe
                 grayscale image (useful for previews).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at: {image_path}")

    img = _upscale_if_small(img)
    gray = _to_grayscale(img)
    gray = _enhance_contrast(gray)
    gray = _denoise(gray)

    if for_ocr:
        processed = _binarize(gray)
        processed = _deskew(processed)
        return processed

    return gray


def save_preprocessed(image_path: str, output_path: str) -> str:
    """Preprocesses an image and writes the result to disk. Returns the path."""
    processed = preprocess_image(image_path)
    cv2.imwrite(output_path, processed)
    return output_path
