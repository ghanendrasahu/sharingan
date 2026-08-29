import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { User, Shield } from "lucide-react";
import { UserProfile } from "../components/UserProfile";
import { AccountSettings } from "../components/AccountSettings";

const queryClient = new QueryClient();

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"profile" | "security">("profile");

  return (
    <QueryClientProvider client={queryClient}>
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your account settings and preferences.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1">
            <nav className="space-y-1">
              <NavItem
                active={activeTab === "profile"}
                onClick={() => setActiveTab("profile")}
                icon={<User className="h-4 w-4" />}
                label="Profile"
              />
              <NavItem
                active={activeTab === "security"}
                onClick={() => setActiveTab("security")}
                icon={<Shield className="h-4 w-4" />}
                label="Security"
              />
            </nav>
          </div>

          <div className="lg:col-span-3">
            {activeTab === "profile" && <UserProfile />}
            {activeTab === "security" && <AccountSettings />}
          </div>
        </div>
      </div>
    </QueryClientProvider>
  );
}

function NavItem({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 w-full px-3 py-2 rounded-md transition-colors ${
        active
          ? "bg-primary text-primary-foreground"
          : "hover:bg-muted text-muted-foreground hover:text-foreground"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}
