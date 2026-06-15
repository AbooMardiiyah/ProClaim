import { Suspense, lazy } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "react-hot-toast";
import Layout from "./components/Layout";
import { getAccessToken } from "./lib/api";

const LoginPage = lazy(() => import("./pages/LoginPage"));
const LandingPage = lazy(() => import("./pages/LandingPage"));
const DashboardPage = lazy(() => import("./pages/DashboardPage"));
const UploadPage = lazy(() => import("./pages/UploadPage"));
const ClaimsListPage = lazy(() => import("./pages/ClaimsListPage"));
const ReviewPage = lazy(() => import("./pages/ReviewPage"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

function RequireAuth({ children }: { children: React.ReactNode }) {
  if (!getAccessToken()) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Suspense
          fallback={
            <div className="flex items-center justify-center h-screen text-slate-400 text-sm">
              Loading…
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="upload" element={<UploadPage />} />
              <Route path="claims" element={<ClaimsListPage />} />
              <Route path="claims/:id" element={<ReviewPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3000,
          style: { fontSize: "0.875rem" },
          success: { iconTheme: { primary: "#028090", secondary: "#fff" } },
        }}
      />

      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
