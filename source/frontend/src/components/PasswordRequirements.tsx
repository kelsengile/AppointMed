// Live checklist shown under a new-password field. Each rule turns green once it is met.
import { PASSWORD_RULES } from "../utils/password";

export default function PasswordRequirements({ password }: { password: string }) {
  return (
    <ul className="mt-2 space-y-0.5 text-xs" aria-label="Password requirements">
      {PASSWORD_RULES.map((rule) => {
        const ok = rule.test(password);
        return (
          <li key={rule.key} className={ok ? "text-emerald-700" : "text-slate-500"}>
            <span aria-hidden="true">{ok ? "✓" : "○"}</span> {rule.label}
            <span className="sr-only">{ok ? " (met)" : " (not met)"}</span>
          </li>
        );
      })}
    </ul>
  );
}