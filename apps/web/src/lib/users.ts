import api from "./api";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

export interface UpdateProfileRequest {
  full_name?: string;
  email?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export const usersApi = {
  async getProfile(): Promise<User> {
    const response = await api.get("/auth/me");
    return response.data;
  },

  async updateProfile(request: UpdateProfileRequest): Promise<User> {
    const response = await api.patch("/auth/me", request);
    return response.data;
  },

  async changePassword(request: ChangePasswordRequest): Promise<void> {
    await api.post("/auth/change-password", request);
  },

  async deleteAccount(): Promise<void> {
    await api.delete("/auth/me");
  },
};
