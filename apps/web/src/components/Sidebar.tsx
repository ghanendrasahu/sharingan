import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Search,
  BarChart3,
  CreditCard,
  Settings,
  HelpCircle,
} from "lucide-react";

const navItems = [
  {
    to: "/",
    icon: LayoutDashboard,
    label: "Dashboard",
  },
  {
    to: "/documents",
    icon: FileText,
    label: "Documents",
  },
  {
    to: "/analysis",
    icon: BarChart3,
    label: "Analysis",
  },
  {
    to: "/search",
    icon: Search,
    label: "Search & Reports",
  },
  {
    to: "/subscription",
    icon: CreditCard,
    label: "Subscription",
  },
  {
    to: "/settings",
    icon: Settings,
    label: "Settings",
  },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-muted/30 min-h-screen p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-primary">LegalLens</h1>
        <p className="text-xs text-muted-foreground">India</p>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`
            }
          >
            <item.icon className="h-4 w-4" />
            <span className="text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="absolute bottom-4 left-4 right-4">
        <NavLink
          to="/help"
          className="flex items-center gap-3 px-3 py-2 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <HelpCircle className="h-4 w-4" />
          <span className="text-sm">Help & Support</span>
        </NavLink>
      </div>
    </aside>
  );
}
