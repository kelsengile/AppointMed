// Used for profile pictures. A square JPEG data URL under the backend's 300 KB limit.
// A picture with a transparent background is placed on one of the 10 backgrounds in public/doctor-1.png ... doctor-10.png
// (picked from `seed`, so the same person always gets the same one).
const BACKGROUNDS = 10;

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error("That image could not be read."));
    image.src = src;
  });
}

function pickBackground(seed: string): number {
  let hash = 0;
  for (const ch of seed) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return (hash % BACKGROUNDS) + 1;
}

function hasTransparency(image: HTMLImageElement): boolean {
  const scale = Math.min(1, 128 / Math.max(image.width, image.height));
  const w = Math.max(1, Math.round(image.width * scale));
  const h = Math.max(1, Math.round(image.height * scale));
  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const context = canvas.getContext("2d");
  if (!context) return false;
  context.drawImage(image, 0, 0, w, h);
  const pixels = context.getImageData(0, 0, w, h).data;
  for (let i = 3; i < pixels.length; i += 4) if (pixels[i] < 250) return true;
  return false;
}

export async function resizeImage(file: File, size = 512, seed = ""): Promise<string> {
  if (!file.type.startsWith("image/")) throw new Error("Choose an image file (PNG, JPEG or WebP).");
  const url = URL.createObjectURL(file);
  try {
    const image = await loadImage(url);
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const context = canvas.getContext("2d");
    if (!context) throw new Error("Your browser cannot process images.");

    if (hasTransparency(image)) {
      // Draw one of the clinic backgrounds first (cropped to a square), then the person on top, bottom-aligned.
      try {
        const background = await loadImage(`/doctor-${pickBackground(seed)}.png`);
        const side = Math.min(background.width, background.height);
        context.drawImage(background, (background.width - side) / 2, (background.height - side) / 2, side, side, 0, 0, size, size);
      } catch {
        context.fillStyle = "#DCE9FB";
        context.fillRect(0, 0, size, size);
      }
      const scale = Math.min(size / image.width, size / image.height);
      const w = image.width * scale;
      const h = image.height * scale;
      context.drawImage(image, (size - w) / 2, size - h, w, h);
    } else {
      // Crop the centre square, then scale it.
      const side = Math.min(image.width, image.height);
      context.drawImage(image, (image.width - side) / 2, (image.height - side) / 2, side, side, 0, 0, size, size);
    }

    let quality = 0.85;
    let out = canvas.toDataURL("image/jpeg", quality);
    while (out.length * 0.75 > 280_000 && quality > 0.4) {
      quality -= 0.1;
      out = canvas.toDataURL("image/jpeg", quality);
    }
    return out;
  } finally {
    URL.revokeObjectURL(url);
  }
}

/** Shrinks a picture to fit inside maxW x maxH (keeps the proportions) and returns a data URL under maxBytes. */
export function fitImage(file: File, maxW: number, maxH: number, mime: "image/png" | "image/jpeg", maxBytes: number): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) {
      reject(new Error("Choose an image file (PNG, JPEG or WebP)."));
      return;
    }
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      const scale = Math.min(1, maxW / image.width, maxH / image.height);
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(image.width * scale));
      canvas.height = Math.max(1, Math.round(image.height * scale));
      const context = canvas.getContext("2d");
      if (!context) {
        reject(new Error("Your browser cannot process images."));
        return;
      }
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      let quality = 0.9;
      let out = canvas.toDataURL(mime, quality);
      while (mime === "image/jpeg" && out.length * 0.75 > maxBytes && quality > 0.4) {
        quality -= 0.1;
        out = canvas.toDataURL(mime, quality);
      }
      if (out.length * 0.75 > maxBytes) {
        reject(new Error("That picture is too large. Choose a smaller one."));
        return;
      }
      resolve(out);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("That image could not be read."));
    };
    image.src = url;
  });
}