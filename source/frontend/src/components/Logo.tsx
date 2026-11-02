// The AppointMed logo with optional name. Used in the side panel, landing page, login, and booking page.
// The image is served from frontend/public/appointmed-logo.png.
interface LogoProps {
  size?: number; // image height in pixels
  showName?: boolean; // show the "AppointMed" text next to the image
  onDark?: boolean; // true on dark backgrounds: the name turns white
}

export default function Logo({ size = 36, showName = true, onDark = false }: LogoProps) {
  return (
    <span className="inline-flex items-center gap-2">
      <img src="/appointmed-logo.png" alt={showName ? "" : "AppointMed"} style={{ height: size, width: "auto" }} />
      {showName && (
        <span className={`text-lg font-semibold ${onDark ? "text-white" : "text-brand-700"}`}>AppointMed</span>
      )}
    </span>
  );
}