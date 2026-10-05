"""Behavior fixtures: removing normalization/limits or changing DIB rows breaks these."""
import io
import struct
import unittest
from PIL import Image, PngImagePlugin

try:
    from snappaste import images
except ImportError:
    images = None


def encoded(image, format="PNG", **kwargs):
    output = io.BytesIO()
    image.save(output, format, **kwargs)
    return output.getvalue()


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(images, "image normalization module is not implemented")

    def test_exif_all_eight_orientations(self):
        # Numbered 3x2 fixture, expected rows derived by hand.
        source = Image.new("RGB", (3, 2))
        source.putdata([(n, 0, 0) for n in range(1, 7)])
        cases = {
            1: ((3, 2), [1, 2, 3, 4, 5, 6]),
            2: ((3, 2), [3, 2, 1, 6, 5, 4]),
            3: ((3, 2), [6, 5, 4, 3, 2, 1]),
            4: ((3, 2), [4, 5, 6, 1, 2, 3]),
            5: ((2, 3), [1, 4, 2, 5, 3, 6]),
            6: ((2, 3), [4, 1, 5, 2, 6, 3]),
            7: ((2, 3), [6, 3, 5, 2, 4, 1]),
            8: ((2, 3), [3, 6, 2, 5, 1, 4]),
        }
        for orientation, (size, pixels) in cases.items():
            with self.subTest(orientation=orientation):
                exif = Image.Exif()
                exif[274] = orientation
                result = images.normalize_image(encoded(source, exif=exif))
                self.assertEqual(result.size, size)
                self.assertEqual([p[0] for p in result.get_flattened_data()], pixels)

    def test_metadata_does_not_survive_pixel_normalization(self):
        source = Image.new("RGB", (2, 3), "red")
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "PRIVATE DESCRIPTION"
        text = PngImagePlugin.PngInfo()
        text.add_text("GPS", "PRIVATE LOCATION")
        text.add_itxt("XML:com.adobe.xmp", "PRIVATE XMP")
        result = images.normalize_image(encoded(source, exif=exif, pnginfo=text,
                                                 icc_profile=b"PRIVATE ICC"))
        self.assertEqual(result.size, (3, 2))
        self.assertEqual(result.info, {})
        self.assertEqual(dict(result.getexif()), {})
        self.assertNotIn(b"PRIVATE", images.dib_bytes(result))
        saved = Image.open(io.BytesIO(encoded(result)))
        self.assertEqual(saved.info, {})

    def test_resize_preserves_portrait_aspect(self):
        result = images.normalize_image(encoded(Image.new("RGB", (200, 400))), max_edge=100)
        self.assertEqual(result.size, (50, 100))

    def test_small_image_is_not_enlarged(self):
        result = images.normalize_image(encoded(Image.new("RGB", (7, 3))), max_edge=100)
        self.assertEqual(result.size, (7, 3))

    def test_alpha_is_composited_on_white(self):
        source = Image.new("RGBA", (3, 1))
        source.putdata([(255, 0, 0, 0), (0, 0, 255, 128), (255, 0, 0, 255)])
        result = images.normalize_image(encoded(source))
        self.assertEqual(result.mode, "RGB")
        self.assertEqual(list(result.get_flattened_data()), [(255, 255, 255), (127, 127, 255), (255, 0, 0)])

    def test_palette_transparency_is_composited(self):
        source = Image.new("P", (1, 1))
        source.putpalette([255, 0, 0] + [0] * 765)
        result = images.normalize_image(encoded(source, transparency=0))
        self.assertEqual(result.getpixel((0, 0)), (255, 255, 255))

    def test_jpeg_grayscale_and_webp_decode(self):
        for mode, format in [("L", "JPEG"), ("CMYK", "JPEG"), ("RGB", "WEBP")]:
            with self.subTest(mode=mode, format=format):
                result = images.normalize_image(encoded(Image.new(mode, (5, 3)), format))
                self.assertEqual(result.mode, "RGB")
                self.assertEqual(result.size, (5, 3))

    def test_corrupt_and_unsupported_are_rejected(self):
        for content in [b"not an image", encoded(Image.new("RGB", (2, 2)), "BMP")]:
            with self.subTest(content=content[:2]):
                with self.assertRaises(images.ImageValidationError):
                    images.normalize_image(content)

    def test_truncated_image_is_rejected(self):
        content = encoded(Image.new("RGB", (30, 30)), "JPEG")
        with self.assertRaises(images.ImageValidationError):
            images.normalize_image(content[:-20])

    def test_byte_and_pixel_limits_are_enforced(self):
        content = encoded(Image.new("RGB", (3, 2)))
        with self.assertRaises(images.ImageValidationError):
            images.normalize_image(content, max_bytes=len(content) - 1)
        with self.assertRaises(images.ImageValidationError):
            images.normalize_image(content, max_pixels=5)
        self.assertEqual(images.normalize_image(content, max_pixels=6).size, (3, 2))

    def test_animation_is_rejected(self):
        content = encoded(Image.new("RGB", (2, 2), "red"), "PNG", save_all=True,
                          append_images=[Image.new("RGB", (2, 2), "blue")], duration=100)
        with self.assertRaises(images.ImageValidationError):
            images.normalize_image(content)

    def test_dib_bgr_bottom_up_and_padding_widths_one_to_five(self):
        for width, stride in [(1, 4), (2, 8), (3, 12), (4, 12), (5, 16)]:
            with self.subTest(width=width):
                source = Image.new("RGB", (width, 2))
                source.putdata([(255, 0, 0)] * width + [(0, 0, 255)] * width)
                dib = images.dib_bytes(source)
                self.assertEqual(struct.unpack("<IiiHHIIiiII", dib[:40]),
                                 (40, width, 2, 1, 24, 0, stride * 2, 0, 0, 0, 0))
                padding = bytes(stride - width * 3)
                self.assertEqual(dib[40:], b"\xff\x00\x00" * width + padding +
                                 b"\x00\x00\xff" * width + padding)
                self.assertEqual(Image.open(io.BytesIO(dib)).getpixel((0, 0)), (255, 0, 0))


if __name__ == "__main__":
    unittest.main()
