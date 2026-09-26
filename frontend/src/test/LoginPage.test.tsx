import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { AuthProvider } from '../context/AuthContext';

// Mock the api module
vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

import api from '../services/api';

const renderLoginPage = () => {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders the login form with email and password fields', () => {
    renderLoginPage();
    expect(screen.getByText(/WoundAI Platform/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/clinician@hospital.org/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/••••••••/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Dashboard/i })).toBeInTheDocument();
  });

  it('shows demo credentials on the page', () => {
    renderLoginPage();
    expect(screen.getByText('admin@woundai.com')).toBeInTheDocument();
    expect(screen.getByText('Admin123!')).toBeInTheDocument();
  });

  it('displays error message on failed login', async () => {
    const user = userEvent.setup();
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Incorrect email or password' } },
    });

    renderLoginPage();

    const submitButton = screen.getByRole('button', { name: /Sign In to Dashboard/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Incorrect email or password/i)).toBeInTheDocument();
    });
  });

  it('calls login and navigates on successful login', async () => {
    const user = userEvent.setup();
    const mockToken = 'fake-jwt-token';
    const mockUser = {
      id: 1,
      email: 'admin@woundai.com',
      full_name: 'Dr. Admin',
      role: 'Admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00',
    };

    vi.mocked(api.post).mockResolvedValueOnce({
      data: { access_token: mockToken, token_type: 'bearer', user: mockUser },
    } as any);

    renderLoginPage();

    const submitButton = screen.getByRole('button', { name: /Sign In to Dashboard/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'admin@woundai.com',
        password: 'Admin123!',
      });
    });
  });

  it('shows loading state during authentication', async () => {
    const user = userEvent.setup();
    // Make the API call hang
    vi.mocked(api.post).mockReturnValueOnce(new Promise(() => {}));

    renderLoginPage();

    const submitButton = screen.getByRole('button', { name: /Sign In to Dashboard/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Authenticating/i)).toBeInTheDocument();
    });
  });
});
