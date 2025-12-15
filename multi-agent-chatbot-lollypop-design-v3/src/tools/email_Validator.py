import re
import socket
import smtplib
import dns.resolver
from typing import Tuple, Optional
from email_validator import validate_email, EmailNotValidError

def validate_email_address(email: str, verify_smtp: bool = False) -> Tuple[bool, str]:
    """
    Validate an email address by checking format, DNS records, and SMTP connection.
    
    Args:
        email (str): Email address to validate
        verify_smtp (bool) : Boolean flag for SMTP connection verification
    
    Returns:
        Tuple[bool, str]: (is_valid, message)
    """
    try:
        # Step 1: Basic format validation
        validate_email(email, check_deliverability=False)
        
        # Step 2: Split email into local part and domain
        local_part, domain = email.split('@')
        
        # Step 3: Check DNS MX records
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_record = str(mx_records[0].exchange)

            # condition added for cases where SMTP validation 
            # added as part of gcp vm deployment. based-https://stackoverflow.com/questions/8640129/resolving-gmail-com-mail-server
            if not verify_smtp:
                if len(mx_records) > 0:
                    return True, "Valid email"
                else:
                    return False, "Not valid email"
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            return False, "Domain does not have MX records"
        
        # Step 4: Verify SMTP connection
        try:
            # Connect to SMTP server
            smtp = smtplib.SMTP(timeout=10)
            smtp.connect(mx_record)
            smtp.helo(socket.getfqdn())
            
            # Start TLS if available
            if smtp.has_extn('starttls'):
                smtp.starttls()
                smtp.helo(socket.getfqdn())
            
            # Try to verify the email
            smtp_from_address = f"verify@{socket.getfqdn()}"
            code, message = smtp.verify(email)
            
            smtp.quit()
            
            if code == 250:
                return True, "Email address is valid and reachable"
            elif code == 251:
                return True, "Email address is valid but user is not local"
            elif code == 252:
                return True, "Email address is valid but cannot verify user"
            else:
                return False, f"Email verification failed with code {code}: {message}"
            
        except (socket.timeout, socket.error, smtplib.SMTPException) as e:
            return False, f"SMTP connection failed: {str(e)}"
            
    except EmailNotValidError as e:
        return False, f"Invalid email format: {str(e)}"
    except Exception as e:
        return False, f"Validation failed: {str(e)}"

def main():
    """
    Main function to demonstrate email validation usage.
    """
    # Example usage
    test_emails = [
        "chickoo193@gmail.com",
        "invalid.email@nonexistentdomain.com",
        "notanemail",
    ]
    
    for email in test_emails:
        print(f"\nValidating {email}:")
        is_valid, message = validate_email_address(email)
        print(f"Valid: {is_valid}")
        print(f"Message: {message}")

if __name__ == "__main__":
    main()