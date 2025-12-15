import re
import yaml
import bleach
from bs4 import BeautifulSoup

def load_client_properties(client):
    """
    Load the properties for the given client. Returns a key value pair of property name and properties.
    """
    with open("client_properties.yaml") as file:
        client_properties = yaml.safe_load(file)
        client_properties = client_properties[client]
    return client_properties


def load_application_properties():
    """
    Load the application properties.
    """
    with open("application_properties.yaml") as file:
        application_properties = yaml.safe_load(file)
    return application_properties


def sanitize_input(input_value):
    if input_value is None:
        return None
    # Allow only safe HTML tags and attributes (if needed)
    allowed_tags = []  # Empty list means no HTML tags are allowed
    allowed_attributes = {}  # Empty dict means no attributes are allowed
    return bleach.clean(input_value, tags=allowed_tags, attributes=allowed_attributes)

def bs4_extractor(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    
    body = soup.body or soup
    header = body.find("header")
    if header:                            # uncommenting this will eliminate header from the extracted content
        header.decompose()
    
    # Remove footers, mob-footrs from main
    main = body.find("main") or body
    for div in main.find_all("div", class_="mob-footer"):
        div.decompose()
    
    selectors = ["style", "script", "footer"]
    for tag_name in selectors:
        for tag in main.find_all(tag_name):
            tag.decompose()
    
    # Remove footers, mob-footers from body
    for div in body.find_all("div", class_="mob-footer"):
        div.decompose()
    
    selectors = ["style", "script", "footer"]
    for tag_name in selectors:
        for tag in body.find_all(tag_name):
            tag.decompose()
    
    raw_text = body.get_text(separator="\n")
    return re.sub(r"\n\n+", "\n\n", raw_text).strip()


