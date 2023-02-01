from bs4 import BeautifulSoup, Tag


def fix_inline_code_p_tags(html_content: str) -> str:
    """
    Find all p tags that are in front of inline code div tags and add a class to identify them using CSS rules.
    @param html_content: HTML content string
    @return: updated HTML content string
    """
    soup = BeautifulSoup(html_content, "html.parser")
    for inline_code_div in soup.findAll("div", {"class": "highlight_inline"}):
        inline_code_div: Tag = inline_code_div
        for inline_code_div_prev in inline_code_div.previous_elements:
            inline_code_div_prev: Tag = inline_code_div_prev
            if inline_code_div_prev.name == "p":
                inline_code_div_prev["class"] = inline_code_div_prev.get(
                    "class", []
                ) + ["highlight_inline_next"]
    return str(soup)
