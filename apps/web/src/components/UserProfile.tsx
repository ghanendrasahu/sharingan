import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { User, Mail, Calendar, Loader2, Save } from "lucide-react";
import { usersApi } from "../lib/users";

export function UserProfile() {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
  });

  const { data: user, isLoading } = useQuery({
    queryKey: ["user"],
    queryFn: () => usersApi.getProfile(),
  });

  const updateMutation = useMutation({
    mutationFn: usersApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user"] });
      setIsEditing(false);
    },
  });

  const handleEdit = () => {
    if (user) {
      setFormData({
        full_name: user.full_name,
        email: user.email,
      });
      setIsEditing(true);
    }
  };

  const handleSave = () => {
    updateMutation.mutate(formData);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="text-center py-8 border rounded-lg">
        <p className="text-muted-foreground">Failed to load profile</p>
      </div>
    );
  }

  return (
    <div className="border rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Profile Information</h3>
        {!isEditing && (
          <button
            onClick={handleEdit}
            className="px-4 py-2 border rounded-md hover:bg-muted"
          >
            Edit Profile
          </button>
        )}
      </div>

      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <User className="h-6 w-6 text-primary" />
          </div>
          <div>
            {isEditing ? (
              <input
                type="text"
                value={formData.full_name}
                onChange={(e) =>
                  setFormData({ ...formData, full_name: e.target.value })
                }
                className="px-3 py-1 border rounded-md"
              />
            ) : (
              <p className="font-medium">{user.full_name}</p>
            )}
            <p className="text-sm text-muted-foreground">{user.email}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div className="flex items-center gap-2">
            <Mail className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Email</p>
              {isEditing ? (
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="px-3 py-1 border rounded-md w-full"
                />
              ) : (
                <p className="text-sm">{user.email}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <div>
              <p className="text-sm text-muted-foreground">Joined</p>
              <p className="text-sm">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        {isEditing && (
          <div className="flex items-center gap-2 pt-4">
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
            >
              {updateMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save Changes
            </button>
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 border rounded-md hover:bg-muted"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
