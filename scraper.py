from playwright.sync_api import sync_playwright
import re
from unidecode import unidecode

def get_element_text(url: str, selector: str) -> str:
    """Fetches the text content of an HTML element from a web page.

    Args:
        url (str): The URL of the web page.
        selector (str): The CSS selector of the element.

    Returns:
        str: The text content of the element.

    Raises:
        ValueError: If the element is not found.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)

        element = page.query_selector(selector)
        if element is None:
            browser.close()
            raise ValueError("Element not found")

        text = element.inner_text()
        text = normalize_text(text)
        browser.close()
        return text
        
def normalize_text(text: str) -> str:
    """Removes diacritics, special characters, and replaces whitespaces with dashes.

    Args:
        text (str): Input string.

    Returns:
        str: Normalized string.
    """
    text = unidecode(text)  # Remove diacritics (e.g., "č" -> "c", "é" -> "e")
    text = re.sub(r"[^\w\s]", "", text)  # Remove special characters (dots, commas, etc.)
    text = re.sub(r"\s+", "-", text.strip())  # Replace whitespaces with dashes
    return text.lower()  # Convert to lowercase (optional)