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
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    organization_id: string;
  };
}

export const authApi = {
  async login(request: LoginRequest): Promise<AuthResponse> {
    const formData = new URLSearchParams();
    formData.append("username", request.email);
    formData.append("password", request.password);

    const response = await api.post("/auth/login", formData, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
    return response.data;
  },

  async register(request: RegisterRequest): Promise<AuthResponse> {
    const response = await api.post("/auth/register", request);
    return response.data;
  },

  async getCurrentUser(): Promise<AuthResponse["user"]> {
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
