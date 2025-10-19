
from django.utils import timezone
from django.db.models import Sum
from django.db.models.functions import Coalesce
import re



def format_bangladeshi_currency(amount):
    """
    Format a numeric value in Bangladeshi Taka (BDT) style with commas and 2 decimal places.

    Example:
        Input: 10000
        Output: "10,000.00"
    """
    if not isinstance(amount, (int, float)):
        raise ValueError("Input must be an integer or float.")
    
    # Convert amount to string with two decimal places
    amount_str = f"{amount:.2f}"
    integer_part, decimal_part = amount_str.split(".")  # Split integer and decimal parts
    
    # Handle Bangladeshi/Indian style grouping
    n = len(integer_part)
    if n <= 3:
        # If the number is 3 digits or less, no special grouping is needed
        formatted_integer = integer_part
    else:
        # Split into last 3 digits and the rest
        last_three = integer_part[-3:]
        other_numbers = integer_part[:-3]
        # Add commas every 2 digits for the rest
        formatted_integer = ",".join(
            [other_numbers[max(i - 2, 0):i] for i in range(len(other_numbers), 0, -2)][::-1]
        ) + "," + last_three
    
    # Combine integer part with the decimal part
    return f"{formatted_integer}.{decimal_part}"





def format_phone_number(phone_number):
    """Formats phone number to +88 XXXX XXXXXX"""

    # Remove any extra characters (like spaces or dashes)
    phone_number = re.sub(r"\D", "", phone_number)  # Keep only digits

    # If number starts with +880, remove +88
    if phone_number.startswith("880") and len(phone_number) == 13:
        phone_number = phone_number[2:]  # Remove '880' (keep 11 digits)

    # Ensure it's exactly 11 digits (Bangladeshi mobile format)
    if len(phone_number) == 11 and phone_number.startswith("01"):
        return f"+88 {phone_number[:5]} {phone_number[5:]}"  

    return phone_number  # Return as is if not valid


