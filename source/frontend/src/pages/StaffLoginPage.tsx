// Staff login, rebuilt 1:1 from the Figma design "Desktop - 9":
// https://www.figma.com/design/LtKOvs4BqcEhbH3vDw6SKr/Untitled?node-id=33-40
// Two overlapping frosted-glass panels: the AppointMed logo over a blurred photo (left),
// and the sign-in form (right). One deviation from the design: the first field asks for the
// username, not an email address, because the backend authenticates staff by username only.
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
  // The backdrop re-renders the front page; keep it out of the tab order (aria-hidden + inert).
  const backdropRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (backdropRef.current) (backdropRef.current as HTMLDivElement & { inert: boolean }).inert = true;
  }, []);

  // Prefill the username saved on a previous visit when "Remember me" was ticked.
  useEffect(() => {
    try {
      const saved = localStorage.getItem(REMEMBER_KEY);
      if (saved) setUsername(saved);
    } catch {
      /* storage unavailable: start blank */
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
        /* storage unavailable: nothing to remember */
      }
      navigate(`/${role}`, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log in.");
      setBusy(false);
    }
  }

  const label = "block text-[#053067] text-base font-normal sm:text-lg xl:text-2xl";

  return (
    <div
      className="relative min-h-screen bg-[#05294a]"
      style={{ fontFamily: "Poppins, system-ui, -apple-system, sans-serif" }}
    >
      {/* Backdrop: the website's front page, blurred and dimmed so the glass panels read. Fixed so it always covers the viewport while the content can scroll on small screens. */}
      <div ref={backdropRef} aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 select-none overflow-hidden">
        <div className="absolute inset-0 scale-105 blur-[7px] brightness-[0.72] saturate-[0.9]">
          <LandingPage />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-[#05294a]/60 via-[#06386b]/35 to-[#04223c]/70" />
      </div>

      <div className="relative z-10 flex min-h-screen items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="flex w-full max-w-[1490px] flex-col lg:flex-row lg:items-stretch">
        {/* Left panel: blurred photo and logo, overlapping the form panel. */}
        <div
          aria-hidden
          className="glass-panel glass-panel--left relative z-10 order-first -mb-7 flex min-h-[240px] w-full items-center justify-center overflow-hidden py-10 sm:min-h-[300px] sm:py-12 lg:order-none lg:-mr-8 lg:mb-0 lg:min-h-0 lg:w-[492px] lg:flex-none lg:self-stretch lg:py-0"
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
            className="relative w-40 drop-shadow-xl sm:w-48 lg:w-60 xl:w-72 2xl:w-80"
          />
        </div>

        {/* Right panel: the sign-in form. */}
        <form onSubmit={submit} className="glass-panel glass-panel--form flex-1 px-6 pb-8 pt-16 sm:px-12 sm:pt-20 lg:min-h-[min(88vh,960px)] lg:px-14 lg:pt-20 xl:px-28 xl:pt-24 2xl:px-[135px]"
>
          <h1 className="text-5xl font-bold leading-tight tracking-tight text-[#053067] md:text-6xl xl:text-7xl 2xl:text-8xl 2xl:leading-[144px]">
            STAFF LOGIN
          </h1>
          <p className="mt-2 text-base text-[#94A3B8] md:text-lg xl:text-2xl 2xl:mt-4 2xl:text-[32px] 2xl:leading-[48px]">
            For doctors, nurses, and administrators
          </p>

          <label className={`mt-8 sm:mt-10 xl:mt-14 ${label}`} htmlFor="staff-username">
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
              className="glass-input mt-2 block h-14 w-full px-5 text-lg sm:h-16 sm:text-xl xl:mt-3 xl:h-20 xl:text-2xl 2xl:h-[108px]"
            />
          </label>

          <label className={`mt-5 sm:mt-6 xl:mt-8 ${label}`} htmlFor="staff-password">
            Password
            <div className="relative mt-2 xl:mt-3">
              <input
                id="staff-password"
                name="password"
                type={showPassword ? "text" : "password"}
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={error ? true : undefined}
                className="glass-input block h-14 w-full px-5 pr-24 text-lg sm:h-16 sm:text-xl xl:h-20 xl:text-2xl 2xl:h-[108px]"
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                aria-pressed={showPassword}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute right-4 top-1/2 -translate-y-1/2 rounded px-2 py-1 text-sm font-medium text-[#053067] hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] sm:text-base"
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

          <div className="mt-5 flex items-center justify-between gap-4 sm:mt-6 xl:mt-8">
            <label className="flex cursor-pointer select-none items-center gap-2 text-sm text-[#053067] sm:gap-3 sm:text-base xl:text-[22px]">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              <span
                aria-hidden
                className="grid h-5 w-5 place-items-center rounded-[4px] border border-[#053067] bg-[#053067] transition peer-focus-visible:ring-2 peer-focus-visible:ring-[#053067] peer-focus-visible:ring-offset-2 peer-checked:bg-[#053067] sm:h-6 sm:w-6 xl:h-[25px] xl:w-[25px] xl:rounded-[3px]"
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
              className="rounded text-sm text-[#053067] underline-offset-2 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] sm:text-base xl:text-[22px]"
            >
              Forgot Password?
            </button>
          </div>
          {showRecoveryHint && (
            <p className="mt-2 text-right text-xs text-[#053067]/80 sm:text-sm" role="status">
              Passwords are reset by an administrator. Ask one to reset yours.
            </p>
          )}

          <div className="mt-8 flex items-center justify-end gap-6 sm:mt-10 sm:gap-10 lg:mt-12 xl:mt-16 xl:gap-16 2xl:mt-20">
            <button
              type="button"
              onClick={() => navigate("/")}
              className="rounded text-lg font-light text-[#6E6E6E] transition hover:text-[#053067] focus:outline-none focus-visible:ring-2 focus-visible:ring-[#053067] sm:text-xl xl:text-3xl 2xl:text-4xl"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={busy}
              className="glass-login-button h-14 min-w-[9rem] px-8 text-lg focus:outline-none focus-visible:ring-4 focus-visible:ring-[#053067]/40 sm:h-16 sm:min-w-[11rem] sm:text-xl xl:h-20 xl:min-w-[14rem] xl:text-2xl 2xl:h-[88px] 2xl:min-w-[16rem] 2xl:text-4xl"
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
