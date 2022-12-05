from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="md2anki",
    version="2.7.1",
    author="AnonymerNiklasistanonym",
    description="Convert Markdown formatted documents to anki decks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AnonymerNiklasistanonym/Md2Anki",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=[
        "genanki>=0.13.0",
        "Markdown>=3.4.1",
    ],
    package_data={
        "md2anki": [
            "highlightJs_renderer.js",
            "kaTex_renderer.js",
            "stylesheet.css",
        ],
    },
    entry_points={
        "console_scripts": [
            "md2anki=md2anki:_main",
        ],
    },
    project_urls={
        "Bug Tracker": "https://github.com/AnonymerNiklasistanonym/Md2Anki/issues",
    },
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
