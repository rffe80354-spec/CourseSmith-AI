# Keygen GUI Design Documentation

## Overview
The `keygen_gui.py` is a professional CustomTkinter-based GUI tool that replaces the CLI admin keygen tool. It provides a modern, dark-mode interface for generating license keys.

## Visual Design

### Window Specifications
- **Size:** 700x600 pixels (minimum 600x500)
- **Theme:** Dark mode with blue accent colors
- **Layout:** Centered single-column with generous padding (40px margins)

### UI Components

#### 1. Header Section
```
🔑 License Key Generator
(28pt bold, blue accent color)

Admin Tool - Vendor Use Only
(14pt, gray subtitle)
```

#### 2. Email Input Section
```
📧 Buyer Email Address:
(16pt bold label)

[buyer@example.com                    ]
(50px height entry field, 2px border, rounded corners)
```

#### 3. License Tier Selection
```
📋 License Tier:
(16pt bold label)

(•) Standard ($59)         ( ) Extended ($249)
    Basic Features             Full Features + Branding
(Radio buttons with 25px size, 14pt text)
```

#### 4. Generate Button
```
┌─────────────────────────────────────┐
│   🚀 GENERATE LICENSE KEY           │
│   (60px height, 18pt bold)          │
└─────────────────────────────────────┘
(Blue gradient background, rounded corners)
```

#### 5. Result Display
```
🔐 Generated License Key:
(16pt bold label)

[FALEOVAD-EXT-A4B2-C8D6-2026          ]
(50px height, readonly, monospace font)
```

#### 6. Copy Button
```
┌─────────────────────────────────────┐
│   📋 COPY TO CLIPBOARD              │
│   (50px height, 15pt bold)          │
└─────────────────────────────────────┘
(Green gradient background, initially disabled)
```

## Key Features

### 1. Email Validation
- Checks for non-empty input
- Validates basic email format (contains @ and .)
- Shows error messagebox if invalid

### 2. Mock License Generation
- Format: `FALEOVAD-{TIER}-{HASH}-{YEAR}`
  - Standard: `FALEOVAD-STD-XXXX-XXXX-2026`
  - Extended: `FALEOVAD-EXT-XXXX-XXXX-2026`
- Uses SHA-256 hash of email + tier + year for uniqueness
- Deterministic: same email+tier produces same key

### 3. Copy to Clipboard
- One-click copy functionality
- Shows confirmation messagebox
- Button disabled until key is generated

### 4. Success Confirmation
Shows messagebox with:
```
Success

License key generated successfully!

Email: customer@example.com
Tier: Extended

Key: FALEOVAD-EXT-A4B2-C8D6-2026

Send this key to the buyer for activation.
```

## Color Scheme

- **Primary Blue:** #1f6aa5 (light) / #3b8ed0 (dark)
- **Hover Blue:** #1a5a8f / #2f5ba0
- **Success Green:** #28a745 / #20873a
- **Hover Green:** #218838 / #1a6d2e
- **Gray Text:** #888888
- **Border:** #333333 (gray30)

## Spacing Standards (High-End)

- Window padding: 40px all sides
- Frame padding: 30px internal
- Section spacing: 15-25px between elements
- Input heights: 50-60px for premium feel
- Button heights: 50-60px for solid feel

## Code Structure

```python
class KeygenApp(ctk.CTk):
    def __init__(self)
        # Initialize window
        
    def _create_ui(self)
        # Build all UI components
        
    def _generate_key(self)
        # Validate email
        # Get tier
        # Generate key
        # Display result
        # Enable copy button
        
    def _mock_generate_key(email, tier)
        # Mock key generation logic
        # TODO: Replace with real license_guard logic
        
    def _copy_to_clipboard(self)
        # Copy key to clipboard
        # Show confirmation
```

## Integration Notes

### To Connect Real License Generation:

Replace the `_mock_generate_key()` method with:

```python
from license_guard import generate_key

def _generate_key(self):
    """Generate a license key based on email and tier selection."""
    email = self.email_entry.get().strip()
    
    # Validate email
    if not email or '@' not in email or '.' not in email:
        messagebox.showerror("Error", "Please enter a valid email address.")
        return
    
    # Get selected tier
    tier = self.tier_var.get()
    
    # Use real license generation
    license_key = generate_key(email, tier)
    
    # Display result...
    # (rest of the method remains the same)
```

## Usage

Run from command line:
```bash
python keygen_gui.py
```

Or double-click the file in file explorer (if Python is configured for .py files).

## Security Notes

- This is a **vendor-only** tool
- Should NOT be distributed to customers
- Keep in secure location separate from main application
- Consider adding password protection for production use

## Future Enhancements

1. Add password/PIN protection on launch
2. Store generation history in encrypted log
3. Add key validation/verification feature
4. Export keys to CSV for record-keeping
5. Add database integration for key tracking
