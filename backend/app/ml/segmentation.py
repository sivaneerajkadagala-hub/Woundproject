import os
import logging
import cv2
import numpy as np
from typing import Dict, Any
from app.core.config import settings

logger = logging.getLogger("wound_ai.segmentation")

# Path to optional pretrained U-Net checkpoint
UNET_CHECKPOINT_PATH = os.getenv("UNET_CHECKPOINT_PATH", "")


class SegmentationService:
    """
    Segmentation service with two strategies:

    1. CV color-based segmentation (default, reliable for synthetic/demo data)
    2. U-Net segmentation (used only when a real pretrained checkpoint is available)

    The service automatically selects the appropriate method. When no trained
    checkpoint is found, it falls back to the CV method and clearly reports
    which method was used in the result metadata.
    """

    def __init__(self):
        self.unet_model = None
        self.device = "cpu"
        self._unet_available = False
        self._init_unet()

    def _init_unet(self):
        """
        Attempt to load a pretrained U-Net checkpoint.
        The model is only marked as available if a checkpoint file exists
        AND can be loaded successfully. An untrained model (random decoder
        weights) is never used for inference.
        """
        if not UNET_CHECKPOINT_PATH or not os.path.exists(UNET_CHECKPOINT_PATH):
            logger.info("No U-Net checkpoint found. Using CV segmentation as default.")
            self._unet_available = False
            return

        try:
            import torch
            import segmentation_models_pytorch as smp

            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading U-Net checkpoint from {UNET_CHECKPOINT_PATH} on {self.device}")

            self.unet_model = smp.Unet(
                encoder_name="resnet34",
                encoder_weights="imagenet",
                in_channels=3,
                classes=1,
                activation=None
            )

            checkpoint = torch.load(UNET_CHECKPOINT_PATH, map_location=self.device)
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                self.unet_model.load_state_dict(checkpoint["state_dict"])
            elif isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
                self.unet_model.load_state_dict(checkpoint["model_state_dict"])
            else:
                self.unet_model.load_state_dict(checkpoint)

            self.unet_model.to(self.device)
            self.unet_model.eval()
            self._unet_available = True
            logger.info("U-Net checkpoint loaded successfully. U-Net segmentation available.")
        except Exception as e:
            logger.warning(f"Failed to load U-Net checkpoint: {e}. Using CV segmentation.")
            self.unet_model = None
            self._unet_available = False

    def segment_wound(
        self,
        image_path: str,
        output_mask_path: str,
        output_overlay_path: str,
        threshold: float = 0.5,
        force_method: str = ""
    ) -> Dict[str, Any]:
        """
        Execute wound segmentation pipeline.

        Method selection:
        - If force_method is specified ("cv_color" or "unet"), use that method.
        - If U-Net is available (checkpoint loaded), use U-Net.
        - Otherwise, use CV color segmentation (default).

        Returns dict with mask_path, overlay_path, confidence_score,
        wound_pixel_area, width_px, height_px, segmentation_method, processing_status.
        """
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError(f"Unable to read image at {image_path}")

        h, w, c = img_bgr.shape

        # Determine which method to use
        use_unet = False
        if force_method == "unet" and self._unet_available:
            use_unet = True
        elif force_method == "cv_color":
            use_unet = False
        elif self._unet_available:
            use_unet = True

        if use_unet:
            result = self._segment_unet(img_bgr, h, w, threshold)
        else:
            result = self._segment_cv(img_bgr, h, w)

        binary_mask = result["binary_mask"]
        confidence_score = result["confidence_score"]
        segmentation_method = result["segmentation_method"]

        # Count wound pixels
        wound_pixel_area = int(np.count_nonzero(binary_mask))

        # Calculate bounding box dimensions from the mask
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        width_px, height_px = 0, 0
        if contours:
            x, y, bw, bh = cv2.boundingRect(np.vstack(contours))
            width_px = bw
            height_px = bh
        else:
            width_px = int(np.sqrt(wound_pixel_area))
            height_px = int(np.sqrt(wound_pixel_area))

        # Save Binary Mask Image (Black background, White wound)
        cv2.imwrite(output_mask_path, binary_mask)

        # Create Transparent Red Overlay on Original Image
        overlay_img = img_bgr.copy()
        if wound_pixel_area > 0 and contours:
            red_tint = np.zeros_like(img_bgr, dtype=np.uint8)
            red_tint[:, :, 2] = 255  # Red channel

            wound_indices = binary_mask > 0
            overlay_img[wound_indices] = cv2.addWeighted(
                img_bgr[wound_indices], 0.6,
                red_tint[wound_indices], 0.4,
                0
            )
            # Draw wound border outline
            cv2.drawContours(overlay_img, contours, -1, (0, 255, 255), 2)  # Yellow border

        cv2.imwrite(output_overlay_path, overlay_img)

        return {
            "mask_path": output_mask_path,
            "overlay_path": output_overlay_path,
            "confidence_score": round(confidence_score, 2),
            "wound_pixel_area": wound_pixel_area,
            "width_px": width_px,
            "height_px": height_px,
            "segmentation_method": segmentation_method,
            "processing_status": "Completed"
        }

    def _segment_unet(self, img_bgr, h, w, threshold) -> Dict[str, Any]:
        """Run U-Net inference (only called when a real checkpoint is loaded)."""
        import torch

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        try:
            input_tensor = cv2.resize(img_rgb, (256, 256))
            input_tensor = input_tensor.astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            input_tensor = (input_tensor - mean) / std
            input_tensor = np.transpose(input_tensor, (2, 0, 1))
            input_tensor = torch.tensor(input_tensor).unsqueeze(0).to(self.device)

            with torch.no_grad():
                logits = self.unet_model(input_tensor)
                probs = torch.sigmoid(logits).squeeze().cpu().numpy()

            prob_map = cv2.resize(probs, (w, h))
            binary_mask = (prob_map >= threshold).astype(np.uint8) * 255
            confidence_score = float(np.mean(prob_map[prob_map >= threshold])) if np.any(prob_map >= threshold) else 0.5

            return {
                "binary_mask": binary_mask,
                "confidence_score": confidence_score,
                "segmentation_method": "unet"
            }
        except Exception as e:
            logger.error(f"U-Net inference error, falling back to CV: {e}")
            return self._segment_cv(img_bgr, h, w)

    def _segment_cv(self, img_bgr, h, w) -> Dict[str, Any]:
        """
        OpenCV wound segmentation using adaptive multi-stage analysis.

        Distinguishes the actual wound from surrounding erythema/inflammation
        by combining:

        1. LAB a* redness deviation from skin tone (adaptive per image)
        2. Otsu automatic thresholding on the reddish region (separates
           wound from erythema without a fixed threshold)
        3. Gradient-based boundary detection (wound has sharp edges,
           erythema has gradual/diffuse transitions)
        4. Watershed segmentation seeded by the wound core
        5. Connected component scoring by wound-specific features
           (redness intensity, local contrast, compactness, texture)

        Pipeline:
        Original → LAB a* deviation → reddish region → Otsu threshold
        → wound core (high threshold) → gradient map → watershed
        → select wound basin → boundary refinement → final mask
        """
        # --- Step 1: Color space conversion ---
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        a_channel = lab[:, :, 1].astype(np.float32)
        s_channel = hsv[:, :, 1].astype(np.float32)
        v_channel = hsv[:, :, 2].astype(np.float32)

        # --- Step 2: Adaptive skin tone estimation ---
        median_a = float(np.median(a_channel))
        a_deviation = a_channel - median_a

        # --- Step 3: Define valid tissue region ---
        # Exclude bright/white (calibration markers, background, highlights)
        bright_mask = (v_channel > 200) & (s_channel < 50)
        # Exclude low-saturation (background, non-tissue)
        valid_tissue = (s_channel > 30) & (~bright_mask)

        # --- Step 4: Find reddish region (wound + erythema) ---
        # Use a low threshold to capture all potentially wound-related tissue
        reddish = (a_deviation > 10) & valid_tissue
        reddish_count = np.count_nonzero(reddish)

        if reddish_count < 200:
            # No significant reddish tissue found
            return {
                "binary_mask": np.zeros((h, w), dtype=np.uint8),
                "confidence_score": 0.20,
                "segmentation_method": "cv_color"
            }

        # --- Step 5: Otsu adaptive thresholding ---
        # Apply Otsu on the a* deviation values within the reddish region.
        # Otsu automatically finds the optimal threshold that separates
        # two classes (wound vs erythema) based on the distribution.
        dev_values = np.clip(a_deviation[reddish], 0, 255).astype(np.uint8)
        otsu_thresh_val, _ = cv2.threshold(
            dev_values, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        # Ensure minimum threshold to avoid selecting erythema
        otsu_thresh_val = max(float(otsu_thresh_val), 20.0)

        # --- Step 6: Create wound mask and core mask ---
        # Wound mask: Otsu threshold (wound + some erythema)
        wound_mask = ((a_deviation > otsu_thresh_val) & valid_tissue).astype(np.uint8) * 255

        # Core mask: higher threshold (definitely wound, strong redness)
        max_dev = float(a_deviation[valid_tissue].max())
        core_threshold = max(otsu_thresh_val + 10, max_dev * 0.55)
        core_mask = ((a_deviation > core_threshold) & valid_tissue).astype(np.uint8) * 255

        # --- Step 7: Gradient-based boundary detection ---
        # The wound has sharp boundaries (high gradient) while erythema
        # has gradual transitions (low gradient). Use Sobel on the
        # deviation map to find wound edges.
        grad_x = cv2.Sobel(a_deviation, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(a_deviation, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x ** 2 + grad_y ** 2)

        # --- Step 8: Watershed segmentation ---
        # Use watershed to separate wound from erythema based on gradients.
        # Seed with the wound core, let watershed find the boundary.
        binary_mask = self._watershed_wound_segmentation(
            wound_mask, core_mask, grad_mag, a_deviation, valid_tissue, h, w
        )

        # --- Step 9: Morphological refinement ---
        if np.count_nonzero(binary_mask) > 0:
            kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            # Fill holes
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel_close)
            # Remove small artifacts
            binary_mask = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_small)

        # --- Step 10: Connected component analysis & scoring ---
        # Score remaining components by wound-specific features
        binary_mask, confidence_score = self._select_best_wound_component(
            binary_mask, a_deviation, s_channel, grad_mag, h, w
        )

        return {
            "binary_mask": binary_mask,
            "confidence_score": confidence_score,
            "segmentation_method": "cv_color"
        }

    def _watershed_wound_segmentation(
        self, wound_mask, core_mask, grad_mag, a_deviation, valid_tissue, h, w
    ) -> np.ndarray:
        """
        Use watershed to separate wound from surrounding erythema.
        Seeds = wound core (high redness), boundaries = gradients.
        """
        # If core is empty, fall back to wound_mask
        if np.count_nonzero(core_mask) < 50:
            return wound_mask

        # If wound_mask is not much larger than core, core is sufficient
        wound_px = np.count_nonzero(wound_mask)
        core_px = np.count_nonzero(core_mask)
        if wound_px <= core_px * 1.5:
            return core_mask

        # Prepare markers for watershed
        # Marker 1 = background/skin (everything outside wound_mask)
        # Marker 2 = wound core (definitely wound)
        # Marker 0 = unknown (wound_mask minus core — could be wound or erythema)
        markers = np.zeros((h, w), dtype=np.int32)
        markers[valid_tissue == 0] = 1  # Non-tissue background
        markers[(wound_mask == 0) & (valid_tissue > 0)] = 1  # Skin
        markers[core_mask > 0] = 2  # Wound core seed
        # Unknown region (between core and wound_mask boundary) stays 0

        # Prepare the image for watershed: use deviation map as 3-channel
        dev_vis = np.clip(a_deviation + 50, 0, 255).astype(np.uint8)
        watershed_input = cv2.merge([dev_vis, dev_vis, dev_vis])

        # Run watershed
        markers = cv2.watershed(watershed_input, markers)

        # Extract wound region (marker == 2)
        binary_mask = (markers == 2).astype(np.uint8) * 255

        # If watershed produced too small a result, fall back to core
        if np.count_nonzero(binary_mask) < 100:
            return core_mask

        return binary_mask

    def _select_best_wound_component(
        self, binary_mask, a_deviation, s_channel, grad_mag, h, w
    ) -> tuple:
        """
        Analyze connected components and select the most likely wound region.
        Scores by: redness intensity, local contrast (edge strength),
        texture variation, compactness, and size.
        """
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary_mask, connectivity=8
        )

        if num_labels <= 1:
            return binary_mask, 0.20

        total_pixels = h * w
        candidates = []

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < 200:
                continue
            if area > total_pixels * 0.35:
                continue

            comp_mask = labels == i
            mean_deviation = float(a_deviation[comp_mask].mean())
            mean_saturation = float(s_channel[comp_mask].mean())
            mean_gradient = float(grad_mag[comp_mask].mean())

            # Local texture: standard deviation of deviation within component
            texture = float(a_deviation[comp_mask].std())

            # Compactness: area / bounding_box_area
            x, y, bw, bh = stats[i, cv2.CC_STAT_LEFT], stats[i, cv2.CC_STAT_TOP], \
                           stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            bbox_area = bw * bh
            compactness = area / bbox_area if bbox_area > 0 else 0

            # Edge strength relative to region: how distinct is the boundary?
            # Wound has high gradient at its boundary, erythema doesn't
            boundary_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.drawContours(boundary_mask, [np.array([[x, y], [x+bw, y], [x+bw, y+bh], [x, y+bh]])], 0, 255, 2)
            boundary_grad = float(grad_mag[boundary_mask > 0].mean()) if np.count_nonzero(boundary_mask) > 0 else 0

            # Size score: prefer regions that are 0.5%-15% of image
            size_score = 1.0 if 500 < area < total_pixels * 0.15 else 0.5

            # Redness score: higher deviation = more likely wound
            redness_score = min(mean_deviation / 50.0, 1.0)

            # Contrast score: wound has stronger internal texture
            contrast_score = min(texture / 15.0, 1.0)

            # Boundary score: wound has sharp edges
            boundary_score = min(mean_gradient / 10.0, 1.0)

            # Combined score: redness is primary, but texture and boundary
            # help distinguish wound from diffuse erythema
            score = (redness_score * 0.35 +
                     boundary_score * 0.25 +
                     contrast_score * 0.15 +
                     size_score * 0.15 +
                     compactness * 0.10)

            candidates.append({
                'label': i,
                'area': area,
                'mean_deviation': mean_deviation,
                'mean_gradient': mean_gradient,
                'texture': texture,
                'compactness': compactness,
                'score': score,
                'bbox': (x, y, bw, bh)
            })

        if not candidates:
            return binary_mask, 0.20

        # Sort by score
        candidates.sort(key=lambda c: c['score'], reverse=True)

        # Select the best candidate(s) with meaningful redness
        strong = [c for c in candidates if c['mean_deviation'] > 20]
        if strong:
            selected = strong[:3]  # Top 3 (in case of multiple wound regions)
            final_mask = np.zeros((h, w), dtype=np.uint8)
            for cand in selected:
                final_mask[labels == cand['label']] = 255

            # Confidence based on best candidate's redness and boundary strength
            best = selected[0]
            confidence_score = min(0.40 + best['mean_deviation'] / 70.0, 0.88)
            confidence_score = max(confidence_score, 0.40)
            return final_mask, confidence_score
        else:
            # Only weak candidates — use the best one with low confidence
            best = candidates[0]
            final_mask = np.zeros((h, w), dtype=np.uint8)
            final_mask[labels == best['label']] = 255
            return final_mask, 0.30


# Global Instance
segmentation_engine = SegmentationService()
