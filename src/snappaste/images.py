"""Bounded decoding, orientation, pixel-only normalization and 24-bit DIB."""
from __future__ import annotations

import io
import struct
import warnings
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 25 * 1024 * 1024
MAX_PIXELS = 50_000_000
MAX_EDGE = 1920
FORMATS = ("JPEG", "PNG", "WEBP")


class ImageValidationError(ValueError):
    def __init__(self, message: str, code: str = "invalid_image"):
        super().__init__(message)
        self.code = code


def normalize_image(data: bytes, *, max_bytes: int = MAX_BYTES,
                    max_pixels: int = MAX_PIXELS, max_edge: int = MAX_EDGE) -> Image.Image:
    """Return fresh RGB pixels, without source metadata; never enlarge."""
    if min(max_bytes, max_pixels, max_edge) <= 0:
        raise ValueError("image limits must be positive")
    if not data:
        raise ImageValidationError("画像が空です。JPEG・PNG・WebPを選んでください。")
    if len(data) > max_bytes:
        raise ImageValidationError("画像の容量が上限を超えています。小さい画像を選んでください。", "too_large")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data), formats=FORMATS) as source:
                if source.width * source.height > max_pixels:
                    raise ImageValidationError("画像の画素数が上限を超えています。", "too_large")
                if getattr(source, "n_frames", 1) != 1:
                    raise ImageValidationError("アニメーション画像には対応していません。", "unsupported")
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
        raise ImageValidationError("画像の画素数が安全上の上限を超えています。", "too_large") from error
    except UnidentifiedImageError as error:
        raise ImageValidationError("JPEG・PNG・WebPを選んでください。HEICはJPEGへ変換してください。", "unsupported") from error
    except (OSError, ValueError, SyntaxError) as error:
        raise ImageValidationError("画像を読み込めませんでした。壊れていない別の画像を選んでください。") from error


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
