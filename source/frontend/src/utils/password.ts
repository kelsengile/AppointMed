// Password rules for new passwords. Mirrors _check_password_strength in backend/schemas/api.py.
// The backend is the authority; this only gives fast feedback.
export const PASSWORD_MAX = 72; // bcrypt's limit, counted in bytes

export interface PasswordRule {
  key: string;
  label: string;
  test: (password: string) => boolean;
}

export const PASSWORD_RULES: PasswordRule[] = [
  { key: "length", label: "At least 8 characters", test: (p) => p.length >= 8 },
  { key: "upper", label: "An uppercase letter (A-Z)", test: (p) => /[A-Z]/.test(p) },
  { key: "lower", label: "A lowercase letter (a-z)", test: (p) => /[a-z]/.test(p) },
  { key: "number", label: "A number (0-9)", test: (p) => /[0-9]/.test(p) },
  { key: "special", label: "A special character, such as ! ? @ * #", test: (p) => /[^A-Za-z0-9\s]/.test(p) },
];

/** Returns a message describing the first problem, or "" when the password is acceptable. */
export function passwordProblem(password: string): string {
  if (new TextEncoder().encode(password).length > PASSWORD_MAX) {
    return `The password is too long (${PASSWORD_MAX} bytes at most; accented or non-Latin characters count as more than one).`;
  }
  const failed = PASSWORD_RULES.filter((rule) => !rule.test(password));
  if (failed.length === 0) return "";
  return `The password needs: ${failed.map((rule) => rule.label.toLowerCase()).join("; ")}.`;
}