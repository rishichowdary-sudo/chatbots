from functools import wraps
from utils.logger_config import logger
from flask import abort, request
import os

def restrict_if_file_not_exists(file_path_template):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            file_path = file_path_template.format(**kwargs)
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                abort(403)  # Not Found
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Custom decorator to restrict access by IP (if needed)
def restrict_domain(allowed_ip):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get the domain from the Host header
            client_domain = request.host
            print(client_domain)
            
            # Allow all if allowed_ip is * or None (for local development)
            if allowed_ip == '*' or allowed_ip is None or allowed_ip == '':
                return func(*args, **kwargs)
            
            # Check if the domain is allowed
            if client_domain != allowed_ip:
                logger.info("Restrict domain decorator: Restricting traffic from- " + str(client_domain))
                abort(403)  # Forbidden access
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
