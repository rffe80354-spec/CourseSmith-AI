#!/usr/bin/env python3
"""
Admin Key Generator - Vendor Tool for Faleovad AI Enterprise.

This script is for the SELLER only to generate tiered license keys for buyers.
Run this script from the command line and enter buyer email addresses.

Tiers:
- Standard ($59): Basic features, no custom branding
- Extended ($249): Full features, custom logo and website support

Usage:
    python admin_keygen.py
"""

from license_guard import generate_key


def main():
    """Main function for the admin keygen tool."""
    print("=" * 65)
    print("  Faleovad AI Enterprise - License Key Generator")
    print("  (Vendor Tool - DO NOT DISTRIBUTE)")
    print("=" * 65)
    print()
    
    while True:
        print("-" * 50)
        email = input("Enter buyer email (or 'quit' to exit): ").strip()
        
        if email.lower() in ('quit', 'exit', 'q'):
            print("\nGoodbye!")
            break
        
        if not email:
            print("Error: Email cannot be empty.")
            continue
        
        if '@' not in email or '.' not in email:
            print("Error: Please enter a valid email address.")
            continue
        
        # Ask for tier selection
        print()
        print("Select License Tier:")
        print("  1. Standard ($59)  - No Branding")
        print("  2. Extended ($249) - Full Branding")
        print()
        tier_choice = input("Enter choice (1 or 2): ").strip()
        
        if tier_choice == '1':
            tier = 'standard'
            tier_label = "Standard ($59)"
        elif tier_choice == '2':
            tier = 'extended'
            tier_label = "Extended ($249)"
        else:
            print("Error: Invalid choice. Please enter 1 or 2.")
            continue
        
        # Generate the license key
        license_key = generate_key(email, tier)
        
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


if __name__ == "__main__":
    main()
