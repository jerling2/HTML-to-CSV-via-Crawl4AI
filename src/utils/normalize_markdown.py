import re

def normalize_markdown(markdown):
    """
    Strips excessive whitespace and compacts markdown text.
    """
    text = markdown.strip()                     # Remove leading/trailing whitespace
    text = re.sub(r'\r\n?', '\n', text)         # Normalize line endings
    text = re.sub(r'\n\s*\n', '\n', text)       # Collapse multiple blank lines
    text = re.sub(r'[ \t]+', ' ', text)         # Collapse multiple spaces/tabs
    text = re.sub(r'\n+', '\n', text)           # Collapse multiple newlines again
    text = text.strip()
    return text