# Faleovad AI Enterprise

A professional desktop application for generating educational PDF books using AI. Built with Python, customtkinter, OpenAI GPT-4o, and ReportLab.

## 🚀 NEW: CourseSmith Ultimate Engine

The **CourseSmith Ultimate Engine** is a powerful educational course generator that creates professional, multi-format courses from a single instruction.

**Key Features:**
- 🌍 **Multi-Language Support**: Automatic English/Russian detection with full Cyrillic support
- 📚 **10-Chapter Structure**: Logical progression from basics to advanced topics
- ✍️ **Expert Content**: ~1500 characters per chapter with markdown formatting
- 📝 **Structured Output**: Easy conversion to PDF, DOCX, and EPUB
- 🎯 **UTF-8 Clean**: Perfect encoding without rendering errors

**Quick Start:**
```python
from coursesmith_engine import generate_course_from_instruction

output = generate_course_from_instruction("Machine Learning Fundamentals")
print(output)
```

📖 **[Read the full documentation →](COURSESMITH_ENGINE_README.md)**

## 💰 License Tiers

Faleovad AI Enterprise features a tiered licensing system:

| Feature | Standard ($59) | Extended ($249) |
|---------|----------------|-----------------|
| Generate Courses | ✅ | ✅ |
| AI Chapter Writing | ✅ | ✅ |
| PDF Export | ✅ | ✅ |
| DALL-E 3 Covers | ✅ | ✅ |
| Custom Logo | ❌ | ✅ |
| Custom Website URL | ❌ | ✅ |

## 🔐 License Activation

Faleovad AI Enterprise requires a valid license to operate. On first launch, you'll see the activation screen.

### For Users
1. Enter your registered email address
2. Enter your license key (format: `STD-XXXX-XXXX-XXXX` or `EXT-XXXX-XXXX-XXXX`)
3. Click "Activate License"

### For Administrators (Key Generation)
Use the admin keygen tool to generate license keys for buyers:

```bash
python admin_keygen.py
```

Enter the buyer's email address when prompted, then select the tier:
- **1. Standard ($59)** - No custom branding
- **2. Extended ($249)** - Full branding support

The tool will output a license key to send to the customer.

#### Admin Note (God Mode)
The keygen tool supports a special "God Mode" for administrators. Enter the **Master Password** instead of an email to access tier selection. Contact the developer for the master password.

- **Normal Mode**: Enter any buyer email → Instantly generates **Standard** license
- **God Mode**: Enter master password → Unlocks tier selection (Standard/Extended)

## ⚙️ OpenAI API Key Setup

Faleovad AI Enterprise requires an OpenAI API key to generate content.

### Method 1: Settings Dialog (Recommended)
1. After activation, click the **⚙️ Settings** button in the header
2. Enter your OpenAI API key
3. Click "Save API Key"

### Method 2: Manual Configuration
Create a `.env` file in the application directory:

```
OPENAI_API_KEY=sk-your-api-key-here
```

## 📦 Installation

### Requirements
- Python 3.9+
- OpenAI API key with GPT-4o and DALL-E 3 access

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Compile to EXE (Windows)
```bash
# Install PyInstaller
pip install pyinstaller

# Build standalone executable
pyinstaller --onefile --windowed --name "FaleovadAI" main.py
```

## 🚀 Usage

### Wizard Workflow

1. **Setup Tab**: Enter your course topic and target audience
   - **Extended License**: Also add your custom logo and website URL for PDF branding

2. **Blueprint Tab**: Generate an AI-powered course outline, then edit the chapter titles as needed

3. **Drafting Tab**: Start the AI writing process - watch the **Live Typewriter Preview** as each chapter is generated in real-time on a paper-like white background

4. **Export Tab**: Generate a DALL-E 3 cover image and build your final professional PDF

## 📂 Project Structure

```
Faleovad-AI/
├── main.py              # Application entry point
├── app.py               # Main GUI application
├── license_guard.py     # DRM license validation (tiered)
├── session_manager.py   # Session token + tier management
├── ai_worker.py         # Threaded AI operations with streaming
├── ai_manager.py        # OpenAI API client
├── pdf_engine.py        # PDF generation with tier-based branding
├── project_manager.py   # Project data model
├── admin_keygen.py      # License key generator (admin tool)
├── utils.py             # Utility functions + Right-Click menu
├── requirements.txt     # Python dependencies
└── .env                 # API key configuration (create this)
```

## 🔒 Security Architecture

Faleovad AI Enterprise implements a **Session Token** system for anti-tamper protection:

1. When the license is validated, a unique session token is generated along with the tier
2. The `ai_worker` and `pdf_engine` modules require this token to function
3. The `pdf_engine` enforces tier-based branding restrictions:
   - **Standard**: Logo and website URL are forced to None
   - **Extended**: Full branding customization allowed
4. If the license gate is bypassed, these core modules will fail without a valid token

## 📄 Output

The generated PDF includes:
- Professional cover page with AI-generated image
- **Extended Tier**: Branded headers with custom logo
- **Extended Tier**: Footers with page numbers and your website URL
- Clean Helvetica typography
- Automatic markdown formatting (headers, bold, italic)
- Page breaks between chapters

## 🛠️ Technical Stack

- **GUI**: customtkinter (Dark Mode) with Right-Click context menus
- **AI**: OpenAI GPT-4o (content with streaming) + DALL-E 3 (images)
- **PDF**: ReportLab Platypus engine
- **Security**: SHA256-based tiered license validation with session tokens

## 🎨 UX Features

- **Live Typewriter Preview**: Watch your chapters being written in real-time on a paper-like white preview panel
- **Right-Click Context Menu**: Cut/Copy/Paste functionality works reliably on all input fields
- **Tier Indicator**: PRO Features Active badge for Extended license users
- **Upgrade Button**: Standard license users see a prominent upgrade button to unlock branding features

## 📝 License

This software is proprietary. A valid license key is required for use.

---

*Generated by Faleovad AI Enterprise*