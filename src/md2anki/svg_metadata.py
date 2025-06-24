import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Dict

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)  # Ensure SVG root keeps its xmlns declaration


def add_svg_metadata(svg_path: Path, metadata: Dict) -> None:
    """Adds or replaces <metadata> tag in an SVG file with JSON-encoded metadata."""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Remove existing metadata
    for elem in root.findall(f"{{{SVG_NS}}}metadata"):
        root.remove(elem)

    # Create new metadata element
    metadata_elem = ET.Element(f"{{{SVG_NS}}}metadata")
    metadata_elem.text = json.dumps(metadata)

    # Insert it at the top (after <svg>)
    root.insert(0, metadata_elem)

    # Write back to file
    tree.write(svg_path, encoding="utf-8", xml_declaration=True)


def read_svg_metadata(svg_path: Path) -> Optional[Dict]:
    """Reads JSON-encoded metadata from <metadata> tag in an SVG file, if present."""
    tree = ET.parse(svg_path)
    root = tree.getroot()

    metadata_elem = root.find(f"{{{SVG_NS}}}metadata")
    if metadata_elem is not None and metadata_elem.text:
        try:
            data = json.loads(metadata_elem.text.strip())
            if isinstance(data, dict):
                return data
            # Not a dict
        except json.JSONDecodeError:
            pass  # Invalid JSON metadata

    return None
