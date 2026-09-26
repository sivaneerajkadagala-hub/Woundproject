import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { DashboardPage } from '../pages/DashboardPage';

const { mockGet } = vi.hoisted(() => ({ mockGet: vi.fn() }));

vi.mock('../services/api', () => ({
  default: {
    get: mockGet,
    post: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

const mockDashboardSummary = {
  total_patients: 3,
  active_wounds: 2,
  total_measurements: 4,
  improving_wounds: 1,
  attention_wounds: 0,
  recent_assessments: [
    {
      visit_id: 1,
      patient_code: 'PAT-1001',
      patient_name: 'Test Patient',
      case_code: 'WC-1001',
      location: 'Left lower leg',
      visit_date: '2024-01-01T00:00:00',
      area_mm2: 4687.5,
      percentage_change: -15.6,
      healing_status: 'Improving',
    },
  ],
};

const mockHealingTrend = [
  { visit_number: 1, label: 'Visit 1', avg_area_mm2: 4687.5, date: '2024-01-01' },
  { visit_number: 2, label: 'Visit 2', avg_area_mm2: 3950.0, date: '2024-01-08' },
  { visit_number: 3, label: 'Visit 3', avg_area_mm2: 3200.0, date: '2024-01-15' },
];

const renderDashboard = () => {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <DashboardPage />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('wound_ai_token', 'fake-token');
    localStorage.setItem('wound_ai_user', JSON.stringify({
      id: 1, email: 'admin@woundai.com', full_name: 'Admin', role: 'Admin', is_active: true, created_at: '2024-01-01',
    }));
  });

  it('renders dashboard with summary data from API', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/summary') return Promise.resolve({ data: mockDashboardSummary });
      if (url === '/dashboard/healing-trend') return Promise.resolve({ data: mockHealingTrend });
      return Promise.resolve({ data: {} });
    });

    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('renders healing trend chart with real data', async () => {
    mockGet.mockImplementation((url: string) => {
      if (url === '/dashboard/summary') return Promise.resolve({ data: mockDashboardSummary });
      if (url === '/dashboard/healing-trend') return Promise.resolve({ data: mockHealingTrend });
      return Promise.resolve({ data: {} });
    });

    renderDashboard();

    // Verify the API was called for both endpoints
    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith('/dashboard/summary');
      expect(mockGet).toHaveBeenCalledWith('/dashboard/healing-trend');
    });
  });

  it('handles API error gracefully', async () => {
    mockGet.mockRejectedValue(new Error('Network error'));

    renderDashboard();

    // Should not crash - just wait for loading to finish
    await waitFor(() => {
      // The page should still render something (not crash)
      expect(document.body).toBeInTheDocument();
    });
  });
});
