import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { NAV } from "./config/Navigation";
import { AuthProvider } from "./context/AuthContext";
import DashboardLayout from "./layouts/DashboardLayout";
import BookingPage from "./pages/BookingPage";
import LandingPage from "./pages/LandingPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage";
import AuditPage from "./pages/admin/AuditPage";
import ClinicSettingsPage from "./pages/admin/ClinicSettingsPage";
import ReportsPage from "./pages/admin/ReportsPage";
import RoomsPage from "./pages/admin/RoomsPage";
import UsersPage from "./pages/admin/UsersPage";
import HelpPage from "./pages/shared/HelpPage";
import ProfilePage from "./pages/shared/ProfilePage";
import SettingsPage from "./pages/shared/SettingsPage";
import AppointmentsPage from "./pages/staff/AppointmentsPage";
import DashboardPage from "./pages/staff/DashboardPage";
import HistoryPage from "./pages/staff/HistoryPage";
import InvoicePage from "./pages/staff/InvoicePage";
import NotificationsPage from "./pages/staff/NotificationsPage";
import PatientsPage from "./pages/staff/PatientsPage";
import PrescriptionsPage from "./pages/staff/PrescriptionsPage";
import { ROLES, type NavItem, type Role } from "./types";

// Maps a navigation item (see config/Navigation.ts) to the page that fills it.
function pageFor(role: Role, item: NavItem) {
  // Pages every role has.
  switch (item.path) {
    case "dashboard":
      return role === "admin" ? <AdminDashboardPage /> : <DashboardPage />;
    case "profile":
      return <ProfilePage />;
    case "settings":
      return <SettingsPage />;
    case "help":
      return <HelpPage />;
  }
  if (role === "admin") {
    switch (item.path) {
      case "users":
        return <UsersPage />;
      case "rooms":
        return <RoomsPage />;
      case "clinic":
        return <ClinicSettingsPage />;
      case "reports":
        return <ReportsPage />;
      case "audits":
        return <AuditPage />;
    }
  } else {
    // Doctors and nurses share the clinical pages.
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
      case "prescriptions":
        return <PrescriptionsPage />;
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