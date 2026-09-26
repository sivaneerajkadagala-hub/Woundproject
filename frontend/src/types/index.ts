export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'Admin' | 'Clinician' | 'Staff';
  is_active: boolean;
  created_at: string;
}

export interface Patient {
  id: number;
  patient_code: string;
  full_name: string;
  age?: number;
  gender?: string;
  medical_notes?: string;
  is_archived: string;
  created_at: string;
  updated_at: string;
  active_wounds_count?: number;
}

export interface WoundCase {
  id: number;
  case_code: string;
  patient_id: number;
  patient_code?: string;
  patient_name?: string;
  location: string;
  wound_type: string;
  status: 'Active' | 'Healing' | 'Closed' | 'Attention Required';
  notes?: string;
  created_at: string;
  latest_area_mm2?: number;
  latest_visit_date?: string;
  healing_status?: 'Baseline' | 'Improving' | 'Stable' | 'Increasing';
  visits_count?: number;
}

export interface AssessmentDetail {
  visit_id: number;
  wound_id: number;
  visit_number: number;
  visit_date: string;
  clinician_notes?: string;
  original_image_url: string;
  mask_image_url: string;
  overlay_image_url: string;
  image_width: number;
  image_height: number;
  known_size_mm: number;
  marker_size_px: number;
  scale_mm_per_px: number;
  is_automatic_calibration: boolean;
  confidence_score: number;
  wound_pixel_area: number;
  segmentation_method: string;
  area_mm2: number;
  area_cm2: number;
  width_mm: number;
  height_mm: number;
  percentage_change?: number;
  healing_status: 'Baseline' | 'Improving' | 'Stable' | 'Increasing';
  requires_clinical_review?: boolean;
  clinical_review_notice?: string;
}

export interface HealingHistoryPoint {
  visit_id: number;
  visit_number: number;
  visit_date: string;
  area_mm2: number;
  area_cm2: number;
  percentage_change?: number;
  healing_status: string;
  overlay_image_url?: string;
}

export interface DashboardSummary {
  total_patients: number;
  active_wounds: number;
  total_measurements: number;
  improving_wounds: number;
  attention_wounds: number;
  recent_assessments: Array<{
    visit_id: number;
    patient_code: string;
    patient_name: string;
    case_code: string;
    location: string;
    visit_date: string;
    area_mm2: number;
    percentage_change?: number;
    healing_status: string;
  }>;
}

export interface HealingTrendPoint {
  visit_number: number;
  label: string;
  avg_area_mm2: number;
  date: string | null;
}
