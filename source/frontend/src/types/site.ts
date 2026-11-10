export interface SiteContent {
  version: string;
  has_logo: boolean;
  has_hero: boolean;
  values: Record<string, string>;
}

// Shown until the admin changes them (and whenever a field is cleared).
export const SITE_DEFAULTS: Record<string, string> = {
  hero_title: "Booked in a click!",
  hero_text:
    "Enjoy effortless scheduling on your own timeline. Simply choose your doctor and a convenient time; our clinical team will confirm your details so your room is fully prepared upon your arrival.",
  about_title: "About us",
  about_subtitle: "Your Partner in Health and Wellness",
  about_lead:
    "At AppointMed, we believe that accessing quality healthcare should be seamless, transparent, and centered around you. Our modern clinic brings together a dedicated team of experienced medical professionals, cutting-edge diagnostics, and patient-first values to deliver comprehensive care for individuals and families.",
  about_second:
    "From routine checkups and chronic condition management to effortless online booking, we are committed to making your healthcare journey as smooth as possible—ensuring you receive the right attention, right when you need it.",
  footer_text:
    "AppointMed is your trusted partner for clinical appointment booking. Connecting patients with certified specialists for world-class healthcare.",
  contact_phone: "+1 (234) 567-8900",
  contact_email: "info@appointmed.com",
  contact_hours: "Mon - Sat: 8:00 AM – 8:00 PM",
  social_facebook: "https://www.facebook.com",
  social_x: "https://x.com",
  social_linkedin: "https://www.linkedin.com",
  social_youtube: "https://www.youtube.com",
};