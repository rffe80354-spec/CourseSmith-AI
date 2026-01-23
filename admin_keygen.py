#!/usr/bin/env python3
"""
Admin Key Generator - Vendor Tool for Faleovad AI Enterprise.

This script is for the SELLER only to generate tiered license keys for buyers.
Run this script from the command line and enter buyer email addresses.

Tiers:
- Standard ($59): Basic features, no custom branding
- Extended ($249): Full features, custom logo and website support

Features:
- Normal Mode: Enter buyer email to instantly generate Standard license
- God Mode: Enter the master password to access tier selection

Usage:
    python admin_keygen.py
"""

from license_guard import generate_key

# God Mode secret trigger - DO NOT SHARE
GOD_MODE_CODE = "A543278.B543278.Z12345_Faleovad2009"


def print_license(email, tier, license_key):
    """Print the generated license in a formatted box."""
    tier_label = "Extended ($249)" if tier == 'extended' else "Standard ($59)"
    print()
    print("=" * 50)
    print("✓ License Generated Successfully!")
    print("=" * 50)
    print(f"  Email:   {email}")
    print(f"  Tier:    {tier_label}")
    print(f"  Key:     {license_key}")
    print()
    print("  Send this key to the buyer for activation.")
    print("=" * 50)
    print()


def god_mode():
    """God Mode - Full admin access with tier selection."""
    print()
    print("*" * 60)
    print(">>> GOD MODE ACTIVATED - FALEOVAD ADMIN <<<")
    print("*" * 60)
    print()
    
    while True:
        print("-" * 50)
        email = input("Enter REAL Buyer Email (or 'quit' to exit): ").strip()
        
        if email.lower() in ('quit', 'exit', 'q'):
            print("\nExiting God Mode...")
            break
        
        if not email:
            print("Error: Email cannot be empty.")
            continue
        
        if '@' not in email or '.' not in email:
            print("Error: Please enter a valid email address.")
            continue
        
        # Ask for tier selection (God Mode feature)
        print()
        print("Select License Tier:")
        print("  1. Standard ($59)  - No Branding")
        print("  2. Extended ($249) - Full Branding")
        print()
        tier_choice = input("Enter choice (1 or 2): ").strip()
        
        if tier_choice == '1':
            tier = 'standard'
        elif tier_choice == '2':
            tier = 'extended'
        else:
            print("Error: Invalid choice. Please enter 1 or 2.")
            continue
        
        # Generate the license key
        license_key = generate_key(email, tier)
        print_license(email, tier, license_key)


def normal_mode(email):
    """Normal Mode - Instantly generate Standard license for the email."""
    # Generate Standard license immediately
    tier = 'standard'
    license_key = generate_key(email, tier)
    print_license(email, tier, license_key)


def main():
    """Main function for the admin keygen tool."""
    print("=" * 65)
    print("  Faleovad AI Enterprise - License Key Generator")
    print("  Version 1.0.0 (Gold Release)")
    print("  (Vendor Tool - DO NOT DISTRIBUTE)")
    print("=" * 65)
    print()
    
    while True:
        print("-" * 50)
        email_input = input("Enter Buyer Email (or 'quit' to exit): ").strip()
        
        if email_input.lower() in ('quit', 'exit', 'q'):
            print("\nGoodbye!")
            break
        
        if not email_input:
            print("Error: Input cannot be empty.")
            continue
        
        # Check for God Mode trigger
        if email_input == GOD_MODE_CODE:
            god_mode()
            continue
        
        # Normal mode - validate as email and generate Standard license
        if '@' not in email_input or '.' not in email_input:
            print("Error: Please enter a valid email address.")
            continue
        
        normal_mode(email_input)


if __name__ == "__main__":
    main()
