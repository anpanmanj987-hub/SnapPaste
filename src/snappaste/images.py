"""Bounded decoding, orientation, pixel-only normalization and 24-bit DIB."""
from __future__ import annotations

import io
import struct
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

from .messages import text

MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELS = 50_000_000
MAX_EDGE = 1920
FORMATS = ("JPEG", "PNG", "WEBP")


class ImageValidationError(ValueError):
    """A rejected image; `key` names its text in messages.MESSAGES."""
    def __init__(self, key: str, code: str = "invalid_image"):
        super().__init__(text(key))
        self.key, self.code = key, code


def normalize_image(data: bytes, *, max_bytes: int = MAX_BYTES,
                    max_pixels: int = MAX_PIXELS, max_edge: int = MAX_EDGE) -> Image.Image:
    """Return fresh RGB pixels, without source metadata; never enlarge."""
    if min(max_bytes, max_pixels, max_edge) <= 0:
        raise ValueError("image limits must be positive")
    if not data:
        raise ImageValidationError("empty_image")
    if len(data) > max_bytes:
        raise ImageValidationError("image_too_large", "too_large")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=FORMATS) as source:
                if source.width * source.height > max_pixels:
                    raise ImageValidationError("too_many_pixels", "too_large")
                if getattr(source, "n_frames", 1) != 1:
                    raise ImageValidationError("animated", "unsupported")
                source.load()
                oriented = ImageOps.exif_transpose(source)
                rgba = oriented.convert("RGBA")
                rgb = Image.new("RGB", rgba.size, "white")
                rgb.paste(rgba, mask=rgba.getchannel("A"))
                rgb.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
                # No copy(), info dict, EXIF, ICC, PNG text, or XMP is carried forward.
                return Image.frombytes("RGB", rgb.size, rgb.tobytes())
    except ImageValidationError:
        raise
    except (Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise ImageValidationError("pixel_bomb", "too_large") from error
    except UnidentifiedImageError as error:
        raise ImageValidationError("unsupported", "unsupported") from error
    except (OSError, ValueError, SyntaxError) as error:
        raise ImageValidationError("corrupt") from error


def dib_bytes(image: Image.Image) -> bytes:
    """BITMAPINFOHEADER + bottom-up BGR rows; no BMP file header or metadata."""
    if image.mode != "RGB":
        raise ValueError("DIB input must be normalized RGB")
    width, height = image.size
    stride = (width * 3 + 3) & ~3
    row_bytes = width * 3
    pixels = image.tobytes("raw", "BGR")
    padding = bytes(stride - row_bytes)
    rows = b"".join(pixels[row * row_bytes:(row + 1) * row_bytes] + padding
                    for row in range(height - 1, -1, -1))
    header = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0,
                         len(rows), 0, 0, 0, 0)
    return header + rows
