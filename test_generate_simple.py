import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest

from PIL import Image, ImageDraw

SPEC = importlib.util.spec_from_file_location(
    "generate_simple", Path(__file__).with_name("generate-simple.py")
)
simple = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(simple)
BACKGROUND = (238, 237, 217)


class TrimTests(unittest.TestCase):
    def test_textured_spacer_is_removed(self):
        randomizer = random.Random(42)
        image = Image.new("RGB", (150, 60), BACKGROUND)
        image.putdata(
            [
                tuple(c - randomizer.randrange(12) for c in BACKGROUND)
                for _ in range(image.width * image.height)
            ]
        )
        self.assertIsNone(simple.trim_background(image))

    def test_trim_preserves_outside_lettering_and_illustration(self):
        image = Image.new("RGB", (400, 500), BACKGROUND)
        draw = ImageDraw.Draw(image)
        draw.rectangle((150, 100, 300, 400), fill="black")
        draw.rectangle((330, 120, 340, 140), fill="black")
        draw.line((40, 350, 70, 370), fill=(170, 170, 160), width=2)
        trimmed = simple.trim_background(image)
        self.assertLess(trimmed.width, image.width)
        self.assertLess(trimmed.height, image.height)
        self.assertEqual(
            sum(p == (0, 0, 0) for p in image.get_flattened_data()),
            sum(p == (0, 0, 0) for p in trimmed.get_flattened_data()),
        )
        self.assertEqual(
            sum(p == (170, 170, 160) for p in image.get_flattened_data()),
            sum(p == (170, 170, 160) for p in trimmed.get_flattened_data()),
        )

    def test_full_bleed_and_dark_pages_are_unchanged(self):
        for color in ["black", "navy"]:
            image = Image.new("RGB", (200, 300), color)
            self.assertEqual(simple.trim_background(image).tobytes(), image.tobytes())
        image = Image.new("RGB", (200, 300), BACKGROUND)
        ImageDraw.Draw(image).rectangle((0, 0, 40, 40), fill="red")
        self.assertEqual(simple.trim_background(image).tobytes(), image.tobytes())


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.docs = Path(self.temp.name)
        self.source = self.docs / "4koma" / "ja"
        self.source.mkdir(parents=True)
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

    def test_page_order_size_and_no_upscale(self):
        paths = [
            self.source / name for name in ["first.png", "second.png", "spacer.png"]
        ]
        joined = simple.join_pages(paths, gap=8, padding=4, max_width=200)
        self.assertEqual(joined.size, (88, 166))
        self.assertEqual(joined.getpixel((44, 4)), (255, 0, 0))
        self.assertEqual(joined.getpixel((44, 112)), (0, 0, 255))
        self.assertEqual(joined.getpixel((4, 112)), (255, 0, 0))
        scaled = simple.join_pages(paths, gap=0, padding=0, max_width=40)
        self.assertEqual(scaled.size, (40, 75))

    def test_no_trim_keeps_spacers(self):
        paths = [self.source / name for name in ["first.png", "spacer.png"]]
        joined = simple.join_pages(paths, trim=False, padding=0, gap=0)
        self.assertEqual(joined.size, (80, 120))

    def test_max_dimension_shrinks_long_side_without_upscaling(self):
        Image.new("RGB", (120, 2400), "red").save(self.source / "first.png")
        simple.generate(self.docs, max_dimension=300)
        with Image.open(self.source / "simple" / "1.jpg") as image:
            self.assertLessEqual(image.width, 300)
            self.assertLessEqual(image.height, 300)
            self.assertGreater(image.height, image.width)
        simple.generate(self.docs)
        with Image.open(self.source / "simple" / "1.jpg") as image:
            self.assertLessEqual(image.width, 1600)
            self.assertLessEqual(image.height, 2048)

    def test_metadata_paths_originals_and_idempotence(self):
        original = (self.docs / "4komaData.json").read_bytes()
        source_bytes = {path: path.read_bytes() for path in self.source.iterdir()}
        self.assertEqual(simple.generate(self.docs), (1, 1))
        output = json.loads((self.docs / "4komaDataSimple.json").read_text())
        self.assertEqual(output, [{**self.rows[0], "ImagesUrl": ["./simple/1.jpg"]}])
        with Image.open(self.source / output[0]["ImagesUrl"][0]) as image:
            image.verify()
        self.assertEqual(simple.generate(self.docs), (1, 0))
        self.assertEqual((self.docs / "4komaData.json").read_bytes(), original)
        for path, data in source_bytes.items():
            self.assertEqual(path.read_bytes(), data)

    def test_source_and_metadata_updates_are_reflected(self):
        simple.generate(self.docs)
        Image.new("RGB", (80, 100), "green").save(self.source / "first.png")
        self.rows[0]["Title"] = "変更"
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (1, 1))
        data = json.loads((self.docs / "4komaDataSimple.json").read_text())
        self.assertEqual(data[0]["Title"], "変更")

    def test_missing_sources_do_not_publish_json(self):
        self.rows[0]["ImagesUrl"].append("missing.jpg")
        self.write_rows()
        with self.assertRaisesRegex(ValueError, "missing"):
            simple.generate(self.docs)
        self.assertFalse((self.docs / "4komaDataSimple.json").exists())

    def test_unsafe_sources_and_duplicate_indices_are_rejected(self):
        for value in ["../first.png", "/etc/passwd", "https://example.com/1.jpg"]:
            self.rows[0]["ImagesUrl"] = [value]
            self.write_rows()
            with self.assertRaises(ValueError):
                simple.generate(self.docs)
        self.rows[0]["ImagesUrl"] = ["first.png"]
        self.rows.append(self.rows[0].copy())
        self.write_rows()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            simple.generate(self.docs)

    def test_blank_only_episode_is_rejected(self):
        self.rows[0]["ImagesUrl"] = ["spacer.png"]
        self.write_rows()
        with self.assertRaisesRegex(ValueError, "blank"):
            simple.generate(self.docs)

    def test_invalid_options_are_rejected(self):
        for options in [
            {"padding": -1},
            {"gap": -1},
            {"max_width": 10},
            {"max_dimension": 0},
            {"threshold": 0},
            {"quality": 101},
        ]:
            with self.assertRaises(ValueError):
                simple.generate(self.docs, **options)

    def test_single_image_episode_and_list_order(self):
        self.rows.insert(0, {"Title": "先頭", "Index": 9, "ImagesUrl": ["first.png"]})
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (2, 2))
        data = json.loads((self.docs / "4komaDataSimple.json").read_text())
        self.assertEqual([row["Index"] for row in data], [9, 1])
        self.assertEqual(data[0]["ImagesUrl"], ["./simple/9.jpg"])

    def test_string_indices_are_preserved_and_filename_collisions_rejected(self):
        self.rows[0]["Index"] = "ri"
        self.write_rows()
        self.assertEqual(simple.generate(self.docs), (1, 1))
        data = json.loads((self.docs / "4komaDataSimple.json").read_text())
        self.assertEqual(data[0]["Index"], "ri")
        self.assertEqual(data[0]["ImagesUrl"], ["./simple/ri.jpg"])
        for index in ["../bad", "", True, -1, 1.5]:
            self.rows[0]["Index"] = index
            self.write_rows()
            with self.assertRaises(ValueError):
                simple.generate(self.docs)
        self.rows[0]["Index"] = 1
        self.rows.append({**self.rows[0], "Index": "1"})
        self.write_rows()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            simple.generate(self.docs)


