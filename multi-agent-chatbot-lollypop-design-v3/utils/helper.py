import yaml
import bleach

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


