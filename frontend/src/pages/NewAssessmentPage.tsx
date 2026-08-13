import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { UploadCloud, Ruler, Cpu, CheckCircle, ArrowRight, ShieldCheck, RefreshCw } from 'lucide-react';
import { Card } from '../components/ui/Card';
import { ImageUploader } from '../components/assessment/ImageUploader';
import { CalibrationStep } from '../components/assessment/CalibrationStep';
import { MaskViewer } from '../components/assessment/MaskViewer';
import { Patient, WoundCase } from '../types';
import api from '../services/api';

export const NewAssessmentPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialWoundId = searchParams.get('wound_id');

  const [patients, setPatients] = useState<Patient[]>([]);
  const [wounds, setWounds] = useState<WoundCase[]>([]);
  
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [selectedWoundId, setSelectedWoundId] = useState<string>(initialWoundId || '');

  // Workflow State: 1: Upload, 2: Calibrate, 3: Segment & Calculate
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMsg, setStatusMsg] = useState<string>('');

  // Uploaded Image State
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [serverImagePath, setServerImagePath] = useState<string>('');
  const [imgWidth, setImgWidth] = useState<number>(600);
  const [imgHeight, setImgHeight] = useState<number>(500);

  // Calibration State
  const [knownSizeMm, setKnownSizeMm] = useState<number>(10.0);
  const [markerSizePx, setMarkerSizePx] = useState<number>(80.0);
  const [scaleMmPerPx, setScaleMmPerPx] = useState<number>(0.125);
  const [isAutoCalibration, setIsAutoCalibration] = useState<boolean>(true);

  // Segmentation State
  const [maskPath, setMaskPath] = useState<string>('');
  const [overlayPath, setOverlayPath] = useState<string>('');
  const [confidenceScore, setConfidenceScore] = useState<number>(0.92);
  const [woundPixelArea, setWoundPixelArea] = useState<number>(20000);
  const [areaMm2, setAreaMm2] = useState<number>(312.5);
  const [areaCm2, setAreaCm2] = useState<number>(3.125);
  const [widthMm, setWidthMm] = useState<number>(17.7);
  const [heightMm, setHeightMm] = useState<number>(17.7);
  const [notes, setNotes] = useState<string>('');

  const navigate = useNavigate();

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const res = await api.get('/patients');
        setPatients(res.data);
        if (res.data.length > 0 && !selectedPatientId) {
          setSelectedPatientId(res.data[0].id.toString());
        }
      } catch (err) {
        console.error('Error fetching patients:', err);
      }
    };
    fetchPatients();
  }, []);

  useEffect(() => {
    const fetchWounds = async () => {
      if (!selectedPatientId) return;
      try {
        const res = await api.get('/wounds', { params: { patient_id: selectedPatientId } });
        setWounds(res.data);
        if (res.data.length > 0 && !selectedWoundId) {
          setSelectedWoundId(res.data[0].id.toString());
        }
      } catch (err) {
        console.error('Error fetching wounds:', err);
      }
    };
    fetchWounds();
  }, [selectedPatientId]);

  const handleImageSelected = (file: File, preview: string, width: number, height: number) => {
    setImageFile(file);
    setPreviewUrl(preview);
    setImgWidth(width);
    setImgHeight(height);
  };

  const handleClearImage = () => {
    setImageFile(null);
    setPreviewUrl('');
    setServerImagePath('');
    setStep(1);
  };

  // Step 1 -> 2: Upload to backend
  const processUpload = async () => {
    if (!imageFile) return;
    setLoading(true);
    setStatusMsg('Uploading wound photograph to secure local processing engine...');

    try {
      const formData = new FormData();
      formData.append('file', imageFile);

      const res = await api.post('/assessments/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setServerImagePath(res.data.original_path);

      // Perform Calibration
      setStatusMsg('Detecting 10mm calibration target via OpenCV...');
      const calForm = new FormData();
      calForm.append('image_id', '0');
      calForm.append('known_size_mm', knownSizeMm.toString());
      calForm.append('image_path', res.data.original_path);

      const calRes = await api.post('/assessments/calibrate', calForm);
      setKnownSizeMm(calRes.data.known_size_mm);
      setMarkerSizePx(calRes.data.marker_size_px);
      setScaleMmPerPx(calRes.data.scale_mm_per_px);
      setIsAutoCalibration(calRes.data.is_automatic);

      setStep(2);
    } catch (err: any) {
      console.error('Upload / Calibration error:', err);
    } finally {
      setLoading(false);
      setStatusMsg('');
    }
  };

  const handleCalibrationChange = (knownMm: number, markerPx: number) => {
    setKnownSizeMm(knownMm);
    setMarkerSizePx(markerPx);
    const newScale = knownMm / markerPx;
    setScaleMmPerPx(newScale);
    setIsAutoCalibration(false);
    recalculateArea(woundPixelArea, newScale);
  };

  const recalculateArea = (pxArea: number, scale: number) => {
    const mm2 = pxArea * (scale * scale);
    const cm2 = mm2 / 100.0;
    const wMm = Math.sqrt(pxArea) * scale;
    setAreaMm2(roundVal(mm2, 2));
    setAreaCm2(roundVal(cm2, 3));
    setWidthMm(roundVal(wMm, 1));
    setHeightMm(roundVal(wMm, 1));
  };

  function roundVal(v: number, decimals: number) {
    const factor = Math.pow(10, decimals);
    return Math.round(v * factor) / factor;
  }

  // Step 2 -> 3: U-Net Segmentation
  const processSegmentation = async () => {
    if (!serverImagePath) return;
    setLoading(true);
    setStatusMsg('Running pretrained PyTorch U-Net segmentation inference...');

    try {
      const segForm = new FormData();
      segForm.append('image_id', '0');
      segForm.append('image_path', serverImagePath);
      segForm.append('threshold', '0.5');

      const segRes = await api.post('/assessments/segment', segForm);
      setMaskPath(segRes.data.mask_path);
      setOverlayPath(segRes.data.overlay_path);
      setConfidenceScore(segRes.data.confidence_score);
      setWoundPixelArea(segRes.data.wound_pixel_area);

      recalculateArea(segRes.data.wound_pixel_area, scaleMmPerPx);

      setStep(3);
    } catch (err) {
      console.error('Segmentation error:', err);
    } finally {
      setLoading(false);
      setStatusMsg('');
    }
  };

  // Step 3: Finalize Assessment
  const handleSaveAssessment = async () => {
    if (!selectedWoundId) return;
    setLoading(true);
    setStatusMsg('Finalizing assessment & calculating longitudinal trajectory...');

    try {
      const areaForm = new FormData();
      areaForm.append('image_id', '0');
      areaForm.append('wound_id', selectedWoundId);
      areaForm.append('image_path', serverImagePath);
      areaForm.append('mask_path', maskPath);
      areaForm.append('overlay_path', overlayPath);
      areaForm.append('confidence_score', confidenceScore.toString());
      areaForm.append('wound_pixel_area', woundPixelArea.toString());
      areaForm.append('scale_mm_per_px', scaleMmPerPx.toString());
      areaForm.append('marker_size_px', markerSizePx.toString());
      areaForm.append('known_size_mm', knownSizeMm.toString());
      areaForm.append('is_automatic_calibration', isAutoCalibration ? 'true' : 'false');
      areaForm.append('notes', notes);

      const res = await api.post('/assessments/calculate-area', areaForm);
      navigate(`/assessment/${res.data.visit_id}`);
    } catch (err) {
      console.error('Error finalizing assessment:', err);
    } finally {
      setLoading(false);
      setStatusMsg('');
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Title */}
      <div>
        <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">New AI Wound Assessment</h2>
        <p className="text-xs text-slate-500">Upload photograph, perform scale calibration, and execute U-Net segmentation</p>
      </div>

      {/* Case Selector Card */}
      <Card className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Select Patient</label>
          <select
            value={selectedPatientId}
            onChange={(e) => {
              setSelectedPatientId(e.target.value);
              setSelectedWoundId('');
            }}
            className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-cyan-500"
          >
            {patients.map((p) => (
              <option key={p.id} value={p.id}>
                {p.patient_code} - {p.full_name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">Select Active Wound Case</label>
          <select
            value={selectedWoundId}
            onChange={(e) => setSelectedWoundId(e.target.value)}
            className="w-full px-3.5 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs font-semibold text-slate-800 focus:ring-2 focus:ring-cyan-500"
          >
            {wounds.map((w) => (
              <option key={w.id} value={w.id}>
                {w.case_code} - {w.location} ({w.wound_type})
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Workflow Step Bar */}
      <div className="flex items-center justify-between bg-slate-900 text-white p-4 rounded-2xl border border-slate-800 font-medium text-xs">
        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-cyan-400 font-bold' : 'text-slate-500'}`}>
          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-xs">1</span>
          <span>1. Upload Photograph</span>
        </div>
        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-cyan-400 font-bold' : 'text-slate-500'}`}>
          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-xs">2</span>
          <span>2. Calibration Scale</span>
        </div>
        <div className={`flex items-center gap-2 ${step >= 3 ? 'text-cyan-400 font-bold' : 'text-slate-500'}`}>
          <span className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-xs">3</span>
          <span>3. U-Net Segmentation & Area</span>
        </div>
      </div>

      {/* Step 1: Image Upload */}
      {step === 1 && (
        <Card className="space-y-4">
          <h3 className="font-bold text-slate-900 text-base">Step 1: Select Wound Image</h3>
          <ImageUploader
            onImageSelected={handleImageSelected}
            selectedPreview={previewUrl}
            onClearImage={handleClearImage}
          />

          {imageFile && (
            <button
              onClick={processUpload}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>{statusMsg || 'Processing...'}</span>
              ) : (
                <>
                  <span>Proceed to Calibration Step</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          )}
        </Card>
      )}

      {/* Step 2: Calibration */}
      {step >= 2 && (
        <div className="space-y-6">
          <CalibrationStep
            knownSizeMm={knownSizeMm}
            markerSizePx={markerSizePx}
            scaleMmPerPx={scaleMmPerPx}
            isAutomatic={isAutoCalibration}
            onCalibrationChange={handleCalibrationChange}
          />

          {step === 2 && (
            <button
              onClick={processSegmentation}
              disabled={loading}
              className="w-full py-3 bg-gradient-to-r from-cyan-600 to-teal-500 hover:from-cyan-500 hover:to-teal-400 text-white font-bold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>{statusMsg || 'Running Segmentation...'}</span>
              ) : (
                <>
                  <Cpu className="w-4 h-4" />
                  <span>Execute Pretrained U-Net Segmentation</span>
                </>
              )}
            </button>
          )}
        </div>
      )}

      {/* Step 3: Segmentation Results & Save */}
      {step === 3 && (
        <div className="space-y-6">
          <MaskViewer
            originalUrl={`/api/assessments/media?path=${serverImagePath}`}
            maskUrl={`/api/assessments/media?path=${maskPath}`}
            overlayUrl={`/api/assessments/media?path=${overlayPath}`}
            confidenceScore={confidenceScore}
            pixelArea={woundPixelArea}
            areaMm2={areaMm2}
            areaCm2={areaCm2}
            widthMm={widthMm}
            heightMm={heightMm}
          />

          {/* Clinician Notes Input */}
          <Card className="space-y-4">
            <h4 className="font-bold text-slate-900 text-sm">Clinician Observations & Assessment Notes</h4>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record clinical observations, exudate type, tissue granulation details..."
              className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-cyan-500"
            />

            <button
              onClick={handleSaveAssessment}
              disabled={loading}
              className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <span>Saving Assessment...</span>
              ) : (
                <>
                  <CheckCircle className="w-5 h-5" />
                  <span>Finalize & Record Visit Assessment</span>
                </>
              )}
            </button>
          </Card>
        </div>
      )}
    </div>
  );
};
