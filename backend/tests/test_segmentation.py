import os
import cv2
import numpy as np
import pytest
from app.ml.segmentation import segmentation_engine
from app.services.seed_service import generate_synthetic_wound_image
from app.core.config import settings

def test_synthetic_wound_image_generation_and_segmentation(tmp_path):
    img_filename = "test_wound_segmentation.jpg"
    img_path = generate_synthetic_wound_image(img_filename, wound_radius_x=60, wound_radius_y=45)

    assert os.path.exists(img_path)

    mask_out = str(tmp_path / "test_mask.png")
    overlay_out = str(tmp_path / "test_overlay.jpg")

    res = segmentation_engine.segment_wound(
        image_path=img_path,
        output_mask_path=mask_out,
        output_overlay_path=overlay_out
    )

    assert res["processing_status"] == "Completed"
    assert res["wound_pixel_area"] > 0
    assert os.path.exists(mask_out)
    assert os.path.exists(overlay_out)
