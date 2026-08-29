import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Lock, Loader2, AlertTriangle } from "lucide-react";
import { usersApi } from "../lib/users";

export function AccountSettings() {
  const [passwords, setPasswords] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [error, setError] = useState<string | null>(null);

  const changePasswordMutation = useMutation({
    mutationFn: usersApi.changePassword,
    onSuccess: () => {
      setPasswords({
        current_password: "",
        new_password: "",
        confirm_password: "",
      });
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message || "Failed to change password");
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: usersApi.deleteAccount,
    onSuccess: () => {
      localStorage.clear();
      window.location.href = "/login";
    },
  });

  const handleChangePassword = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (passwords.new_password !== passwords.confirm_password) {
      setError("Passwords do not match");
      return;
    }

    if (passwords.new_password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    changePasswordMutation.mutate({
      current_password: passwords.current_password,
      new_password: passwords.new_password,
    });
  };

  const handleDeleteAccount = () => {
    if (
      confirm(
        "Are you sure you want to delete your account? This action cannot be undone."
      )
    ) {
      if (
        confirm(
          "All your data will be permanently deleted. Type DELETE to confirm."
        )
      ) {
        deleteAccountMutation.mutate();
      }
    }
  };

  return (
    <div className="space-y-6">
      <div className="border rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <Lock className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Change Password</h3>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">
              Current Password
            </label>
            <input
              type="password"
              value={passwords.current_password}
              onChange={(e) =>
                setPasswords({ ...passwords, current_password: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              New Password
            </label>
            <input
              type="password"
              value={passwords.new_password}
              onChange={(e) =>
                setPasswords({ ...passwords, new_password: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md"
              required
              minLength={8}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Confirm New Password
            </label>
            <input
              type="password"
              value={passwords.confirm_password}
              onChange={(e) =>
                setPasswords({ ...passwords, confirm_password: e.target.value })
              }
              className="w-full px-3 py-2 border rounded-md"
              required
              minLength={8}
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={changePasswordMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            {changePasswordMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Lock className="h-4 w-4" />
            )}
            Change Password
          </button>
        </form>
      </div>

      <div className="border border-red-200 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h3 className="text-lg font-semibold text-red-800">Danger Zone</h3>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Once you delete your account, there is no going back. Please be
          certain.
        </p>

        <button
          onClick={handleDeleteAccount}
          disabled={deleteAccountMutation.isPending}
          className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 disabled:opacity-50"
        >
          {deleteAccountMutation.isPending ? "Deleting..." : "Delete Account"}
        </button>
      </div>
    </div>
  );
}
