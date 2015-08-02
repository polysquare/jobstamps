# /jobstamps/jobstamp_cmd_main.py
#
# This provides the main entry point for the jobstamp command line utility.
# Everything after "--" is interpreted as a subprocess command.
#
# Use --dependencies to specify a set of dependencies which will cause
# this job to be re-run if they are more recent than this job's last
# invocation
#
# Use --output-files to specify a set of expected output files for this job,
# which will be re-run if any of those files don't exist.
#
# The user may specify --stamp-directory to change the directory in which
# cache files are stored.
#
# See /LICENCE.md for Copyright information
"""Main entry point for the jobstamp command line utility."""

import argparse

import os

import shutil  # suppress(unused-import)

import subprocess

import sys

from jobstamps import jobstamp

import parseshebang

import shutilwhich  # suppress(F401,unused-import)


def _run_cmd(cmd):
    """Run command specified by :cmd: and return stdout, stderr and code."""
    if not os.path.exists(cmd[0]):
        cmd[0] = shutil.which(cmd[0])
        assert cmd[0] is not None

    shebang_parts = parseshebang.parse(cmd[0])

    proc = subprocess.Popen(shebang_parts + cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    return {
        "stdout": stdout,
        "stderr": stderr,
        "code": proc.returncode
    }


def main(argv=None):  # suppress(unused-function)
    """Entry point for jobstamp command.

    This will parse arguments and run the specified command in a subprocess. If
    the command has already been run, then the last captured stdout and
    stderr of the command will be printed on the command line.
    """
    argv = argv or sys.argv

    if "--" not in argv:
        sys.stderr.write("""Must specify command after '--'.\n""")
        return 1

    cmd_index = argv.index("--")
    args, cmd = (argv[1:cmd_index], argv[cmd_index + 1:])

    parser = argparse.ArgumentParser(description="""Cache results from jobs""")
    parser.add_argument("--dependencies",
                        metavar="PATH",
                        nargs="*",
                        help="""A list of paths which, if more recent than """
                             """the last time this job was invoked, will """
                             """cause the job to be re-invoked.""")
    parser.add_argument("--output-files",
                        metavar="PATH",
                        nargs="*",
                        help="""A list of expected output paths form this """
                             """command, which, if they do not exist, will """
                             """cause the job to be re-invoked.""")
    parser.add_argument("--stamp-directory",
                        metavar="DIRECTORY",
                        type=str,
                        help="""A directory to store cached results from """
                             """this command. If a matching invocation is """
                             """used and the files specified in """
                             """--dependencies and --output-files are """
                             """up-to-date, then the cached stdout, stderr """
                             """and return code is used and the command is """
                             """not run again.""")
    parser.add_argument("--use-hashes",
                        action="store_true",
                        help="""Use hash comparison in order to determine """
                             """if dependencies have changed since the last """
                             """invocation of the job. This method is """
                             """slower, but can withstand files being """
                             """copied or moved.""")
    namespace = parser.parse_args(args)
    stamp_directory = namespace.stamp_directory
    if namespace.use_hashes:
        method = jobstamp.HashMethod
    else:
        method = jobstamp.MTimeMethod

    result = jobstamp.run(_run_cmd,
                          cmd,
                          jobstamps_dependencies=namespace.dependencies,
                          jobstamps_output_files=namespace.output_files,
                          jobstamps_cache_output_directory=stamp_directory,
                          jobstamps_method=method)

    sys.stdout.write(result["stdout"].decode())
    sys.stderr.write(result["stderr"].decode())
    return result["code"]
