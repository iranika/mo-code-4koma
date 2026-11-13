import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image, ImageDraw, JpegImagePlugin

SPEC = importlib.util.spec_from_file_location(
    "generate_simple", Path(__file__).with_name("generate-simple.py")
)
simple = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(simple)
BACKGROUND = (238, 237, 217)


class FitTests(unittest.TestCase):
    def test_preserves_aspect_ratio_and_borders_without_cropping(self):
        for size, expected in [
            ((3000, 1500), (2048, 1024)),
            ((1500, 3000), (1024, 2048)),
        ]:
            with self.subTest(size=size):
                image = Image.new("RGB", size, "white")
                draw = ImageDraw.Draw(image)
                draw.rectangle((0, 0, 100, 100), fill="red")
                draw.rectangle((size[0] - 101, size[1] - 101, *size), fill="blue")
                fitted = simple.fit_max_dimension(image)
                self.assertEqual(fitted.size, expected)
                self.assertEqual(fitted.getpixel((0, 0)), (255, 0, 0))
                self.assertEqual(
                    fitted.getpixel((expected[0] - 1, expected[1] - 1)), (0, 0, 255)
                )
                self.assertEqual(image.size, size)

    def test_small_and_boundary_images_are_not_upscaled(self):
        for size in [(100, 200), (2048, 100), (100, 2048), (2048, 2048)]:
            with self.subTest(size=size):
                image = Image.new("RGB", size, "red")
                fitted = simple.fit_max_dimension(image)
                self.assertEqual(fitted.size, size)
                self.assertEqual(fitted.tobytes(), image.tobytes())


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = Path(self.temp.name)
        self.source = self.docs / "4koma" / "ja"
        self.source.mkdir(parents=True)
        self.output = self.source / "simple"
        self.catalog = self.docs / "4komaDataSimple.json"
        self.rows = [
            {
                "Title": "テスト",
                "BaseUrl": "https://example.com/1",
                "Index": 1,
                "ImagesUrl": ["./first.png", "second.png", "spacer.png"],
                "Extra": {"keep": True},
            }
        ]
        Image.new("RGB", (80, 100), "red").save(self.source / "first.png")
        Image.new("RGB", (60, 50), "blue").save(self.source / "second.png")
        Image.new("RGB", (80, 20), BACKGROUND).save(self.source / "spacer.png")
        self.write_rows()

    def write_rows(self):
        (self.docs / "4komaData.json").write_text(
            json.dumps(self.rows), encoding="utf-8"
        )

    def read_output(self):
        return json.loads(self.catalog.read_text())

    def test_preserves_metadata_page_order_and_unmodified_image_bytes(self):
        original = (self.docs / "4komaData.json").read_bytes()
        sources = {p.name: p.read_bytes() for p in self.source.iterdir()}
        self.assertEqual(simple.generate(self.docs), (1, 3))
        self.assertEqual(
            self.read_output(),
            [
                {
                    **self.rows[0],
                    "ImagesUrl": [
                        "./simple/first.png",
                        "./simple/second.png",
                        "./simple/spacer.png",
                    ],
                }
            ],
        )
        self.assertEqual((self.docs / "4komaData.json").read_bytes(), original)
        for name, data in sources.items():
            self.assertEqual((self.output / name).read_bytes(), data)
            self.assertEqual((self.source / name).read_bytes(), data)

    def test_idempotence_does_not_rewrite_images_or_catalog(self):
        simple.generate(self.docs)
        files = [self.catalog, *self.output.iterdir()]
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
        self.assertEqual(simple.generate(self.docs), (1, 0))
        self.assertEqual(
            before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in files}
        )

    def test_small_jpeg_is_copied_without_recompression(self):
        path = self.source / "original.jpg"
        Image.new("RGB", (1900, 2048), "red").save(path, quality=75)
        self.rows[0]["ImagesUrl"] = [path.name]
        self.write_rows()
        simple.generate(self.docs)
        self.assertEqual((self.output / path.name).read_bytes(), path.read_bytes())

    def test_resizes_each_large_page_independently_and_preserves_originals(self):
        for name, size in [("tall.jpg", (1500, 3000)), ("wide.jpg", (3000, 1500))]:
            Image.new("RGB", size, "red").save(self.source / name)
        self.rows[0]["ImagesUrl"] = ["tall.jpg", "wide.jpg", "spacer.png"]
        self.write_rows()
        before = {p: p.read_bytes() for p in self.source.iterdir()}
        self.assertEqual(simple.generate(self.docs), (1, 3))
        for name, expected in [("tall.jpg", (1024, 2048)), ("wide.jpg", (2048, 1024))]:
            with Image.open(self.output / name) as image:
                self.assertEqual(image.size, expected)
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(JpegImagePlugin.get_sampling(image), 0)
                image.load()
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)

    def test_resizes_png_without_changing_its_format_or_alpha(self):
        Image.new("RGBA", (1000, 3000), (255, 0, 0, 128)).save(
            self.source / "first.png"
        )
        simple.generate(self.docs)
        with Image.open(self.output / "first.png") as image:
            self.assertEqual(image.format, "PNG")
            self.assertEqual(image.height, 2048)
            self.assertEqual(image.getpixel((0, 0))[3], 128)

    def test_custom_limit_cannot_exceed_vrchat_limit(self):
        simple.generate(self.docs, max_dimension=50)
        for path in self.output.iterdir():
            with Image.open(path) as image:
                self.assertLessEqual(max(image.size), 50)
        for options in [
            {"max_dimension": 0},
            {"max_dimension": 2049},
            {"quality": 0},
            {"quality": 101},
        ]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                simple.generate(self.docs, **options)

    def test_shared_images_and_repeated_references_are_preserved(self):
        self.rows[0]["ImagesUrl"].append("first.png")
        self.rows.append({**self.rows[0], "Index": 2})
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (2, 3))
        for row in self.read_output():
            self.assertEqual(
                row["ImagesUrl"],
                [
                    "./simple/first.png",
                    "./simple/second.png",
                    "./simple/spacer.png",
                    "./simple/first.png",
                ],
            )
        self.assertEqual(len(list(self.output.iterdir())), 3)

    def test_preserves_nested_paths_with_the_same_basename(self):
        for directory, color in [("a", "red"), ("b", "blue")]:
            (self.source / directory).mkdir()
            Image.new("RGB", (30, 40), color).save(self.source / directory / "page.png")
        self.rows[0]["ImagesUrl"] = ["a/page.png", "b/page.png"]
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (1, 2))
        self.assertEqual(
            self.read_output()[0]["ImagesUrl"],
            ["./simple/a/page.png", "./simple/b/page.png"],
        )
        self.assertNotEqual(
            (self.output / "a/page.png").read_bytes(),
            (self.output / "b/page.png").read_bytes(),
        )

    def test_removes_legacy_joined_and_unreferenced_images_only(self):
        self.output.mkdir()
        for name in ["1.jpg", "ri.jpg", "orphan.jpg", "first.png"]:
            (self.output / name).write_bytes(b"old joined image")
        (self.output / "old").mkdir()
        (self.output / "old/page.jpg").write_bytes(b"unused")
        simple.generate(self.docs)
        self.assertEqual(
            {p.name for p in self.output.iterdir()},
            {"first.png", "second.png", "spacer.png"},
        )
        self.assertEqual(
            (self.output / "first.png").read_bytes(),
            (self.source / "first.png").read_bytes(),
        )
        self.assertTrue((self.source / "first.png").is_file())

    def test_blank_only_episode_is_copied_not_omitted(self):
        self.rows[0]["ImagesUrl"] = ["spacer.png"]
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (1, 1))
        self.assertEqual(self.read_output()[0]["ImagesUrl"], ["./simple/spacer.png"])
        self.assertEqual(
            (self.output / "spacer.png").read_bytes(),
            (self.source / "spacer.png").read_bytes(),
        )

    def test_source_and_metadata_changes_are_reflected(self):
        simple.generate(self.docs)
        Image.new("RGB", (80, 100), "green").save(self.source / "first.png")
        self.rows[0]["Title"] = "変更"
        self.rows[0]["ImagesUrl"] = ["second.png", "first.png"]
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (1, 1))
        self.assertEqual(self.read_output()[0]["Title"], "変更")
        self.assertEqual(
            self.read_output()[0]["ImagesUrl"],
            ["./simple/second.png", "./simple/first.png"],
        )
        self.assertFalse((self.output / "spacer.png").exists())

    def test_missing_sources_do_not_publish_or_delete_existing_files(self):
        self.output.mkdir()
        (self.output / "1.jpg").write_bytes(b"old joined image")
        self.rows[0]["ImagesUrl"].append("missing.jpg")
        self.write_rows()
        with self.assertRaisesRegex(ValueError, "missing"):
            simple.generate(self.docs)
        self.assertFalse(self.catalog.exists())
        self.assertEqual((self.output / "1.jpg").read_bytes(), b"old joined image")

    def test_corrupt_source_keeps_previous_catalog_and_images(self):
        simple.generate(self.docs)
        before = {p: p.read_bytes() for p in [self.catalog, *self.output.iterdir()]}
        Image.new("RGB", (80, 100), "green").save(self.source / "first.png")
        (self.source / "second.png").write_bytes(b"corrupt image")
        with self.assertRaises(OSError):
            simple.generate(self.docs)
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertEqual(list(self.docs.glob(".simple-*")), [])

    def test_unsafe_source_and_output_symlinks_are_rejected(self):
        simple.generate(self.docs)
        unsafe = [
            "../first.png",
            str(self.source / "first.png"),
            "https://example.com/1.jpg",
            "simple/first.png",
            "a/../first.png",
            "a\\first.png",
        ]
        for url in unsafe:
            self.rows[0]["ImagesUrl"] = [url]
            self.write_rows()
            with self.subTest(url=url), self.assertRaises(ValueError):
                simple.generate(self.docs)
        self.rows[0]["ImagesUrl"] = ["first.png"]
        self.write_rows()
        (self.output / "link").symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            simple.generate(self.docs)

    def test_string_indices_list_order_and_duplicate_indices(self):
        self.rows.insert(
            0, {"Title": "りれきしょ", "Index": "ri", "ImagesUrl": ["first.png"]}
        )
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (2, 3))
        self.assertEqual([row["Index"] for row in self.read_output()], ["ri", 1])
        for index in ["../bad", "", True, -1, 1.5, "1"]:
            self.rows[0]["Index"] = index
            self.write_rows()
            with self.subTest(index=index), self.assertRaises(ValueError):
                simple.generate(self.docs)


