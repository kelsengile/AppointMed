"""
Helpers for profile pictures.

Two jobs:
  * prepare_avatar(path)  - turns whatever picture the user picked (any
    size, PNG/JPG/GIF/...) into a small square JPEG, ready to be stored
    in the database. Keeping it tiny (256x256) keeps the database light
    and every device fast, since the picture is loaded from the central
    database each time the app opens.
  * render_avatar(...)    - turns those stored bytes (or, when the user
    has no picture, their initials) into a round image a CustomTkinter
    label can show.

Needs the Pillow package (`pip install pillow`).
"""

import os
from io import BytesIO

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps

from utils.exceptions import InvalidImageError

# Side length, in pixels, of the square picture kept in the database.
STORED_SIZE = 256

# Refuse absurdly large source files before even trying to open them.
MAX_SOURCE_BYTES = 10 * 1024 * 1024

# Pillow moved the resampling constants in version 9.1; this works on both.
_RESAMPLE = Image.Resampling.LANCZOS

# Fonts tried, in order, for the initials. The first one found wins;
# Pillow's built-in font is the last resort so this never fails.
_FONT_CANDIDATES = (
    "arialbd.ttf",            # Windows
    "Arial Bold.ttf",         # macOS
    "Helvetica.ttc",          # macOS
    "DejaVuSans-Bold.ttf",    # Linux
)


# ---------------------------------------------------------------------------
# Picking a picture -> bytes for the database
# ---------------------------------------------------------------------------
def prepare_avatar(path):
    """Reads the image at `path`, crops it to a centred square, shrinks it
    to STORED_SIZE and returns it as JPEG bytes. Raises InvalidImageError
    (with a message fit to show the user) if it can't be done."""
    try:
        if os.path.getsize(path) > MAX_SOURCE_BYTES:
            raise InvalidImageError("That picture is larger than 10 MB. Please choose a smaller one.")

        with Image.open(path) as source:
            # Phones store "which way is up" in the file rather than
            # rotating the pixels; honour it so photos aren't sideways.
            upright = ImageOps.exif_transpose(source)
            rgba = upright.convert("RGBA")
    except InvalidImageError:
        raise
    except (OSError, ValueError, Image.DecompressionBombError):
        raise InvalidImageError("That file could not be opened as a picture.")

    # JPEG has no transparency, so flatten onto white first.
    flat = Image.new("RGB", rgba.size, "white")
    flat.paste(rgba, mask=rgba.getchannel("A"))

    square = ImageOps.fit(flat, (STORED_SIZE, STORED_SIZE), _RESAMPLE)
    buffer = BytesIO()
    square.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Stored bytes (or initials) -> round image for a label
# ---------------------------------------------------------------------------
def _load_font(size):
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)   # Pillow 10.1+
    except TypeError:
        return ImageFont.load_default()


def _initials(name):
    """"Juan Diaz" -> "JD", "Dr. Ana" -> "A", "" -> "?"."""
    words = [w for w in (name or "").replace(".", " ").split() if w]
    if len(words) > 1 and words[0].lower() == "dr":
        words = words[1:]
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][0].upper()
    return (words[0][0] + words[-1][0]).upper()


def _circle_mask(px):
    """A smooth-edged filled circle. Drawn 4x too big and shrunk, because
    drawing a circle directly leaves jagged edges."""
    big = Image.new("L", (px * 4, px * 4), 0)
    ImageDraw.Draw(big).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
    return big.resize((px, px), _RESAMPLE)


def _initials_face(name, px, bg, fg):
    face = Image.new("RGB", (px, px), bg)
    draw = ImageDraw.Draw(face)
    text = _initials(name)
    font = _load_font(int(px * 0.42))
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text(
        ((px - (right - left)) / 2 - left, (px - (bottom - top)) / 2 - top),
        text, font=font, fill=fg
    )
    return face


def render_avatar(data, name, size, bg="#3A4152", fg="white",
                  ring_color=None, ring_width=0):
    """A round CTkImage of `size` x `size` (display pixels).

    data        - the stored picture bytes, or None/empty for "no picture",
                  in which case the person's initials are drawn instead
    name        - used for the initials
    bg, fg      - background / text colour of the initials version
    ring_color  - optional coloured border around the circle
    ring_width  - border thickness in display pixels

    The image is built at twice the display size so it stays sharp on
    high-DPI screens; CustomTkinter scales it down as needed."""
    px = size * 2
    ring_px = ring_width * 2 if ring_color else 0
    inner = px - 2 * ring_px

    face = None
    if data:
        try:
            picture = Image.open(BytesIO(bytes(data))).convert("RGB")
            face = ImageOps.fit(picture, (inner, inner), _RESAMPLE)
        except (OSError, ValueError):
            face = None            # corrupt data: fall back to initials
    if face is None:
        face = _initials_face(name, inner, bg, fg)

    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    if ring_px:
        ring = Image.new("RGBA", (px, px), ring_color)
        canvas.paste(ring, (0, 0), _circle_mask(px))
    canvas.paste(face, (ring_px, ring_px), _circle_mask(inner))

    return ctk.CTkImage(light_image=canvas, dark_image=canvas, size=(size, size))