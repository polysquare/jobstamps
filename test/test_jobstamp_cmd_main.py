# /test/test_jobstamp_cmd_main.py
#
# Acceptance tests for the jobstamp command.
#
# See /LICENCE.md for Copyright information
"""Acceptance tests for the jobstamp command."""

import os

import shutil

import stat

from test import testutil

from jobstamps import jobstamp_cmd_main

from nose_parameterized import param, parameterized

import shutilwhich  # suppress(F401,unused-import)


def run_executable(*args):
    """Run the 'executable' file in PATH with jobstamp."""
    return jobstamp_cmd_main.main([
        "jobstamp",
        "--stamp-directory",
        os.getcwd()
    ] + list(args) + ["--", "executable"])


def _flag_doc(func, num, params):
    """Format docstring for tests with extra flags if necessary."""
    del num

    flags = params[0][0]
    if len(flags):
        return func.__doc__[:-1] + """ with flags {}""".format(" ".join(flags))

    return func.__doc__


_PYTHON_SHEBANG = "#!{}\n".format(shutil.which("python"))


class TestJobstampMain(testutil.InTemporaryDirectoryTestBase):

    """TestCase for jobstamps module."""

    def __init__(self, *args, **kwargs):
        """Create instance variables for this TestCase."""
        super(TestJobstampMain, self).__init__(*args, **kwargs)
        self._executable_file = None

    _FLAGS = (param(["--use-hashes"]), param([]))

    def setUp(self):  # suppress(N802)
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

        # Unset the JOBSTAMPS_ALWAYS_USE_HASHES variable if it is
        # set and add a cleanup task to re-set it later. We don't want to
        # keep that variable during tests because it will the
        # mtime code paths to remain untested.
        always_use_hashes_var = "JOBSTAMPS_ALWAYS_USE_HASHES"
        testutil.temporarily_clear_variable_on_testsuite(self,
                                                         always_use_hashes_var)

    def test_require_double_dash(self):
        """Exit with error when -- is not present in command line."""
        with testutil.CapturedOutput():
            self.assertEqual(jobstamp_cmd_main.main(["cmd"]), 1)

    def test_run_binary_executable(self):
        """Run a binary executable."""
        result = jobstamp_cmd_main.main([
            "jobstamp",
            "--",
            "python",
            "-c",
            "import sys; sys.exit(0)"
        ])
        self.assertEqual(result, 0)

    @parameterized.expand(_FLAGS, testcase_func_doc=_flag_doc)
    def test_writes_stdout(self, flags):
        """Write subprocess stdout on first run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write(_PYTHON_SHEBANG +
                                  "import sys\n"
                                  "sys.stdout.write(\"stdout\\n\")\n")

        with testutil.CapturedOutput() as captured:
            run_executable(*flags)

        self.assertEqual(captured.stdout.replace("\r\n", "\n"), "stdout\n")

    @parameterized.expand(_FLAGS, testcase_func_doc=_flag_doc)
    def test_writes_stderr(self, flags):
        """Write subprocess stderr on first run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write(_PYTHON_SHEBANG +
                                  "import sys\n"
                                  "sys.stderr.write(\"stderr\\n\")\n")

        with testutil.CapturedOutput() as captured:
            run_executable(*flags)

        self.assertEqual(captured.stderr.replace("\r\n", "\n"), "stderr\n")

    @parameterized.expand(_FLAGS, testcase_func_doc=_flag_doc)
    def test_returncode(self, flags):
        """Return actual return code of subprocess."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write(_PYTHON_SHEBANG +
                                  "import sys\n"
                                  "sys.exit(2)\n")

        with testutil.CapturedOutput():
            self.assertEqual(run_executable(*flags), 2)

    @parameterized.expand(_FLAGS, testcase_func_doc=_flag_doc)
    def test_returncode_from_cache(self, flags):
        """Return cached return code of subprocess."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write(_PYTHON_SHEBANG +
                                  "import sys\n"
                                  "sys.exit(2)\n")

        with testutil.CapturedOutput():
            run_executable(*flags)
            self.assertEqual(run_executable(*flags), 2)

    @parameterized.expand(_FLAGS, testcase_func_doc=_flag_doc)
    def test_writes_stdout_from_cache(self, flags):
        """Write subprocess stdout on cached run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write(_PYTHON_SHEBANG +
                                  "import sys\n"
                                  "sys.stdout.write(\"stdout\\n\")\n")

        with testutil.CapturedOutput():
            run_executable(*flags)

        with testutil.CapturedOutput() as captured:
            run_executable(*flags)

        self.assertEqual(captured.stdout.replace("\r\n", "\n"), "stdout\n")

    @parameterized.expand(_FLAGS, testcase_func_doc=_flag_doc)
    def test_writes_stderr_from_cache(self, flags):
        """Write subprocess stderr on cached run of jobstamp."""
        with open(self._executable_file, "w") as executable_file:
            executable_file.write(_PYTHON_SHEBANG +
                                  "import sys\n"
                                  "sys.stderr.write(\"stderr\\n\")\n")

        with testutil.CapturedOutput():
            run_executable(*flags)

        with testutil.CapturedOutput() as captured:
            run_executable(*flags)

        self.assertEqual(captured.stderr.replace("\r\n", "\n"), "stderr\n")
