import { Routes, Route } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "./components/AppLayout";
import { ProtectedRoute, PublicRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { AnalysisPage } from "./pages/AnalysisPage";
import { SearchPage } from "./pages/SearchPage";
import { PaymentPage } from "./pages/PaymentPage";
import { SettingsPage } from "./pages/SettingsPage";
import { documentsApi } from "./lib/documents";
import { analysisApi } from "./lib/analysis";
import { paymentsApi } from "./lib/payments";

function Dashboard() {
  const { data: documents } = useQuery({
    queryKey: ["documents", 1],
    queryFn: () => documentsApi.list(1, 1),
  });
  const { data: analyses } = useQuery({
    queryKey: ["analyses"],
    queryFn: () => analysisApi.listAnalyses(undefined, 1, 100),
  });
  const { data: subscription } = useQuery({
    queryKey: ["subscription"],
    queryFn: () => paymentsApi.getSubscription(),
  });

  const documentCount = documents?.total ?? 0;
  const analysisCount = analyses?.total ?? 0;
  const riskCount =
    analyses?.analyses.reduce((sum, item) => sum + (item.risks?.length ?? 0), 0) ??
    0;
  const credits = subscription?.credits_remaining ?? 0;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Welcome to LegalLens India</h1>
        <p className="text-muted-foreground mt-2">
          AI-powered legal document analysis for Indian startups
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Documents"
          value={String(documentCount)}
          description="Uploaded documents"
        />
        <StatCard
          title="Analyses"
          value={String(analysisCount)}
          description="Completed analyses"
        />
        <StatCard
          title="Risks Found"
          value={String(riskCount)}
          description="Total risks identified"
        />
        <StatCard
          title="Credits"
          value={String(credits)}
          description="Credits remaining"
        />
      </div>

      <div className="mt-8 border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2 text-muted-foreground">
          <li>Upload your first legal document</li>
          <li>Run an AI-powered analysis</li>
          <li>Review risks and key terms</li>
          <li>Generate comprehensive reports</li>
        </ol>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  description,
}: {
  title: string;
  value: string;
  description: string;
}) {
  return (
    <div className="border rounded-lg p-4">
      <p className="text-sm text-muted-foreground">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  );
}

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/subscription" element={<PaymentPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}

export default App;