class RepositoryCatalogTests(unittest.TestCase):
    def test_numbered_episodes_are_contiguous(self):
        root = Path(__file__).resolve().parent
        rows = json.loads((root / "4komaData.json").read_text(encoding="utf-8"))
        indices = [row["Index"] for row in rows if type(row["Index"]) is int]
        self.assertEqual(indices, list(range(1, max(indices) + 1)))

    def test_every_page_has_matching_metadata_order_and_vrchat_safe_copy(self):
        docs = Path(__file__).resolve().parent
        source = docs / "4koma" / "ja"
        original = json.loads((docs / "4komaData.json").read_text(encoding="utf-8"))
        generated = json.loads(
            (docs / "4komaDataSimple.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(generated), len(original))
        expected = set()
        checked = set()
        for row, output in zip(original, generated):
            urls = [f"./simple/{Path(url).as_posix()}" for url in row["ImagesUrl"]]
            self.assertEqual(output, {**row, "ImagesUrl": urls})
            for original_url, url in zip(row["ImagesUrl"], urls):
                path = source / url
                expected.add(path.relative_to(source / "simple"))
                if path in checked:
                    continue
                checked.add(path)
                with (
                    self.subTest(path=path),
                    Image.open(source / original_url) as before,
                ):
                    with Image.open(path) as image:
                        image.load()
                        self.assertEqual(image.format, before.format)
                        self.assertLessEqual(image.width, 2048)
                        self.assertLessEqual(image.height, 2048)
                        self.assertLessEqual(image.width, before.width)
                        self.assertLessEqual(image.height, before.height)
                        if max(before.size) <= 2048:
                            self.assertEqual(
                                path.read_bytes(), (source / original_url).read_bytes()
                            )
                        else:
                            self.assertEqual(max(image.size), 2048)
                            self.assertAlmostEqual(
                                image.width / image.height,
                                before.width / before.height,
                                delta=1 / min(image.size),
                            )
        actual = {
            p.relative_to(source / "simple")
            for p in (source / "simple").rglob("*")
            if p.is_file()
        }
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
