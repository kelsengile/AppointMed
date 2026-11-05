import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import LandingPage from "./LandingPage";

const REMEMBER_KEY = "appointmed.remembered-username";

export default function StaffLoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [showRecoveryHint, setShowRecoveryHint] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const backdropRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (backdropRef.current) (backdropRef.current as HTMLDivElement & { inert: boolean }).inert = true;
  }, []);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(REMEMBER_KEY);
      if (saved) setUsername(saved);
    } catch {
      /* storage unavailable */
    }
  }, []);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Enter your username and password.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const role = await login(username, password);
      try {
        if (remember) localStorage.setItem(REMEMBER_KEY, username.trim());
        else localStorage.removeItem(REMEMBER_KEY);
      } catch {
        /* storage unavailable */
      }
      navigate(`/${role}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log in.");
      setBusy(false);
    }
  }

  const label = "block text-[#053067] text-sm font-medium sm:text-base";

  return (
    <div
      className="relative min-h-screen bg-[#05294a] flex items-center justify-center p-4 sm:p-6"
      style={{ fontFamily: "Poppins, system-ui, -apple-system, sans-serif" }}
    >
      {/* Backdrop */}
      <div ref={backdropRef} aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 select-none overflow-hidden">
        <div className="absolute inset-0 scale-105 blur-[7px] brightness-[0.72] saturate-[0.9]">
          <LandingPage />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-[#05294a]/60 via-[#06386b]/35 to-[#04223c]/70" />
      </div>

      {/* Main Container - Outer rounded corners & shadow */}
      <div className="relative z-10 flex w-full max-w-[920px] flex-col lg:flex-row lg:items-stretch shadow-2xl rounded-2xl overflow-hidden">
        
        {/* Left Panel - lg:rounded-r-none flattens the right-side corners */}
        <div
          aria-hidden
          className="glass-panel glass-panel--left relative z-10 order-first flex min-h-[200px] w-full items-center justify-center overflow-hidden py-8 sm:min-h-[240px] lg:order-none lg:mb-0 lg:w-[320px] lg:flex-none lg:self-stretch lg:py-0 lg:rounded-r-none"
        >
          <img
            src="/staff-login-bg.jpg"
            alt=""
            className="pointer-events-none absolute max-w-none select-none"
            style={{ width: "410%", height: "118.9%", left: "-44.4%", top: "-11.5%" }}
          />
          <img
            src="/staff-login-logo.png"
            alt=""
            className="relative w-32 drop-shadow-xl sm:w-40 lg:w-44"
          />
        </div>

        {/* Right Panel - lg:rounded-l-none flattens the left-side corners */}
        <form onSubmit={submit} className="glass-panel glass-panel--form flex-1 px-8 py-10 sm:px-10 sm:py-10 lg:px-12 lg:py-12 lg:rounded-l-none">
          <h1 className="text-3xl font-bold leading-tight tracking-tight text-[#053067] sm:text-4xl">
            STAFF LOGIN
          </h1>
          <p className="mt-1.5 text-xs text-[#94A3B8] sm:text-sm">
            For doctors, nurses, and administrators
          </p>

          <label className={`mt-6 ${label}`} htmlFor="staff-username">
            Username
            <input
              id="staff-username"
              name="username"
              type="text"
              required
              autoFocus
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              aria-invalid={error ? true : undefined}
              className="glass-input mt-1.5 block h-11 w-full px-4 text-base sm:h-12 sm:text-lg"
            />
          </label>

          <label className={`mt-4 ${label}`} htmlFor="staff-password">
            Password
            <div className="relative mt-1.5">
              <input
                id="staff-password"
                name="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={error ? true : undefined}
                className="glass-input block h-11 w-full px-4 pr-20 text-base sm:h-12 sm:text-lg"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-pressed={showPassword}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-3 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-xs font-medium text-[#053067] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067]"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
          </label>

          {error && (
            <p className="mt-3 text-xs text-red-700 sm:text-sm" role="alert">
              {error}
            </p>
          )}

          <div className="mt-5 flex items-center justify-between gap-4">
            <label className="flex cursor-pointer select-none items-center gap-2 text-xs text-[#053067] sm:text-sm">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              <span
                aria-hidden
                className="grid h-4 w-4 place-items-center rounded-[4px] border border-[#053067] bg-[#053067] transition peer-focus-visible:ring-2 peer-focus-visible:ring-[#053067]"
              >
                {remember && (
                  <svg viewBox="0 0 17 16" className="h-[60%] w-[60%]" fill="none" stroke="#FCFDF7" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1.8 8.4l4.5 4.6L15.3 1.9" />
                  </svg>
                )}
              </span>
              Remember me
            </label>

            <button
              type="button"
              onClick={() => setShowRecoveryHint((v) => !v)}
              aria-expanded={showRecoveryHint}
              className="rounded text-xs text-[#053067] underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] sm:text-sm"
            >
              Forgot Password?
            </button>
          </div>
          {showRecoveryHint && (
            <p className="mt-1 text-right text-[11px] text-[#053067]/80 sm:text-xs" role="status">
              Passwords are reset by an administrator. Ask one to reset yours.
            </p>
          )}

          <div className="mt-7 flex items-center justify-end gap-5">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="rounded text-sm font-light text-[#6E6E6E] transition hover:text-[#053067] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] sm:text-base"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy}
              className="glass-login-button h-11 min-w-[7rem] px-5 text-sm font-medium focus:outline-none focus-visible:ring-4 focus-visible:ring-[#053067]/40 sm:h-12 sm:min-w-[9rem] sm:text-base"
            >
              {busy ? "Logging in…" : "Log in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}