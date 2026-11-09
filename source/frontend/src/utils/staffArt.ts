// The character picture shown for each staff member (same rule as "Meet Our Staff" on the front page).
const ART_KEYS = ["spongebob", "sandy", "krabs", "squidward", "patrick", "pearl", "blossom", "bubbles", "buttercup", "dora"];

export interface StaffArt {
  bg: string;
  figure: string;
}

export function staffArt(fullName: string, index = 0): StaffArt {
  const words = fullName
    .toLowerCase()
    .replace(/^(dr|mr|mrs|ms)\.?\s+/, "")
    .split(/\s+/);
  let found = -1;
  for (const word of words) {
    found = ART_KEYS.indexOf(word);
    if (found >= 0) break;
  }
  if (found < 0) found = ART_KEYS.findIndex((key) => words.some((w) => w.includes(key)));
  const slot = (found >= 0 ? found : index % ART_KEYS.length) + 1;
  return { bg: `/doctor-${slot}.png`, figure: `/docchar-${slot}.png` };
}