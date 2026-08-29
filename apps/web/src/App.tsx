import { Routes, Route } from "react-router-dom";

function App() {
  return (
    <div className="min-h-screen bg-background">
      <Routes>
        <Route
          path="/"
          element={
            <div className="flex items-center justify-center min-h-screen">
              <div className="text-center">
                <h1 className="text-4xl font-bold tracking-tight">LegalLens India</h1>
                <p className="mt-2 text-muted-foreground">
                  AI-powered legal document analysis for Indian startups
                </p>
                <p className="mt-4 text-sm text-muted-foreground">
                  Coming soon
                </p>
              </div>
            </div>
          }
        />
      </Routes>
    </div>
  );
}

export default App;
