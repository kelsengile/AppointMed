// Shrinks a chosen picture to a 256x256 JPEG data URL, so it fits the backend's avatar size limit.
export function resizeImage(file: File, size = 256): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) {
      reject(new Error("Choose an image file (PNG, JPEG or WebP)."));
      return;
    }
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      const side = Math.min(image.width, image.height);
      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = size;
      const context = canvas.getContext("2d");
      URL.revokeObjectURL(url);
      if (!context) {
        reject(new Error("Your browser cannot process images."));
        return;
      }
      // Crop the centre square, then scale it down.
      context.drawImage(image, (image.width - side) / 2, (image.height - side) / 2, side, side, 0, 0, size, size);
      resolve(canvas.toDataURL("image/jpeg", 0.85));
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("That image could not be read."));
    };
    image.src = url;
  });
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