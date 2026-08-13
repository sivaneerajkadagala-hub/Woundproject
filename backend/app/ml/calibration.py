import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any

class CalibrationEngine:
    """
    Handles pixel-to-millimeter calibration:
    Scale (s) = known_size_mm / marker_size_px
    Area (mm²) = pixel_count * (s ^ 2)
    """

    @staticmethod
    def detect_marker_cv(image_path: str, known_size_mm: float = 10.0) -> Dict[str, Any]:
        """
        Attempts to automatically detect a circular or rectangular calibration marker using OpenCV.
        Returns marker_size_px, scale_mm_per_px, and is_automatic flag.
        """
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        # 1. Try detecting circular marker via Hough Circles
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=100,
            param2=30,
            minRadius=15,
            maxRadius=150
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            best_circle = circles[0][0]
            radius = best_circle[2]
            diameter_px = float(radius * 2)
            if diameter_px > 10:
                scale = known_size_mm / diameter_px
                return {
                    "marker_size_px": round(diameter_px, 2),
                    "known_size_mm": known_size_mm,
                    "scale_mm_per_px": scale,
                    "is_automatic": True,
                    "marker_type": "circle"
                }

        # 2. Try thresholding & finding bright square/rectangular contour
        _, thresh = cv2.threshold(blurred, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 400 < area < 50000:
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w) / h
                    if 0.8 <= aspect_ratio <= 1.2:
                        marker_size_px = float((w + h) / 2.0)
                        scale = known_size_mm / marker_size_px
                        return {
                            "marker_size_px": round(marker_size_px, 2),
                            "known_size_mm": known_size_mm,
                            "scale_mm_per_px": scale,
                            "is_automatic": True,
                            "marker_type": "rectangle"
                        }

        # 3. Fallback: Default estimated marker size (e.g. 100px = 10mm -> 10px/mm)
        h, w = img.shape[:2]
        default_marker_px = min(w, h) * 0.1  # Assume 10% of frame dimension if undetected
        if default_marker_px < 20:
            default_marker_px = 100.0
        scale = known_size_mm / default_marker_px

        return {
            "marker_size_px": round(default_marker_px, 2),
            "known_size_mm": known_size_mm,
            "scale_mm_per_px": scale,
            "is_automatic": False,
            "marker_type": "estimated_fallback"
        }

    @staticmethod
    def calculate_scale_manual(known_size_mm: float, marker_size_px: float) -> Dict[str, Any]:
        """
        Calculates linear scale from user-specified marker size in pixels and mm.
        """
        if marker_size_px <= 0:
            raise ValueError("Marker size in pixels must be greater than zero.")
        if known_size_mm <= 0:
            raise ValueError("Known marker size in mm must be greater than zero.")

        scale = known_size_mm / marker_size_px
        return {
            "marker_size_px": round(marker_size_px, 2),
            "known_size_mm": known_size_mm,
            "scale_mm_per_px": scale,
            "is_automatic": False
        }

    @staticmethod
    def calculate_area_mm2(pixel_count: int, scale_mm_per_px: float) -> Tuple[float, float]:
        """
        Calculates wound area:
        Area (mm²) = pixel_count * (scale_mm_per_px ^ 2)
        Area (cm²) = Area (mm²) / 100
        """
        area_mm2 = float(pixel_count) * (scale_mm_per_px ** 2)
        area_cm2 = area_mm2 / 100.0
        return round(area_mm2, 2), round(area_cm2, 3)
