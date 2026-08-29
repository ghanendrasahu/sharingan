import { useQuery } from "@tanstack/react-query";
import { Bell, User, LogOut, ChevronDown } from "lucide-react";
import { useState } from "react";
import { usersApi } from "../lib/users";

export function Header() {
  const [showDropdown, setShowDropdown] = useState(false);

  const { data: user } = useQuery({
    queryKey: ["user"],
    queryFn: () => usersApi.getProfile(),
  });

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
  };

  return (
    <header className="h-16 border-b bg-background flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold">Dashboard</h2>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 hover:bg-muted rounded-md">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>

        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            className="flex items-center gap-2 px-3 py-2 hover:bg-muted rounded-md"
          >
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <User className="h-4 w-4 text-primary" />
            </div>
            <span className="text-sm font-medium">
              {user?.full_name || "User"}
            </span>
            <ChevronDown className="h-4 w-4" />
          </button>

          {showDropdown && (
            <div className="absolute right-0 top-full mt-2 w-48 bg-background border rounded-lg shadow-lg z-50">
              <div className="p-2">
                <p className="px-2 py-1 text-sm font-medium">{user?.full_name}</p>
                <p className="px-2 py-1 text-xs text-muted-foreground">
                  {user?.email}
                </p>
              </div>
              <div className="border-t p-2">
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-2 py-1.5 text-sm text-red-600 hover:bg-muted rounded"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
