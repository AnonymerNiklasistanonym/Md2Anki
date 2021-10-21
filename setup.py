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
    packages=find_packages(include=["md2anki.py"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
