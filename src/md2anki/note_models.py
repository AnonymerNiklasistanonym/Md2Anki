#!/usr/bin/env python3

# Internal packages
import os.path
import urllib.request

# Local modules
from md2anki.anki_deck import AnkiModel

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
CSS_GENERAL_FILE_PATH = os.path.join(CURRENT_DIR, "stylesheet.css")
HIGHLIGHTJS_SCRIPT_FILE_PATH = os.path.join(CURRENT_DIR, "highlightJs_renderer.js")
KATEXT_FILE_SCRIPT_PATH = os.path.join(CURRENT_DIR, "kaTex_renderer.js")

HLJS_VERSION = "11.7.0"
HLJS_CSS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{HLJS_VERSION}/styles/default.min.css"
HLJS_CSS_FILE_NAME = f"highlight_{HLJS_VERSION}.min.css"
HLJS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/highlight.js/{HLJS_VERSION}/highlight.min.js"
HLJS_FILE_NAME = f"highlight_{HLJS_VERSION}.min.js"

KATEX_VERSION = "0.16.4"
KATEX_CSS_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.css"
KATEX_CSS_FILE_NAME = f"katex_{KATEX_VERSION}.min.css"
KATEX_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/katex.min.js"
KATEX_FILE_NAME = f"katex_{KATEX_VERSION}.min.js"
KATEX_AUTO_RENDERER_URL = f"https://cdn.jsdelivr.net/npm/katex@{KATEX_VERSION}/dist/contrib/auto-render.min.js"
KATEX_AUTO_RENDERER_FILE_NAME = f"katex_auto_render_{KATEX_VERSION}.min.js"


def download_script_files(
    dir_path: str = os.path.join(CURRENT_DIR, "temp"),
    skip_download_if_existing: bool = True,
):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    if (
        not os.path.isfile(os.path.join(dir_path, HLJS_CSS_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(
            HLJS_CSS_URL, os.path.join(dir_path, HLJS_CSS_FILE_NAME)
        )
    if (
        not os.path.isfile(os.path.join(dir_path, HLJS_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(HLJS_URL, os.path.join(dir_path, HLJS_FILE_NAME))
    if (
        not os.path.isfile(os.path.join(dir_path, KATEX_CSS_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(
            KATEX_CSS_URL, os.path.join(dir_path, KATEX_CSS_FILE_NAME)
        )
    if (
        not os.path.isfile(os.path.join(dir_path, KATEX_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(KATEX_URL, os.path.join(dir_path, KATEX_FILE_NAME))
    if (
        not os.path.isfile(os.path.join(dir_path, KATEX_AUTO_RENDERER_FILE_NAME))
        or not skip_download_if_existing
    ):
        urllib.request.urlretrieve(
            KATEX_AUTO_RENDERER_URL,
            os.path.join(dir_path, KATEX_AUTO_RENDERER_FILE_NAME),
        )


def create_type_answer_anki_deck_model() -> AnkiModel:
    return AnkiModel(
        guid=999991000,
        name=f"Md2Anki type answer card",
        description="Type in the answer",
        css=".card {"
        "  font-family: arial;"
        "  font-size: 20px;"
        "  text-align: center;"
        "  color: black;"
        "  background-color: white;"
        "}",
        template_card_question="{{Question}}\n\n{{type:Answer}}",
        template_card_separator='{{Question}}\n\n<hr id="answer">\n\n',
        template_card_answer="{{type:Answer}}",
    )


def create_katex_highlightjs_anki_deck_model(
    dir_path: str = os.path.join(CURRENT_DIR, "temp"),
    skip_download_if_existing: bool = True,
    online: bool = True,
    debug=False,
) -> AnkiModel:
    if online:
        katex_css_code = (
            f'<link rel="stylesheet" href="{KATEX_CSS_URL}" crossorigin="anonymous">\n'
        )
        katex_js_code = (
            f'<script src="{KATEX_URL}" crossorigin="anonymous"></script>\n'
            f'<script src="{KATEX_AUTO_RENDERER_URL}" crossorigin="anonymous"></script>\n'
        )
        highlightjs_css_code = (
            f'<link rel="stylesheet" href="{HLJS_CSS_URL}" crossorigin="anonymous">\n'
        )
        highlightjs_js_code = (
            f'<script src="{HLJS_URL}" crossorigin="anonymous"></script>\n'
        )
    else:
        download_script_files(
            dir_path=dir_path, skip_download_if_existing=skip_download_if_existing
        )
        katex_css_code = ""
        katex_js_code = ""
        highlightjs_css_code = ""
        highlightjs_js_code = ""
        # Get source code to highlighting source code
        with open(
            os.path.join(dir_path, HLJS_CSS_FILE_NAME), "r"
        ) as highlightjs_css_file:
            highlightjs_css_code += highlightjs_css_file.read()
        with open(os.path.join(dir_path, HLJS_FILE_NAME), "r") as hljs_script_file:
            highlightjs_js_code += f"\n<script>\n{hljs_script_file.read()}\n</script>"

        # Get source code to render LaTeX math code
        with open(os.path.join(dir_path, KATEX_CSS_FILE_NAME), "r") as katex_css_file:
            katex_css_code += katex_css_file.read()
        with open(os.path.join(dir_path, KATEX_FILE_NAME), "r") as katex_file:
            katex_js_code += f"\n<script>\n{katex_file.read()}\n</script>"
        with open(
            os.path.join(dir_path, KATEX_AUTO_RENDERER_FILE_NAME), "r"
        ) as katex_auto_renderer_file:
            katex_js_code += f"\n<script>\n{katex_auto_renderer_file.read()}\n</script>"

    with open(CSS_GENERAL_FILE_PATH, "r") as cssFile:
        css_code = cssFile.read()
    with open(HIGHLIGHTJS_SCRIPT_FILE_PATH, "r") as highlightjs_script_file:
        highlightjs_js_code += (
            f"\n<script>\n{highlightjs_script_file.read()}\n</script>"
        )
    with open(KATEXT_FILE_SCRIPT_PATH, "r") as katex_file:
        katex_js_code += f"\n<script>\n{katex_file.read()}\n</script>"

    if debug:
        print(f"> {katex_js_code=!r}, {highlightjs_js_code=!r}")
        print(f"> {katex_css_code=!r}, {highlightjs_css_code=!r} {css_code=!r}")

    online_state = "online" if online else "offline"
    return AnkiModel(
        guid=999990002,
        name=f"Md2Anki card (KaTeX {KATEX_VERSION}, HighlightJs {HLJS_VERSION}, {online_state})",
        description="Card with integrated KaTeX and HighlightJs support",
        css=katex_css_code + highlightjs_css_code + css_code,
        js=katex_js_code + highlightjs_js_code,
    )
