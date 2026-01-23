#!/usr/bin/env python3
"""
Admin Key Generator - Vendor Tool for CourseSmith ENTERPRISE.

This script is for the SELLER only to generate license keys for buyers.
Run this script from the command line and enter buyer email addresses.

Usage:
    python admin_keygen.py
"""

from license_guard import generate_key


def main():
    """Main function for the admin keygen tool."""
    print("=" * 60)
    print("  CourseSmith ENTERPRISE - License Key Generator")
    print("  (Vendor Tool - DO NOT DISTRIBUTE)")
    print("=" * 60)
    print()
    
    while True:
        print("-" * 40)
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
        
        # Generate the license key
        license_key = generate_key(email)
        
        print()
        print("✓ License Generated Successfully!")
        print(f"  Email: {email}")
        print(f"  Key:   {license_key}")
        print()
        print("  Send this key to the buyer for activation.")
        print()


if __name__ == "__main__":
    main()
