import sys
from pathlib import Path
from setuptools import setup, find_packages

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.joinpath("src", "md2anki")))

from info import (
    md2anki_version,
    md2anki_name,
    md2anki_author,
    md2anki_description,
    md2anki_url,
    md2anki_url_bug_tracker,
    RELATIVE_CSS_FILE_PATH,
    RELATIVE_CSS_FILE_PATH_TYPE_ANSWER,
)

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()


setup(
    name=md2anki_name,
    version=str(md2anki_version),
    author=md2anki_author,
    description=md2anki_description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=md2anki_url,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "beautifulsoup4>=4.11.2",
        "genanki>=0.13.0",
        "Markdown>=3.4.1",
        "Pygments>=2.14.0",
    ],
    package_data={
        md2anki_name: [
            RELATIVE_CSS_FILE_PATH,
            RELATIVE_CSS_FILE_PATH_TYPE_ANSWER,
        ],
    },
    entry_points={
        "console_scripts": [
            f"{md2anki_name}={md2anki_name}:_main",
        ],
    },
    project_urls={
        "Bug Tracker": md2anki_url_bug_tracker,
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
