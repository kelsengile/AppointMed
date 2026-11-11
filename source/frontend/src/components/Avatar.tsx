// Profile picture: the user's own photo, or else their character from "Meet Our Staff".
import { useStaffArt } from "../hooks/useStaffArt";

export default function Avatar({ avatar, name, className = "h-10 w-10" }: { avatar?: string | null; name: string; className?: string }) {
  const art = useStaffArt(name);
  const base = `relative shrink-0 overflow-hidden rounded-full ${className}`;
  if (avatar) return <img src={avatar} alt="" className={`${base} object-cover`} />;
  return (
    <span className={`${base} bg-brand-100`} aria-hidden="true">
      {art && (
        <>
          <img src={art.bg} alt="" className="absolute inset-0 h-full w-full object-cover" />
          <img src={art.figure} alt="" className="absolute left-1/2 top-0 h-[150%] max-w-none -translate-x-1/2 object-contain" />
        </>
      )}
    </span>
  );
}