// The signed-in user's profile: view details, edit the public profile, and upload or remove a picture.
// The picture and the public details also appear on the landing page ("Meet Our Staff") and the staff profile page.
import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { authApi } from "../../api/endpoints";
import Alert from "../../components/Alert";
import { inputClass, primaryButton, secondaryButton } from "../../components/ui";
import { useAuth } from "../../context/AuthContext";
import { usePolling } from "../../hooks/usePolling";
import type { Role } from "../../types";
import { formatDateTime } from "../../utils/format";
import { resizeImage } from "../../utils/image";
import { INT_PROPS, cleanEmail, cleanInt, cleanMultiline, cleanName, cleanText, isEmail, isName } from "../../utils/input";
import Avatar from "../../components/Avatar";

const ROLE_LABEL: Record<Role, string> = { doctor: "Doctor", nurse: "Nurse", admin: "Administrator" };

export default function ProfilePage() {
  const { updateSession } = useAuth();
  const { data: profile, error, loading, reload } = usePolling(() => authApi.me(), 0);
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [bio, setBio] = useState("");
  const [education, setEducation] = useState("");
  const [years, setYears] = useState("");
  const [languages, setLanguages] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [formError, setFormError] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (profile) {
      setFullName(profile.full_name);
      setEmail(profile.email ?? "");
      setBio(profile.bio ?? "");
      setEducation(profile.education ?? "");
      setYears(profile.years_experience === null || profile.years_experience === undefined ? "" : String(profile.years_experience));
      setLanguages(profile.languages ?? "");
    }
  }, [profile]);

  async function save(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    setMessage("");
    if (!isName(fullName.trim())) return setFormError("Enter your full name (letters only, at least 2).");
    if (email.trim() && !isEmail(email.trim())) return setFormError("Enter a valid email address.");
    if (years && Number(years) > 70) return setFormError("Years of experience must be 70 or less.");
    setBusy(true);
    try {
      const updated = await authApi.updateMe({
        full_name: fullName.trim(),
        email: email.trim() || null,
        bio: bio.trim() || null,
        education: education.trim() || null,
        years_experience: years ? Number(years) : null,
        languages: languages.trim() || null,
      });
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
    e.target.value = "";
    if (!file) return;
    setFormError("");
    setMessage("");
    setBusy(true);
    try {
      const updated = await authApi.setAvatar(await resizeImage(file, 512, profile?.full_name ?? ""));
      updateSession({ avatar: updated.avatar });
      setMessage("Photo updated. It now also appears on the home page.");
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
    <section className="mx-auto max-w-2xl">
      <h1 className="text-center text-2xl font-semibold">Profile</h1>
      <p className="mt-1 text-center text-slate-600">Your name, role, photo, and the public details shown on the home page.</p>

      {error && <Alert kind="error">{error}</Alert>}
      {loading && !profile && <p className="mt-6 text-slate-500">Loading...</p>}

      {profile && (
        <>
          <div className="mt-6 flex flex-col items-center gap-5 rounded-xl border border-slate-200 bg-white p-5 text-center sm:flex-row sm:text-left">
            <Avatar avatar={profile.avatar} name={profile.full_name} className="h-24 w-24" />
            <div>
              <p className="text-lg font-semibold">{profile.full_name}</p>
              <p className="text-sm text-slate-600">
                {ROLE_LABEL[profile.role]}
                {profile.specialization ? ` - ${profile.specialization}` : ""}
              </p>
              {profile.assigned_doctor_name && <p className="text-sm text-slate-600">Supports {profile.assigned_doctor_name}</p>}
              <div className="mt-3 flex flex-wrap justify-center gap-2 sm:justify-start">
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
              <p className="mt-2 text-xs text-slate-500">
                This photo is shown on the home page. If it has a transparent background, one of the clinic backgrounds is added behind you.
              </p>
            </div>
          </div>

          <form onSubmit={save} className="mt-6 space-y-4 rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="font-semibold">Edit details</h2>
            <label className="block text-sm font-medium">
              Full name
              <input className={`${inputClass} mt-1`} maxLength={100} autoComplete="off" value={fullName} onChange={(e) => setFullName(cleanName(e.target.value))} />
            </label>
            <label className="block text-sm font-medium">
              Email
              <input type="email" className={`${inputClass} mt-1`} maxLength={100} value={email} onChange={(e) => setEmail(cleanEmail(e.target.value))} />
            </label>

            <h3 className="pt-2 text-sm font-semibold text-slate-700">Public profile (shown on the home page and your profile page)</h3>
            <label className="block text-sm font-medium">
              About me
              <textarea className={`${inputClass} mt-1`} rows={4} maxLength={1000} value={bio} onChange={(e) => setBio(cleanMultiline(e.target.value, 1000))} />
            </label>
            <label className="block text-sm font-medium">
              Education and training
              <input className={`${inputClass} mt-1`} maxLength={255} value={education} onChange={(e) => setEducation(cleanText(e.target.value, 255))} />
            </label>
            <div className="grid gap-4 sm:grid-cols-2">
              <label className="block text-sm font-medium">
                Years of experience
                <input {...INT_PROPS} maxLength={2} className={`${inputClass} mt-1`} value={years} onChange={(e) => setYears(cleanInt(e.target.value, 2))} />
              </label>
              <label className="block text-sm font-medium">
                Languages spoken
                <input
                  className={`${inputClass} mt-1`}
                  maxLength={150}
                  placeholder="e.g. English, Filipino"
                  value={languages}
                  onChange={(e) => setLanguages(e.target.value.replace(/[^\p{L}\p{M} ,.&/-]/gu, "").slice(0, 150))}
                />
              </label>
            </div>

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