import { Navigate, Outlet } from "react-router-dom";
import { authApi } from "../lib/auth";

export function ProtectedRoute() {
  const isAuthenticated = authApi.isAuthenticated();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export function PublicRoute() {
  const isAuthenticated = authApi.isAuthenticated();

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
