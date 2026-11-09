import { useEffect, useState } from "react";
import { siteApi } from "../api/siteApi";
import { SITE_DEFAULTS, type SiteContent } from "../types/site";

// One shared copy of the website content, so the logo and texts update everywhere at once.
let current: SiteContent = { version: "0", has_logo: false, has_hero: false, values: {} };
let loaded = false;
let loading = false;
const listeners = new Set<() => void>();

export function publishSite(next: SiteContent): void {
  current = next;
  loaded = true;
  listeners.forEach((listener) => listener());
}

export function useSite() {
  const [, tick] = useState(0);
  useEffect(() => {
    const listener = () => tick((n) => n + 1);
    listeners.add(listener);
    if (!loaded && !loading) {
      loading = true;
      siteApi
        .get()
        .then(publishSite)
        .catch(() => undefined) // the built-in defaults are used when the request fails
        .finally(() => {
          loading = false;
        });
    }
    return () => {
      listeners.delete(listener);
    };
  }, []);
  const v = encodeURIComponent(current.version);
  return {
    values: { ...SITE_DEFAULTS, ...current.values },
    version: current.version,
    logoSrc: current.has_logo ? `/api/public/site-image/logo?v=${v}` : null,
    heroSrc: current.has_hero ? `/api/public/site-image/hero?v=${v}` : null,
  };
}