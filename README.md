# Jobstamps

Make-like caching of idempotent functions for python.

This module provides memoization of long-running functions which have clearly
documented side effects and do not change their result if their inputs
have not changed. It is ideal for tools which analyze text files to produce
some output, such as a source code linter. The result of a the function
is stored in a file which is named by the hash of the function's
arguments.

A separate `jobstamp` command line utility is provided for integration
with shell scripts or non-python commands. This utility caches the
standard input, output and error of command line invocation and upon
running that utility with the same arguments, the cached output
is printed and return code returned.

## Status

| Travis CI (Ubuntu) | AppVeyor (Windows) | Coverage | PyPI | Licence |
|--------------------|--------------------|----------|------|---------|
|[![Travis](https://img.shields.io/travis/polysquare/jobstamps.svg)](http://travis-ci.org/polysquare/jobstamps)|[![AppVeyor](https://img.shields.io/appveyor/ci/smspillaz/jobstamps.svg)](https://ci.appveyor.com/project/smspillaz/jobstamps)|[![Coveralls](https://img.shields.io/coveralls/polysquare/jobstamps.svg)](http://coveralls.io/polysquare/jobstamps)|[![PyPIVersion](https://img.shields.io/pypi/v/jobstamps.svg)](https://pypi.python.org/pypi/jobstamps)[![PyPIPythons](https://img.shields.io/pypi/pyversions/jobstamps.svg)](https://pypi.python.org/pypi/jobstamps)|[![License](https://img.shields.io/github/license/polysquare/jobstamps.svg)](http://github.com/polysquare/jobstamps)|

## Usage

    usage: jobstamp [-h] [--dependencies [PATH [PATH ...]]]
                    [--output-files [PATH [PATH ...]]]
                    [--stamp-directory DIRECTORY] [--use-hashes]

    Cache results from jobs

    optional arguments:
      -h, --help            show this help message and exit
      --dependencies [PATH [PATH ...]]
                            A list of paths which, if more recent than the last
                            time this job was invoked, will cause the job to be
                            re-invoked.
      --output-files [PATH [PATH ...]]
                            A list of expected output paths form this command,
                            which, if they do not exist, will cause the job to
                            be re-invoked.
      --stamp-directory DIRECTORY
                            A directory to store cached results from this
                            command.
                            If a matching invocation is used and the files
                            specified in --dependencies and --output-files are
                            up-to-date, then the cached stdout, stderr and
                            return code is used and the command is not run
                            again.
      --use-hashes          Use hash comparison in order to determine if
                            dependencies have changed since the last invocation
                            of the job. This method is slower, but can
                            withstand files being copied or moved.

## API Usage

Python modules can integrate directly with the jobstamp API, which is
exposed as so:

    jobstamp.run(func, *args, **kwargs)

The default signature allows for the specified function to be applied to
the specified args and kwargs. The result of the function will be cached
(so long as it can be represented in text form and parsed from its
__repr__) in a stamp file in the temporary files directory. The next time
the function is invoked through the `jobstamp` wrapper with the same arguments,
the result from the stampfile will be loaded and returned directly.

If you want to check if a function will be run again without actually running
it, then, you can use the `out_of_date` function. That function returns
either `None` or any file which would, by virtue of being out of date,
cause the job to be re-run.

    out_of_date(func, *args, **kwargs)

Certain `kwargs` have special meanings and will be parsed and removed
from the `kwargs` passed to the underlying function. Those are:

- `jobstamps_dependencies`: A list of files for which this function depends
                            on to produce its output. If any of these files
                            have been updated since the last invocation, the
                            function will be run again.
- `jobstamps_output_files`: A list of files for which this function produces
                            as a side-effect. If any of these files don't
                            exist, the job gets run again.
- `jobstamps_cache_output_directory`: Where to store internal cached
                                      invocation stamps. Usually this
                                      should be specified on a per-domain
                                      basis to avoid clashes stamps in the
                                      global temporary files directory.
- `jobstamps_method`: Either one of `jobstamp.HashMethod` or
                      `jobstamp.MTimeMethod`, defaulting to the latter if
                      left unspecified. This option allows the user to pick
                      the implementation of determining whether a dependency
                      is out of date. `jobstamp.MTimeMethod` uses the
                      file-system modification time to determine if a
                      dependency is more recent than the last run of the
                      function. `jobstamp.HashMethod` uses the SHA1 algorithm
                      to store a hash of the file and compares the hash on
                      the next invocation. It is slower than
                      `jobstamp.MTimeMethod` but handles cases where files
                      are copied or otherwise saved and restored between
                      invocations.

## Influential environment variables

Specify `JOBSTAMPS_DISABLED` to always disable caching of jobs on all
invocations. Jobs will always be re-run, but existing stamp files
won't be removed.

Specify `JOBSTAMPS_DEBUG` to see when a job was re-run or a cached
value was used.

Specify `JOBSTAMPS_ALWAYS_USE_HASHES` to force any underlying jobstamp
library to use `jobstamp.HashMethod` instead of `jobstamp.MTimeMethod`, even
if the user explicitly asked for the latter. This is useful for CI environments
where the latter method almost never works the way one would expect it to.

