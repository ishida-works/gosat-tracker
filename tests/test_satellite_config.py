import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TLE = """1 33492U 09002A   26215.86589030  .00000521  00000+0  10043-3 0  9995
2 33492  98.0924 326.3581 0001112 101.3560 258.7770 14.67537881938459
"""


class SatelliteConfigTest(unittest.TestCase):
    def test_config_drives_fetch_and_strict_failure_preserves_data(self):
        satellites = json.loads((ROOT / "satellites.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = pathlib.Path(temp_dir)
            shutil.copy(ROOT / "fetch_tle.py", directory)
            config = directory / "satellites.json"
            tle_file = directory / "input.tle"
            tle_file.write_text(TLE, encoding="utf-8")
            config.write_text(json.dumps(satellites[:1]), encoding="utf-8")
            command = [sys.executable, "-X", "utf8", str(directory / "fetch_tle.py"),
                       "--manual", str(tle_file), "--require-all"]
            first = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            output = directory / "data" / "tle.json"
            saved = output.read_bytes()
            self.assertEqual(set(json.loads(saved)["sats"]), {"33492"})

            config.write_text(json.dumps(satellites[:2]), encoding="utf-8")
            second = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output.read_bytes(), saved)


if __name__ == "__main__":
    unittest.main()
