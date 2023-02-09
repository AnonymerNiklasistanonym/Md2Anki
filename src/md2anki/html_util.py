#!/usr/bin/env python3

# Installed packages
from bs4 import BeautifulSoup


def fix_inline_code_p_tags(html_content: str) -> str:
    """
    Find all p tags that are in front of inline code div tags and add a class to identify them using CSS rules.
    @param html_content: HTML content string
    @return: updated HTML content string
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for inline_code_div in soup.findAll("div", {"class": "highlight_inline"}):
        for inline_code_div_prev in inline_code_div.previous_elements:
            if inline_code_div_prev.name == "p":
                inline_code_div_prev["class"] = inline_code_div_prev.get(
                    "class", []
                ) + ["highlight_inline_next"]
    return str(soup)
