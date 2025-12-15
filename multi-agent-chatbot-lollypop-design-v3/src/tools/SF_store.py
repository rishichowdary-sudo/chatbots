import requests
import json
from utils.logger_config import logger
import os

# Salesforce Web-to-Lead Endpoint
SF_URL = os.getenv("SF_URL")
SF_OID = os.getenv("SF_OID")



def extract_company_name(company_info: str):
    for line in company_info.splitlines():
        if line.startswith("Company Name:"):
            return line.split(":", 1)[1].strip()
    return "Unknown"


def split_name(full_name: str):
    """
    Split full name into first and last name.
    If only one name is present, last_name = 'NA'
    """
    if not full_name:
        return "Unknown", "NA"

    parts = full_name.strip().split()
    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else "NA"
    return first_name, last_name



def send_project_enquiry_to_salesforce(enquiry: dict):
    """
    Send project enquiry as Salesforce Lead.
    enquiry dict must include:
    - name
    - email
    - summary (conversation summary)
    - company_info (dict OR JSON string with company_name)
    - category
    """
    try:
        # --- Parse Name ---
        first_name, last_name = split_name(enquiry.get("name", ""))

        # --- Email & Company ---
        email = enquiry.get("email", "")
        company_info_from_db = enquiry.get('company_info','N/A')
        company_name = extract_company_name(company_info_from_db)

        # --- Other fields ---
        description = enquiry.get("summary", "")
        category = enquiry.get("category", "Uncategorized")
        LeadSourceDomain = "lollypop.design"

        # --- Salesforce Web-to-Lead Mappings ---
        data = {
            "oid": SF_OID,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "company": company_name,              # Derived from domain
            "00NQU000002jcnx": company_info_from_db,    # Custom Field: Company Information
            "description": description,                 # Conversation summary
            "00NQU000002jcsn": category,
            "00NKj00000ij80x":LeadSourceDomain,                # Custom Field: Category
        }

        # --- Send request ---
        response = requests.post(SF_URL, data=data, timeout=10)

        if response.status_code == 200:
            if "Thank" in response.text or "success" in response.text.lower():
                logger.info(f"[Salesforce] Lead created successfully for {email}")
                return {"status": "success"}
            else:
                logger.warning(f"[Salesforce] Unclear response for {email}: {response.text[:200]}")
                return {"status": "warning", "reason": response.text[:500]}
        else:
            logger.error(f"[Salesforce] Failed for {email}. Status {response.status_code}: {response.text}")
            return {"status": "error", "reason": response.text}

    except Exception as e:
        logger.exception(f"[Salesforce] Exception while sending lead: {e}")
        return {"status": "error", "reason": str(e)}
