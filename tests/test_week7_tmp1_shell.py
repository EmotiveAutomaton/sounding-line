import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from runners.drive.sealed import week7_tmp1_shell as shell


class TMP1ShellTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.table = self.root / "fixture.csv"
        self.schema = {"fixture.csv": (("group", "lower", "upper", "n"),
                                        (("lower", "upper"),), {"group": {"control"}})}

    def test_delivery_files(self):
        content = b"fixture bytes"
        self.table.write_bytes(content)
        manifest = {self.table.name: hashlib.sha256(content).hexdigest()}
        shell.verify_bundle(self.root, manifest)
        for situation in ("changed", "extra", "missing"):
            with self.subTest(situation=situation):
                self.table.write_bytes(content)
                extra = self.root / "extra"
                if situation == "changed":
                    self.table.write_bytes(content + b"!")
                elif situation == "extra":
                    extra.touch()
                else:
                    self.table.unlink()
                with self.assertRaises(ValueError):
                    shell.verify_bundle(self.root, manifest)
                extra.unlink(missing_ok=True)

    def test_constructed_table_contract(self):
        header = "group,lower,upper,n\n"
        self.table.write_text(header + "control,-1,1,11\n", encoding="utf-8")
        shell.check_tables(self.root, self.schema)
        with self.assertRaises(ValueError):
            shell.check_tables(self.root, shell.TP58_TABLES)
        for content in (header, "lower,upper,n\n0,1,12", header + "other,-1,1,11",
                        header + "control,nan,1,11", header + "control,2,1,11",
                        header + "control,0,1,10", header + "control,0,1,11.0",
                        header + "control,0,1,11,extra",
                        header + "control,0,1,11\n" * 2001):
            self.table.write_text(content, encoding="utf-8")
            with self.assertRaises(ValueError):
                shell.check_tables(self.root, self.schema)
        self.table.write_text(header + "control,-1,1,11\n")
        (self.root / "extra.csv").touch()
        with self.assertRaises(ValueError):
            shell.check_tables(self.root, self.schema)

    def test_closed_entry_and_image_conditions(self):
        sysroot = self.root / "sys"
        devroot = self.root / "dev"
        interfaces = sysroot / "class/net"
        (interfaces / "lo").mkdir(parents=True)
        devroot.mkdir()
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}):
            shell.check_image(sysroot, devroot)
            (interfaces / "eth0").mkdir()
            with self.assertRaises(ValueError):
                shell.check_image(sysroot, devroot)
            (interfaces / "eth0").rmdir()
            (devroot / "nvidia0").touch()
            with self.assertRaises(ValueError):
                shell.check_image(sysroot, devroot)
        with patch.object(shell.sys, "platform", "linux"), patch.object(shell, "check_image"):
            self.assertEqual(shell.main(["--check-image"]), 0)
            self.assertEqual(shell.main([]), 21)

    def test_gate_copy_accepts_literal_fixture(self):
        # This is a CSV contract check. It neither defines a TP58 table nor reads text.
        gate = Path(".agent-state/drive-20261115/lattice-20261119/intake/unpacked/"
                    "PREFLIGHT_2026-11-19/spark/sealed_gate.py")
        if not gate.is_file():
            self.skipTest("the curator's local gate copy is unavailable")
        self.table.write_text("group,lower,upper,n\ncontrol,-1,1,11\n", encoding="utf-8")
        shell.check_tables(self.root, self.schema)
        self.assertEqual(subprocess.run([sys.executable, str(gate), str(self.root)],
                                        capture_output=True).returncode, 0)
        self.table.write_text("group,lower,upper,n\ncontrol,-1,1,10\n", encoding="utf-8")
        self.assertNotEqual(subprocess.run([sys.executable, str(gate), str(self.root)],
                                           capture_output=True).returncode, 0)
