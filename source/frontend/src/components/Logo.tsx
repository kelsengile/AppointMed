// The AppointMed logo with optional name. Used in the side panel and the booking page.
// Uses the logo the admin uploaded in Settings, or else frontend/public/logo-mark.png.
import { useSite } from "../hooks/useSite";
import { DEFAULT_LOGO } from "../config/branding";

interface LogoProps {
  size?: number; // image height in pixels
  showName?: boolean; // show the "AppointMed" text next to the image
  onDark?: boolean; // true on dark backgrounds: the name turns white
}

export default function Logo({ size = 36, showName = true, onDark = false }: LogoProps) {
  const { logoSrc } = useSite();
  return (
    <span className="inline-flex items-center gap-2">
      <img src={logoSrc ?? DEFAULT_LOGO} alt={showName ? "" : "AppointMed"} className="rounded-lg" style={{ height: size, width: "auto" }} />
      {showName && (
        <span className={`text-lg font-semibold ${onDark ? "text-white" : "text-brand-700"}`}>AppointMed</span>
      )}
    </span>
  );
}