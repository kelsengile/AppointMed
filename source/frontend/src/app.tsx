import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { NAV } from "./config/Navigation";
import { AuthProvider } from "./context/AuthContext";
import DashboardLayout from "./layouts/DashboardLayout";
import BookingPage from "./pages/BookingPage";
import LandingPage from "./pages/LandingPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import AppointmentsPage from "./pages/staff/AppointmentsPage";
import HistoryPage from "./pages/staff/HistoryPage";
import InvoicePage from "./pages/staff/InvoicePage";
import NotificationsPage from "./pages/staff/NotificationsPage";
import PatientsPage from "./pages/staff/PatientsPage";
import { ROLES, type NavItem, type Role } from "./types";

// Doctors and nurses share the clinical pages. Every other page is still a placeholder.
function pageFor(role: Role, item: NavItem) {
  if (role !== "admin") {
    switch (item.path) {
      case "appointments":
        return <AppointmentsPage />;
      case "notifications":
        return <NotificationsPage />;
      case "patients":
        return <PatientsPage />;
      case "history":
        return <HistoryPage />;
      case "invoice":
        return <InvoicePage />;
    }
  }
  return <PlaceholderPage item={item} />;
}

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
                <Route key={item.path} path={item.path} element={pageFor(role, item)} />
              ))}
            </Route>
          ))}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}