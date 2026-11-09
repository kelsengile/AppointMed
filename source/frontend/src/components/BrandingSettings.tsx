// Website and branding (logo, hero picture, front page texts and links). Shown on the Clinic Settings page.
import { useEffect, useRef, useState, type ChangeEvent, type ReactNode } from "react";
import { siteApi, type SiteImageKind } from "../api/siteApi";
import { publishSite, useSite } from "../hooks/useSite";
import { fitImage } from "../utils/image";
import Alert from "./Alert";
import { inputClass, primaryButton, secondaryButton } from "./ui";

function Card({ title, desc, children, className = "" }: { title: string; desc?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-slate-200 bg-white p-5 ${className}`}>
      <h2 className="text-lg font-semibold">{title}</h2>
      {desc && <p className="mt-1 text-sm text-slate-600">{desc}</p>}
      <div className="mt-4">{children}</div>
    </section>
  );
}

interface TextField {
  key: string;
  label: string;
  max: number;
  multi?: boolean;
  placeholder?: string;
}

const TEXT_GROUPS: { title: string; fields: TextField[] }[] = [
  {
    title: "Hero (top of the front page)",
    fields: [
      { key: "hero_title", label: "Headline", max: 120 },
      { key: "hero_text", label: "Intro text", max: 500, multi: true },
    ],
  },
  {
    title: "About us section",
    fields: [
      { key: "about_title", label: "Section title", max: 60 },
      { key: "about_subtitle", label: "Subtitle", max: 120 },
      { key: "about_lead", label: "First paragraph", max: 1000, multi: true },
      { key: "about_second", label: "Second paragraph", max: 1000, multi: true },
    ],
  },
  {
    title: "Footer and contact details",
    fields: [
      { key: "footer_text", label: "Footer description", max: 400, multi: true },
      { key: "contact_phone", label: "Phone number", max: 30 },
      { key: "contact_email", label: "Email address", max: 100 },
      { key: "contact_hours", label: "Opening hours", max: 100 },
    ],
  },
  {
    title: "Social media links",
    fields: [
      { key: "social_facebook", label: "Facebook", max: 255, placeholder: "https://www.facebook.com/yourpage" },
      { key: "social_x", label: "X (Twitter)", max: 255, placeholder: "https://x.com/yourpage" },
      { key: "social_linkedin", label: "LinkedIn", max: 255, placeholder: "https://www.linkedin.com/company/yourpage" },
      { key: "social_youtube", label: "YouTube", max: 255, placeholder: "https://www.youtube.com/@yourchannel" },
    ],
  },
];
const ALL_KEYS = TEXT_GROUPS.flatMap((g) => g.fields.map((f) => f.key));

function ImagePicker({
  kind, title, hint, current, fallback, box, mime, maxBytes, previewClass, onDone, onFail,
}: {
  kind: SiteImageKind;
  title: string;
  hint: string;
  current: string | null;
  fallback: string;
  box: [number, number];
  mime: "image/png" | "image/jpeg";
  maxBytes: number;
  previewClass: string;
  onDone: (message: string) => void;
  onFail: (message: string) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);

  async function choose(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setBusy(true);
    try {
      publishSite(await siteApi.setImage(kind, await fitImage(file, box[0], box[1], mime, maxBytes)));
      onDone(`${title} updated.`);
    } catch (err) {
      onFail(err instanceof Error ? err.message : "Could not upload the picture.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    try {
      publishSite(await siteApi.removeImage(kind));
      onDone(`${title} reset to the default.`);
    } catch (err) {
      onFail(err instanceof Error ? err.message : "Could not remove the picture.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-4">
      <img src={current ?? fallback} alt={`Current ${title.toLowerCase()}`} className={`${previewClass} rounded-lg border border-slate-200 bg-slate-100`} />
      <div>
        <p className="text-sm font-medium">{title}</p>
        <p className="text-xs text-slate-500">{hint}</p>
        <input ref={input} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={choose} aria-label={`Choose ${title.toLowerCase()}`} />
        <div className="mt-2 flex flex-wrap gap-2">
          <button type="button" className={secondaryButton} disabled={busy} onClick={() => input.current?.click()}>
            {busy ? "Working..." : "Upload new"}
          </button>
          {current && (
            <button type="button" className={secondaryButton} disabled={busy} onClick={() => void remove()}>
              Use default
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default function BrandingSettings() {
  const site = useSite();
  const [fields, setFields] = useState<Record<string, string>>(site.values);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  // Refill the form when the saved content changes (first load, or after a save).
  useEffect(() => {
    setFields(site.values);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [site.version]);

  async function saveTexts() {
    setError("");
    setMessage("");
    const changed = Object.fromEntries(
      ALL_KEYS.filter((k) => (fields[k] ?? "").trim() !== (site.values[k] ?? "")).map((k) => [k, (fields[k] ?? "").trim()]),
    );
    if (Object.keys(changed).length === 0) return setMessage("Nothing was changed.");
    setBusy(true);
    try {
      publishSite(await siteApi.save(changed));
      setMessage("Website text saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save the website text.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h2 className="mt-10 text-xl font-semibold">Website and branding</h2>
      <p className="mt-1 text-sm text-slate-600">Only administrators see this. Changes appear on the public front page.</p>
      {message && <Alert kind="success" onClose={() => setMessage("")}>{message}</Alert>}
      {error && <Alert kind="error">{error}</Alert>}

      <div className="mt-4 grid gap-6 lg:grid-cols-2">
        <Card title="Logo" desc="Shown in the navigation bar, side panel, and footer.">
          <ImagePicker
            kind="logo" title="Logo" hint="PNG, JPEG or WebP."
            current={site.logoSrc} fallback="/logo-mark.png" box={[512, 512]} mime="image/png" maxBytes={280_000}
            previewClass="h-16 w-auto max-w-[8rem] object-contain p-1" onDone={setMessage} onFail={setError}
          />
        </Card>

        <Card title="Hero picture" desc="The large picture at the top of the front page.">
          <ImagePicker
            kind="hero" title="Hero picture" hint="A wide picture works best. It is resized to fit."
            current={site.heroSrc} fallback="/hero-building.png" box={[1600, 1000]} mime="image/jpeg" maxBytes={1_400_000}
            previewClass="h-24 w-40 object-cover" onDone={setMessage} onFail={setError}
          />
        </Card>
      </div>

      <Card title="Front page text and links" desc="Open a group to edit it. Leave a field empty to use the default." className="mt-6">
        <div className="space-y-3">
          {TEXT_GROUPS.map((g, i) => (
            <details key={g.title} open={i === 0} className="rounded-lg border border-slate-200 p-3">
              <summary className="cursor-pointer font-medium">{g.title}</summary>
              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {g.fields.map((f) => (
                  <label key={f.key} className={`block text-sm font-medium ${f.multi ? "md:col-span-2" : ""}`}>
                    {f.label}
                    {f.multi ? (
                      <textarea className={`${inputClass} mt-1`} rows={3} maxLength={f.max} value={fields[f.key] ?? ""} onChange={(e) => setFields((p) => ({ ...p, [f.key]: e.target.value }))} />
                    ) : (
                      <input className={`${inputClass} mt-1`} maxLength={f.max} placeholder={f.placeholder} value={fields[f.key] ?? ""} onChange={(e) => setFields((p) => ({ ...p, [f.key]: e.target.value }))} />
                    )}
                  </label>
                ))}
              </div>
            </details>
          ))}
        </div>
        <button type="button" disabled={busy} className={`${primaryButton} mt-4`} onClick={() => void saveTexts()}>
          {busy ? "Saving..." : "Save website text"}
        </button>
      </Card>
    </>
  );
}