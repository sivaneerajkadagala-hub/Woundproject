import React, { useState, useRef } from 'react';
import { UploadCloud, Image as ImageIcon, CheckCircle, AlertCircle, X } from 'lucide-react';

interface ImageUploaderProps {
  onImageSelected: (file: File, previewUrl: string, width: number, height: number) => void;
  selectedPreview?: string;
  onClearImage?: () => void;
}

export const ImageUploader: React.FC<ImageUploaderProps> = ({
  onImageSelected,
  selectedPreview,
  onClearImage
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setError(null);
    if (!file.type.startsWith('image/')) {
      setError('Please select a valid image file (JPG, JPEG, or PNG).');
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError('File size exceeds maximum 20MB limit.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        onImageSelected(file, e.target?.result as string, img.width, img.height);
      };
      img.src = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-3">
      {selectedPreview ? (
        <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-900 group shadow-md">
          <img
            src={selectedPreview}
            alt="Wound preview"
            className="w-full max-h-96 object-contain mx-auto"
          />
          <button
            type="button"
            onClick={onClearImage}
            className="absolute top-3 right-3 bg-slate-900/80 text-white p-2 rounded-full hover:bg-rose-600 transition-colors shadow-lg"
            title="Remove image"
          >
            <X className="w-4 h-4" />
          </button>
          <div className="absolute bottom-3 left-3 bg-slate-900/80 backdrop-blur-sm text-cyan-300 px-3 py-1 rounded-lg text-xs font-mono border border-cyan-500/30">
            Image Ready for Calibration
          </div>
        </div>
      ) : (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 ${
            dragActive
              ? 'border-cyan-500 bg-cyan-50/50 scale-[1.01]'
              : 'border-slate-300 hover:border-cyan-500 hover:bg-slate-50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/jpg"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <div className="w-14 h-14 bg-cyan-50 text-cyan-600 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-cyan-100 shadow-sm">
            <UploadCloud className="w-7 h-7" />
          </div>
          <h4 className="font-semibold text-slate-800 text-base mb-1">
            Upload Wound Photograph
          </h4>
          <p className="text-xs text-slate-500 mb-3 max-w-sm mx-auto">
            Drag and drop your image here, or click to browse files (JPG or PNG up to 20MB).
          </p>
          <div className="inline-flex items-center gap-1.5 bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-medium">
            <ImageIcon className="w-3.5 h-3.5" />
            <span>Target should include 10mm calibration marker</span>
          </div>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 bg-rose-50 text-rose-700 border border-rose-200 p-3 rounded-xl text-xs font-medium">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
