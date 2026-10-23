import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { NAV } from "./config/Navigation";
import { AuthProvider } from "./context/AuthContext";
import DashboardLayout from "./layouts/DashboardLayout";
import BookingPage from "./pages/BookingPage";
import LandingPage from "./pages/LandingPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import { ROLES } from "./types";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/book" element={<BookingPage />} />
          {ROLES.map((role) => (
            <Route
              key={role}
              path={`/${role}`}
              element={
                <ProtectedRoute role={role}>
                  <DashboardLayout role={role} />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to={NAV[role][0].path} replace />} />
              {NAV[role].map((item) => (
                <Route key={item.path} path={item.path} element={<PlaceholderPage item={item} />} />
              ))}
            </Route>
          ))}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}