// The signed-in user's profile: view details, change name and email, and upload or remove a picture.
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { authApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import { inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import type { Role } from "../../types";
import { formatDateTime } from "../../utils/format";
import { resizeImage } from "../../utils/image";

const ROLE_LABEL: Record<Role, string> = { doctor: "Doctor", nurse: "Nurse", admin: "Administrator" };
const EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function ProfilePage() {
  const { updateSession } = useAuth();
  const { data: profile, error, loading, reload } = usePolling(() => authApi.me(), 0);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [formError, setFormError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  // Fill the form when the profile loads.
  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name);
      setEmail(profile.email ?? "");
    }
  }, [profile]);

  async function save(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    setMessage("");
    if (fullName.trim().length < 2) return setFormError("Enter your full name.");
    if (email.trim() && !EMAIL.test(email.trim())) return setFormError("Enter a valid email address.");
    setBusy(true);
    try {
      const updated = await authApi.updateMe(fullName.trim(), email.trim() || null);
      updateSession({ fullName: updated.full_name });
      setMessage("Profile saved.");
      await reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not save your profile.");
    } finally {
      setBusy(false);
    }
  }

  async function chooseFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // lets the same file be chosen again later
    if (!file) return;
    setFormError("");
    setMessage("");
    setBusy(true);
    try {
      const updated = await authApi.setAvatar(await resizeImage(file));
      updateSession({ avatar: updated.avatar });
      setMessage("Photo updated.");
      await reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not upload the photo.");
    } finally {
      setBusy(false);
    }
  }

  async function removePhoto() {
    setFormError("");
    setMessage("");
    setBusy(true);
    try {
      await authApi.removeAvatar();
      updateSession({ avatar: null });
      setMessage("Photo removed.");
      await reload();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not remove the photo.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="max-w-2xl">
      <h1 className="text-2xl font-semibold">Profile</h1>
      <p className="mt-1 text-slate-600">Your name, role, and photo.</p>

      {error && <Alert kind="error">{error}</Alert>}
      {loading && !profile && <p className="mt-6 text-slate-500">Loading...</p>}

      {profile && (
        <>
          <div className="mt-6 flex flex-wrap items-center gap-5 rounded-xl border border-slate-200 bg-white p-5">
            {profile.avatar ? (
              <img src={profile.avatar} alt="Your profile" className="h-24 w-24 rounded-full object-cover" />
            ) : (
              <span className="grid h-24 w-24 place-items-center rounded-full bg-brand-600 text-3xl font-semibold text-white" aria-hidden="true">
                {profile.full_name.replace(/^dr\.\s*/i, "").charAt(0).toUpperCase()}
              </span>
            )}
            <div>
              <p className="text-lg font-semibold">{profile.full_name}</p>
              <p className="text-sm text-slate-600">
                {ROLE_LABEL[profile.role]}
                {profile.specialization ? ` - ${profile.specialization}` : ""}
              </p>
              {profile.assigned_doctor_name && <p className="text-sm text-slate-600">Supports {profile.assigned_doctor_name}</p>}
              <div className="mt-3 flex flex-wrap gap-2">
                <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={chooseFile} aria-label="Choose a photo" />
                <button type="button" className={secondaryButton} disabled={busy} onClick={() => fileInput.current?.click()}>
                  Upload photo
                </button>
                {profile.avatar && (
                  <button type="button" className={secondaryButton} disabled={busy} onClick={() => void removePhoto()}>
                    Remove photo
                  </button>
                )}
              </div>
            </div>
          </div>

          <form onSubmit={save} className="mt-6 space-y-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="font-semibold">Edit details</h2>
            <label className="block text-sm font-medium">
              Full name
              <input className={`${inputClass} mt-1`} maxLength={100} value={fullName} onChange={(e) => setFullName(e.target.value)} />
            </label>
            <label className="block text-sm font-medium">
              Email
              <input type="email" className={`${inputClass} mt-1`} maxLength={100} value={email} onChange={(e) => setEmail(e.target.value)} />
            </label>
            <dl className="grid gap-1 text-sm text-slate-600 sm:grid-cols-2">
              <div><dt className="inline font-medium">Username: </dt><dd className="inline">{profile.username}</dd></div>
              <div><dt className="inline font-medium">Last sign-in: </dt><dd className="inline">{formatDateTime(profile.last_login_at)}</dd></div>
              <div><dt className="inline font-medium">Account created: </dt><dd className="inline">{formatDateTime(profile.created_at)}</dd></div>
            </dl>
            {formError && <Alert kind="error">{formError}</Alert>}
            {message && <Alert kind="success">{message}</Alert>}
            <button type="submit" disabled={busy} className={primaryButton}>
              {busy ? "Saving..." : "Save changes"}
            </button>
          </form>
        </>
      )}
    </section>
  );
}