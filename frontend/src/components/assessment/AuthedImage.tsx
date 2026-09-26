import React, { useState, useEffect, useRef, useCallback } from 'react';
import { AlertCircle, RefreshCw, Loader2 } from 'lucide-react';

interface AuthedImageProps {
  /** The full API URL to fetch (e.g. "/api/assessments/media?path=...") */
  src: string;
  alt: string;
  className?: string;
}

/**
 * Renders an image that requires JWT authentication.
 *
 * Standard <img> tags cannot send Authorization headers, so authenticated
 * media endpoints return 401. This component fetches the image via
 * window.fetch with the Bearer token, creates an object URL from the
 * Blob response, and uses that as the <img> src. The object URL is
 * revoked on unmount or when the src changes to prevent memory leaks.
 *
 * Uses fetch directly (not the axios instance) because the axios instance
 * has baseURL='/api' which would double the /api prefix in the URL.
 */
export const AuthedImage: React.FC<AuthedImageProps> = ({ src, alt, className }) => {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState<number>(0);
  const prevUrlRef = useRef<string | null>(null);

  const fetchImage = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Revoke previous object URL to prevent memory leaks
    if (prevUrlRef.current) {
      URL.revokeObjectURL(prevUrlRef.current);
      prevUrlRef.current = null;
    }

    if (!src) {
      setError('No image URL provided.');
      setLoading(false);
      return;
    }

    try {
      const token = localStorage.getItem('wound_ai_token');
      const response = await fetch(src, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Authentication required to view this image.');
        } else if (response.status === 404) {
          throw new Error('Image file not found on server.');
        } else if (response.status === 403) {
          throw new Error('Access denied to this image.');
        } else {
          throw new Error('Unable to load wound image.');
        }
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      prevUrlRef.current = url;
      setObjectUrl(url);
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Unable to load wound image.');
      setLoading(false);
    }
  }, [src]);

  useEffect(() => {
    fetchImage();
  }, [fetchImage, retryCount]);

  // Cleanup object URL on unmount
  useEffect(() => {
    return () => {
      if (prevUrlRef.current) {
        URL.revokeObjectURL(prevUrlRef.current);
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 text-slate-400">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <span className="text-xs font-medium">Loading wound image...</span>
      </div>
    );
  }

  if (error || !objectUrl) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 text-slate-400">
        <AlertCircle className="w-8 h-8 text-rose-400" />
        <span className="text-xs font-medium text-rose-300">{error || 'Unable to load image.'}</span>
        <button
          type="button"
          onClick={() => setRetryCount((c) => c + 1)}
          className="text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1.5 transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Retry</span>
        </button>
      </div>
    );
  }

  return (
    <img
      src={objectUrl}
      alt={alt}
      className={className}
    />
  );
};
