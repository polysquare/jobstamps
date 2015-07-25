# /setup.py
#
# Installation and setup script for jobstamps
#
# See /LICENCE.md for Copyright information
"""Installation and setup script for jobstamps."""

from setuptools import find_packages, setup

setup(name="jobstamps",
      version="0.0.5",
      description="""Cache output of idempotent jobs.""",
      long_description_markdown_filename="README.md",
      author="Sam Spilsbury",
      author_email="smspillaz@gmail.com",
      classifiers=["Development Status :: 3 - Alpha",
                   "Programming Language :: Python :: 2",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3",
                   "Programming Language :: Python :: 3.1",
                   "Programming Language :: Python :: 3.2",
                   "Programming Language :: Python :: 3.3",
                   "Programming Language :: Python :: 3.4",
                   "Intended Audience :: Developers",
                   "Topic :: Software Development :: Build Tools",
                   "License :: OSI Approved :: MIT License"],
      url="http://github.com/polysquare/jobstamps",
      license="MIT",
      keywords="development",
      packages=find_packages(exclude=["tests"]),
      install_requires=["shutilwhich",
                        "setuptools"],
      extras_require={
          "green": ["testtools",
                    "nose",
                    "nose-parameterized>=0.5.0",
                    "mock",
                    "setuptools-green>=0.0.11",
                    "six"],
          "polysquarelint": ["polysquare-setuptools-lint"],
          "upload": ["setuptools-markdown"]
      },
      entry_points={
          "console_scripts": [
              "jobstamp=jobstamps.jobstamp_cmd_main:main"
          ]
      },
      test_suite="nose.collector",
      zip_safe=True,
      include_package_data=True)
