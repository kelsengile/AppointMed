import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import AdminPage from "./pages/AdminPage";
import DoctorPage from "./pages/DoctorPage";
import LoginPage from "./pages/LoginPage";
import NursePage from "./pages/NursePage";

// HashRouter so routes also work when Electron loads the packaged index.html from disk.
export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/doctor" element={<ProtectedRoute role="doctor"><DoctorPage /></ProtectedRoute>} />
          <Route path="/nurse" element={<ProtectedRoute role="nurse"><NursePage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute role="admin"><AdminPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </HashRouter>
  );
}