// Staff login, built from the Figma design "Desktop - 9":
// https://www.figma.com/design/LtKOvs4BqcEhbH3vDw6SKr/Untitled?node-id=33-40
// Two overlapping frosted-glass panels: the AppointMed logo over a blurred photo (left),
// and the sign-in form (right). One deviation from the design: the first field asks for the
// username, not an email address, because the backend authenticates staff by username only.
//
// Sizing: the card is capped at a fixed width and a height that follows the window (about 80% of it),
// and the type and controls use one modest scale. The earlier version kept growing at the 2xl breakpoint
// (1536px and wider), which made everything oversized at 100% zoom on a 1080p screen and caused a scrollbar.
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

  // One scale for every size: base on phones, a little larger from the xl breakpoint (1280px) up. Nothing grows beyond that.
  const label = "block text-base font-normal text-[#053067] xl:text-lg";
  const field = "glass-input block h-12 w-full px-5 text-base sm:h-14 xl:text-lg";

  return (
    <div className="relative min-h-screen bg-[#05294a]" style={{ fontFamily: "Poppins, system-ui, -apple-system, sans-serif" }}>
      {/* Backdrop: the website's front page, blurred and dimmed so the glass panels read. Fixed so it always covers the viewport while the content can scroll on small screens. */}
      <div ref={backdropRef} aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 select-none overflow-hidden">
        <div className="absolute inset-0 scale-105 blur-[7px] brightness-[0.72] saturate-[0.9]">
          <LandingPage />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-[#05294a]/60 via-[#06386b]/35 to-[#04223c]/70" />
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-center p-4 sm:p-6 lg:p-8">
        {/* The card never gets wider than 1100px, however large the window is. */}
        <div className="flex w-full max-w-[1100px] flex-col lg:flex-row lg:items-stretch">
          {/* Left panel: blurred photo and logo, overlapping the form panel. */}
          <div
            aria-hidden
            className="glass-panel glass-panel--left relative z-10 order-first -mb-7 flex min-h-[180px] w-full items-center justify-center overflow-hidden py-8 sm:min-h-[220px] lg:order-none lg:-mr-8 lg:mb-0 lg:min-h-0 lg:w-[340px] lg:flex-none lg:self-stretch lg:py-0 xl:w-[380px]"
          >
            <img
              src="/staff-login-bg.jpg"
              alt=""
              className="pointer-events-none absolute max-w-none select-none"
              style={{ width: "410%", height: "118.9%", left: "-44.4%", top: "-11.5%" }}
            />
            <img src="/staff-login-logo.png" alt="" className="relative w-32 drop-shadow-xl sm:w-40 lg:w-44 xl:w-52" />
          </div>

          {/* Right panel: the sign-in form, centred vertically inside a card that is about 80% of the window height. */}
          <form
            onSubmit={submit}
            className="glass-panel glass-panel--form flex flex-1 flex-col justify-center px-6 pb-8 pt-10 sm:px-10 lg:min-h-[min(80vh,700px)] lg:py-10 lg:pl-16 lg:pr-12 xl:pl-20 xl:pr-16"
          >
            <h1 className="text-4xl font-bold leading-tight tracking-tight text-[#053067] sm:text-5xl xl:text-6xl">STAFF LOGIN</h1>
            <p className="mt-1 text-base text-[#94A3B8] xl:mt-2 xl:text-xl">For doctors, nurses, and administrators</p>

            <label className={`mt-8 xl:mt-10 ${label}`} htmlFor="staff-username">
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
                className={`${field} mt-2`}
              />
            </label>

            <label className={`mt-5 xl:mt-6 ${label}`} htmlFor="staff-password">
              Password
              <div className="relative mt-2">
                <input
                  id="staff-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  aria-invalid={error ? true : undefined}
                  className={`${field} pr-20`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-pressed={showPassword}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-4 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-sm font-medium text-[#053067] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067]"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>

            {error && (
              <p className="mt-4 text-sm text-red-700 sm:text-base" role="alert">
                {error}
              </p>
            )}

            <div className="mt-5 flex items-center justify-between gap-4 xl:mt-6">
              <label className="flex cursor-pointer select-none items-center gap-2 text-sm text-[#053067] sm:text-base">
                <input type="checkbox" className="peer sr-only" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                <span
                  aria-hidden
                  className="grid h-5 w-5 place-items-center rounded-[4px] border border-[#053067] bg-[#053067] transition peer-focus-visible:ring-2 peer-focus-visible:ring-[#053067] peer-focus-visible:ring-offset-2"
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
                className="rounded text-sm text-[#053067] underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] sm:text-base"
              >
                Forgot Password?
              </button>
            </div>
            {showRecoveryHint && (
              <p className="mt-2 text-right text-xs text-[#053067]/80 sm:text-sm" role="status">
                Passwords are reset by an administrator. Ask one to reset yours.
              </p>
            )}

            <div className="mt-8 flex items-center justify-end gap-6 xl:mt-10 xl:gap-8">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="rounded text-lg font-light text-[#6E6E6E] transition hover:text-[#053067] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] xl:text-xl"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={busy}
                className="glass-login-button h-12 min-w-[8rem] px-8 text-lg focus:outline-none focus-visible:ring-4 focus-visible:ring-[#053067]/40 sm:h-14 sm:min-w-[9.5rem] xl:text-xl"
              >
                {busy ? "Logging in…" : "Log in"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
} 
