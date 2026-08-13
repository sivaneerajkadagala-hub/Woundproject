import pytest
from app.ml.calibration import CalibrationEngine

def test_calibration_manual_scale():
    # 100 pixels = 10 mm -> scale = 0.1 mm/px
    res = CalibrationEngine.calculate_scale_manual(known_size_mm=10.0, marker_size_px=100.0)
    assert res["scale_mm_per_px"] == 0.1
    assert res["known_size_mm"] == 10.0
    assert res["marker_size_px"] == 100.0

def test_area_calculation_mm2():
    # If scale = 0.1 mm/px, scale^2 = 0.01 mm²/px²
    # 20,000 pixels² * 0.01 = 200 mm²
    area_mm2, area_cm2 = CalibrationEngine.calculate_area_mm2(pixel_count=20000, scale_mm_per_px=0.1)
    assert area_mm2 == 200.0
    assert area_cm2 == 2.0

def test_invalid_calibration_input():
    with pytest.raises(ValueError):
        CalibrationEngine.calculate_scale_manual(known_size_mm=10.0, marker_size_px=0.0)
