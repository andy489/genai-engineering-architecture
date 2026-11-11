import contextlib
import io
import os
import unittest
from unittest.mock import patch
from app import effective_config, main

BASE = dict(APP_ENV="demo", MODEL_NAME="demo-model", LOG_LEVEL="INFO",
            MAX_OUTPUT_TOKENS="256", PROVIDER_API_KEY="private-sentinel")


class ConfigTests(unittest.TestCase):
    def test_safe_projection(self):
        with patch.dict(os.environ, BASE | {"OTHER_SECRET": "hidden-sentinel"}, clear=True):
            config = effective_config()
        self.assertEqual(config["PROVIDER_API_KEY"], "[REDACTED]")
        self.assertNotIn("sentinel", str(config))
        self.assertEqual(config["MAX_OUTPUT_TOKENS"], 256)

    def test_rejected_values_do_not_leak(self):
        for field, value in [("PROVIDER_API_KEY", ""), ("LOG_LEVEL", "secret-value"),
                             ("MAX_OUTPUT_TOKENS", "secret-value"), ("MAX_OUTPUT_TOKENS", "9999")]:
            with self.subTest(field=field), patch.dict(os.environ, BASE | {field: value}, clear=True):
                with self.assertRaises(ValueError) as error:
                    effective_config()
                self.assertNotIn("secret-value", str(error.exception))

    def test_startup_fails_closed(self):
        stream = io.StringIO()
        with patch.dict(os.environ, BASE | {"PROVIDER_API_KEY": ""}, clear=True), patch("sys.argv", ["app.py"]):
            with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
                self.assertEqual(main(), 2)
        self.assertNotIn("READY", stream.getvalue())
        self.assertNotIn("private-sentinel", stream.getvalue())


if __name__ == "__main__":
    unittest.main()
