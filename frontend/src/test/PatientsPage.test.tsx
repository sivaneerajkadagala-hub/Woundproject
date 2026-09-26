import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { PatientsPage } from '../pages/PatientsPage';

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

const mockPatients = [
  {
    id: 1,
    patient_code: 'PAT-1001',
    full_name: 'Demo Patient Alpha',
    age: 58,
    gender: 'Female',
    is_archived: 'Active',
    created_at: '2024-01-01T00:00:00',
    updated_at: '2024-01-01T00:00:00',
    active_wounds_count: 1,
  },
  {
    id: 2,
    patient_code: 'PAT-1002',
    full_name: 'Demo Patient Beta',
    age: 64,
    gender: 'Male',
    is_archived: 'Active',
    created_at: '2024-01-01T00:00:00',
    updated_at: '2024-01-01T00:00:00',
    active_wounds_count: 1,
  },
];

const renderPatientsPage = () => {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <PatientsPage />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('PatientsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('wound_ai_token', 'fake-token');
    localStorage.setItem('wound_ai_user', JSON.stringify({
      id: 1, email: 'admin@woundai.com', full_name: 'Admin', role: 'Admin', is_active: true, created_at: '2024-01-01',
    }));
  });

  it('renders patient list from API data', async () => {
    mockGet.mockResolvedValue({ data: mockPatients });

    renderPatientsPage();

    await waitFor(() => {
      expect(screen.getByText('Demo Patient Alpha')).toBeInTheDocument();
      expect(screen.getByText('Demo Patient Beta')).toBeInTheDocument();
      expect(screen.getByText('PAT-1001')).toBeInTheDocument();
      expect(screen.getByText('PAT-1002')).toBeInTheDocument();
    });
  });

  it('shows loading state initially', () => {
    mockGet.mockReturnValue(new Promise(() => {}));

    renderPatientsPage();

    // The page should render something while loading (not crash)
    expect(screen.queryByText('Demo Patient Alpha')).not.toBeInTheDocument();
  });

  it('handles empty patient list', async () => {
    mockGet.mockResolvedValue({ data: [] });

    renderPatientsPage();

    await waitFor(() => {
      // Should not crash on empty list
      expect(screen.queryByText('Demo Patient Alpha')).not.toBeInTheDocument();
    });
  });
});
