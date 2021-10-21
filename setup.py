from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="md2anki",
    version="2.5.2",
    author="AnonymerNiklasistanonym",
    description="Convert Markdown formatted documents to anki decks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AnonymerNiklasistanonym/Md2Anki",
    project_urls={
        "Bug Tracker": "https://github.com/AnonymerNiklasistanonym/Md2Anki/issues",
    },
    packages=find_packages(),
    py_modules=["md2anki"],
    package_dir={"": "./"},
    package_data={
        "md2anki": [
            "highlightJs_renderer.js",
            "kaTex_renderer.js",
            "stylesheet.css",
        ],
    },
    include_package_data=True,
    license='MIT',
    scripts=["scripts/md2anki.py", "scripts/md2anki"],
    install_requires=[
        "genanki>=0.11.0",
        "Markdown>=3.3.4",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
