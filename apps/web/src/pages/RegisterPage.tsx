import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Mail, Lock, User, Building2 } from "lucide-react";
import { authApi } from "../lib/auth";

export function RegisterPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirm_password: "",
    full_name: "",
    organization_name: "",
  });
  const [error, setError] = useState<string | null>(null);

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.access_token);
      navigate("/");
    },
    onError: (err: Error) => {
      setError(err.message || "Registration failed. Please try again.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (formData.password !== formData.confirm_password) {
      setError("Passwords do not match");
      return;
    }

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    registerMutation.mutate({
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
      organization_name: formData.organization_name || undefined,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary">LegalLens</h1>
          <p className="text-muted-foreground mt-2">India</p>
        </div>

        <div className="bg-background border rounded-lg p-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-center mb-6">
            Create your account
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  className="w-full pl-9 pr-4 py-2 border rounded-md"
                  placeholder="John Doe"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="w-full pl-9 pr-4 py-2 border rounded-md"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Organization Name (Optional)
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  value={formData.organization_name}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      organization_name: e.target.value,
                    })
                  }
                  className="w-full pl-9 pr-4 py-2 border rounded-md"
                  placeholder="Acme Inc."
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className="w-full pl-9 pr-4 py-2 border rounded-md"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="password"
                  value={formData.confirm_password}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      confirm_password: e.target.value,
                    })
                  }
                  className="w-full pl-9 pr-4 py-2 border rounded-md"
                  placeholder="••••••••"
                  required
                  minLength={8}
                />
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={registerMutation.isPending}
              className="w-full py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {registerMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link to="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
