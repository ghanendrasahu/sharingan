import api from "./api";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
}

export const authApi = {
  async login(request: LoginRequest): Promise<AuthResponse> {
    const response = await api.post("/auth/login", request);
    return response.data;
  },

  async register(request: RegisterRequest): Promise<UserResponse> {
    const response = await api.post("/auth/register", request);
    return response.data;
  },

  async getCurrentUser(): Promise<UserResponse> {
    const response = await api.get("/auth/me");
    return response.data;
  },

  async logout(): Promise<void> {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem("access_token");
  },
};