class FitTests(unittest.TestCase):
    def test_shrinks_only_the_over_limit_side(self):
        tall = Image.new("RGB", (100, 3000), "red")
        fitted = simple.fit_max_dimension(tall, 2048)
        self.assertLessEqual(fitted.width, 2048)
        self.assertLessEqual(fitted.height, 2048)
        self.assertLess(fitted.height, 3000)
        self.assertAlmostEqual(fitted.width / fitted.height, 100 / 3000, delta=0.01)
        wide = Image.new("RGB", (3000, 100), "red")
        fitted = simple.fit_max_dimension(wide, 2048)
        self.assertLessEqual(fitted.width, 2048)
        self.assertLessEqual(fitted.height, 2048)
        self.assertLess(fitted.width, 3000)

    def test_small_images_are_not_upscaled(self):
        image = Image.new("RGB", (100, 200), "red")
        self.assertEqual(simple.fit_max_dimension(image, 2048).size, (100, 200))


class RepositoryCatalogTests(unittest.TestCase):
    def test_numbered_episodes_are_contiguous(self):
        root = Path(__file__).resolve().parent
        rows = json.loads((root / "4komaData.json").read_text(encoding="utf-8"))
        indices = [row["Index"] for row in rows if type(row["Index"]) is int]
        self.assertEqual(indices, list(range(1, max(indices) + 1)))

    def test_every_catalog_entry_has_one_decodable_image_and_preserved_metadata(self):
        docs = Path(__file__).resolve().parent
        original = json.loads((docs / "4komaData.json").read_text(encoding="utf-8"))
        generated = json.loads(
            (docs / "4komaDataSimple.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(generated), len(original))
        for source, output in zip(original, generated):
            with self.subTest(index=source["Index"]):
                self.assertEqual(
                    output, {**source, "ImagesUrl": [f"./simple/{source['Index']}.jpg"]}
                )
                path = docs / "4koma" / "ja" / output["ImagesUrl"][0]
                with Image.open(path) as image:
                    self.assertEqual(image.format, "JPEG")
                    self.assertLessEqual(image.width, 1600)
                    self.assertLessEqual(image.height, 2048)
                    image.load()


if __name__ == "__main__":
    unittest.main()
