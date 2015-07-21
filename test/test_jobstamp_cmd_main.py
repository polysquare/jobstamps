# /test/test_jobstamp_cmd_main.py
#
# Acceptance tests for the jobstamp command.
#
# See /LICENCE.md for Copyright information
"""Acceptance tests for the jobstamp command."""

import os

import stat

from test import testutil

from jobstamps import jobstamp_cmd_main


def run_executable():
    """Run the 'executable' file in PATH with jobstamp."""
    return jobstamp_cmd_main.main(["jobstamp",
                                   "--stamp-directory",
                                   os.getcwd(),
                                   "--",
                                   "executable"])


class TestJobstampMain(testutil.InTemporaryDirectoryTestBase):

    """TestCase for jobstamps module."""

    def __init__(self, *args, **kwargs):
        """Create instance variables for this TestCase."""
        super(TestJobstampMain, self).__init__(*args, **kwargs)
        self._executable_file = None

    def setUp(self):
        """Create executable python file in temp dir and add it to PATH."""
        super(TestJobstampMain, self).setUp()
        self._executable_file = os.path.join(os.getcwd(), "executable")
        with open(self._executable_file, "w"):
            pass

        os.chmod(self._executable_file,
                 os.stat(self._executable_file).st_mode |
                 stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        last_path = os.environ["PATH"]
        os.environ["PATH"] = os.environ["PATH"] + os.pathsep + os.getcwd()

        self.addCleanup(lambda: os.environ.update({"PATH": last_path}))

    def test_require_double_dash(self):
        """Exit with error when -- is not present in command line."""
        with testutil.CapturedOutput():
            self.assertEqual(jobstamp_cmd_main.main(["cmd"]), 1)

    def test_writes_stdout(self):
        """Write subprocess stdout on first run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write("#!/usr/bin/env python\n"
                                  "import sys\n"
                                  "sys.stdout.write(\"stdout\\n\")\n")

        with testutil.CapturedOutput() as captured:
            run_executable()

        self.assertEqual(captured.stdout, "stdout\n")

    def test_writes_stderr(self):
        """Write subprocess stderr on first run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write("#!/usr/bin/env python\n"
                                  "import sys\n"
                                  "sys.stderr.write(\"stderr\\n\")\n")

        with testutil.CapturedOutput() as captured:
            run_executable()

        self.assertEqual(captured.stderr, "stderr\n")

    def test_returncode(self):
        """Return actual return code of subprocess."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write("#!/usr/bin/env python\n"
                                  "import sys\n"
                                  "sys.exit(2)\n")

        with testutil.CapturedOutput():
            self.assertEqual(run_executable(), 2)

    def test_returncode_from_cache(self):
        """Return cached return code of subprocess."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write("#!/usr/bin/env python\n"
                                  "import sys\n"
                                  "sys.exit(2)\n")

        with testutil.CapturedOutput():
            run_executable()
            self.assertEqual(run_executable(), 2)

    def test_writes_stdout_from_cache(self):
        """Write subprocess stdout on cached run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write("#!/usr/bin/env python\n"
                                  "import sys\n"
                                  "sys.stdout.write(\"stdout\\n\")\n")

        with testutil.CapturedOutput():
            run_executable()

        with testutil.CapturedOutput() as captured:
            run_executable()

        self.assertEqual(captured.stdout, "stdout\n")

    def test_writes_stderr_from_cache(self):
        """Write subprocess stderr on cached run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write("#!/usr/bin/env python\n"
                                  "import sys\n"
                                  "sys.stderr.write(\"stderr\\n\")\n")

        with testutil.CapturedOutput():
            run_executable()

        with testutil.CapturedOutput() as captured:
            run_executable()

        self.assertEqual(captured.stderr, "stderr\n")
