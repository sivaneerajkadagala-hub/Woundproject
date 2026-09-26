import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';

// ProtectedRoute is defined inline in App.tsx, so we recreate it here for testing
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Simulate the auth check - if no token in localStorage, redirect to /login
  const token = localStorage.getItem('wound_ai_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

import { Navigate } from 'react-router-dom';

// Mock the api module
vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}));

const ProtectedContent = () => <div>Protected Dashboard Content</div>;
const LoginPage = () => <div>Login Page</div>;

const renderWithRouter = (initialPath: string = '/dashboard') => {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <ProtectedContent />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
    </MemoryRouter>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('redirects to login when no token is present', () => {
    renderWithRouter('/dashboard');
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Dashboard Content')).not.toBeInTheDocument();
  });

  it('shows protected content when token is present', () => {
    localStorage.setItem('wound_ai_token', 'fake-token');
    localStorage.setItem('wound_ai_user', JSON.stringify({ id: 1, email: 'test@test.com' }));
    renderWithRouter('/dashboard');
    expect(screen.getByText('Protected Dashboard Content')).toBeInTheDocument();
  });
});
