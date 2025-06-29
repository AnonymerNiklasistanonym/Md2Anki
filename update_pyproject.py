#!/usr/bin/env python3

import sys
import re
from tomlkit import parse, dumps, document, table, inline_table, array
from pathlib import Path

# Append the module path for md2anki
sys.path.append(str(Path(__file__).parent.joinpath("src")))

# Import project metadata from your module
from md2anki.info.general import (
    MD2ANKI_NAME,
    MD2ANKI_VERSION,
    MD2ANKI_AUTHOR,
    MD2ANKI_DESCRIPTION,
    MD2ANKI_URL,
    MD2ANKI_URL_BUG_TRACKER,
    MD2ANKI_URL_SOURCE_CODE,
)
from md2anki.info.files import (
    RELATIVE_RES_CSS_FILE_PATH,
    RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER,
    RELATIVE_RES_CSS_FILE_PATH_TYPE_CLOZE,
)

pyproject_path = Path("pyproject.toml")
requirements_path = Path("requirements.txt")


def auto_comment(source: str, prefix="md2anki.info.general."):
    return f"Automatically generated from {prefix}{source}"


def parse_requirements_txt(filepath: Path, filter_names=None):
    """
    Parse requirements.txt and return a list of dependencies.
    If filter_names is provided (set or list), only include dependencies with those names.
    """
    dependencies = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Extract the package name from the line (before any version specifiers or extras)
            # Handles patterns like: package[extra]==1.2.3, package>=1.0, package
            match = re.match(r"^([a-zA-Z0-9_.+-]+)", line)
            if not match:
                continue
            name = match.group(1)

            if filter_names is None or name.lower() in filter_names:
                dependencies.append(line)

    return dependencies


# Main method
if __name__ == "__main__":
    if not pyproject_path.exists():
        raise FileNotFoundError(f"{pyproject_path} does not exist.")

    if not requirements_path.exists():
        raise FileNotFoundError(f"{requirements_path} does not exist.")

    deps = parse_requirements_txt(
        requirements_path,
        filter_names={"beautifulsoup4", "genanki", "markdown", "pygments"},
    )

    # Read existing TOML
    with pyproject_path.open("rb") as f:
        pyproject = parse(pyproject_path.read_text(encoding="utf-8"))

    # ---- [project] ----
    project = pyproject.get("project", table())
    project["name"] = MD2ANKI_NAME
    project["name"].comment(auto_comment("MD2ANKI_NAME"))
    project["version"] = str(MD2ANKI_VERSION)
    project["version"].comment(auto_comment("MD2ANKI_VERSION"))
    project["description"] = MD2ANKI_DESCRIPTION
    project["description"].comment(auto_comment("MD2ANKI_DESCRIPTION"))
    project["dependencies"] = [dep.replace("==", ">=") for dep in deps]
    project["dependencies"].comment(auto_comment("requirements.txt", prefix=""))

    # ---- [project.authors] ----
    authors_table = inline_table()
    authors_table["name"] = MD2ANKI_AUTHOR
    project["authors"] = [authors_table]
    # comment not possible?

    # ---- [project.urls] ----
    urls = project.get("urls", table())
    urls["Homepage"] = MD2ANKI_URL
    urls["Homepage"].comment(auto_comment("MD2ANKI_URL"))
    urls["Bug Tracker"] = MD2ANKI_URL_BUG_TRACKER
    urls["Bug Tracker"].comment(auto_comment("MD2ANKI_URL_BUG_TRACKER"))
    urls["Source"] = MD2ANKI_URL_SOURCE_CODE
    urls["Source"].comment(auto_comment("MD2ANKI_URL_SOURCE_CODE"))
    project["urls"] = urls

    # ---- [project.scripts] ----
    scripts = project.get("scripts", table())
    scripts[MD2ANKI_NAME] = f"{MD2ANKI_NAME}:_main"
    scripts[MD2ANKI_NAME].comment(auto_comment("MD2ANKI_NAME"))
    project["scripts"] = scripts

    pyproject["project"] = project

    # ---- [tool.setuptools.package-data] ----
    tool = pyproject.get("tool", table())
    setuptools = tool.get("setuptools", table())
    package_data = setuptools.get("package-data", table())
    package_data[MD2ANKI_NAME] = [
        str(RELATIVE_RES_CSS_FILE_PATH),
        str(RELATIVE_RES_CSS_FILE_PATH_TYPE_ANSWER),
        str(RELATIVE_RES_CSS_FILE_PATH_TYPE_CLOZE),
    ]
    package_data[MD2ANKI_NAME].comment(auto_comment("*", prefix="md2anki.info.files."))
    setuptools["package-data"] = package_data

    tool["setuptools"] = setuptools
    pyproject["tool"] = tool

    # ---- Write file ----
    content = re.sub(r"\n{3,}", "\n\n", dumps(pyproject)).rstrip() + "\n"
    pyproject_path.write_text(content, encoding="utf-8")
