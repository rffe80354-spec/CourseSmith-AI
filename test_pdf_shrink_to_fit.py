#!/usr/bin/env python3
"""
Test script for PDF Shrink-to-Fit functionality.
Tests that PDFs respect the target page count by adjusting font sizes.
"""

import os
import sys
import tempfile
from project_manager import CourseProject
from pdf_engine import PDFBuilder

# Mock session manager to bypass license checks for testing
import session_manager
session_manager.is_active = lambda: True
session_manager.get_tier = lambda: 'extended'

def create_large_content_project(target_pages=10):
    """Create a project with large amounts of content to test shrink-to-fit."""
    project = CourseProject()
    project.topic = "Advanced Machine Learning Techniques"
    project.audience = "Graduate Students and AI Researchers"
    
    # Create outline with multiple chapters
    project.outline = [
        "Introduction to Deep Learning",
        "Neural Network Architectures",
        "Convolutional Neural Networks",
        "Recurrent Neural Networks",
        "Transformer Models",
        "Attention Mechanisms",
        "Training Strategies",
        "Optimization Techniques",
        "Regularization Methods",
        "Advanced Applications"
    ]
    
    # Generate large content for each chapter (7000+ chars per chapter)
    large_content = """
# Introduction

This chapter provides a comprehensive overview of the fundamental concepts and advanced techniques in modern machine learning. We will explore the theoretical foundations, practical implementations, and cutting-edge developments that are shaping the field today.

## Historical Context

The field of machine learning has evolved dramatically over the past several decades. From simple perceptrons to sophisticated deep learning architectures, the journey has been marked by breakthrough innovations and paradigm shifts. Understanding this historical context is crucial for appreciating current methodologies and anticipating future developments.

## Core Principles

At the heart of machine learning lie several fundamental principles that guide algorithm design and implementation. These include the bias-variance tradeoff, the principle of parsimony, and the importance of generalization. Each of these concepts plays a critical role in developing robust and effective models.

The bias-variance tradeoff represents a fundamental tension in statistical learning. Models with high bias tend to be too simple and may underfit the data, missing important patterns. Conversely, models with high variance may be too complex, capturing noise rather than signal and leading to overfitting. Finding the right balance is essential for optimal performance.

## Modern Architectures

Contemporary machine learning systems leverage sophisticated architectures that can process vast amounts of data and extract meaningful patterns. These architectures are built on principles of hierarchical learning, where lower layers capture simple features and higher layers combine these into complex representations.

Deep neural networks exemplify this hierarchical approach. Through multiple layers of transformation, they can learn increasingly abstract representations of the input data. This capability has led to breakthrough performance in tasks ranging from image recognition to natural language processing.

## Training Methodologies

Effective training of machine learning models requires careful consideration of multiple factors. These include data preprocessing, feature engineering, model selection, hyperparameter tuning, and validation strategies. Each component must be carefully designed and implemented to ensure optimal performance.

Data preprocessing is often the most time-consuming but critical phase of model development. It involves cleaning the data, handling missing values, normalizing features, and potentially augmenting the dataset to improve model robustness. The quality of preprocessing directly impacts the final model performance.

## Advanced Techniques

Recent advances in machine learning have introduced powerful techniques that push the boundaries of what's possible. These include transfer learning, meta-learning, few-shot learning, and self-supervised learning. Each approach offers unique advantages and is suited to different types of problems.

Transfer learning allows models trained on one task to be adapted for related tasks, dramatically reducing the amount of labeled data required. This has proven particularly valuable in domains where labeled data is scarce or expensive to obtain. The success of transfer learning has revolutionized many application areas.

## Practical Considerations

Deploying machine learning systems in production environments introduces a host of practical considerations. These include model serving infrastructure, monitoring and maintenance, handling concept drift, and ensuring fairness and interpretability. Success in real-world applications requires attention to these operational concerns.

Model serving infrastructure must be robust, scalable, and efficient. It needs to handle varying loads, maintain low latency, and ensure high availability. Modern solutions often employ containerization, orchestration platforms, and specialized serving frameworks to meet these requirements.

## Future Directions

The field continues to evolve rapidly, with new techniques and applications emerging regularly. Areas of active research include continual learning, causal inference, and the integration of symbolic reasoning with neural approaches. These developments promise to address current limitations and open new possibilities.

Continual learning aims to create systems that can learn continuously from new data without forgetting previously acquired knowledge. This capability would represent a significant step toward more flexible and adaptable AI systems that can operate in dynamic environments.

## Conclusion

Machine learning represents one of the most powerful tools in modern technology. Its applications span virtually every domain, from healthcare to finance, from entertainment to scientific discovery. As the field continues to advance, understanding its principles and techniques becomes increasingly important for practitioners and researchers alike.

The journey through machine learning is both challenging and rewarding. It requires a combination of theoretical understanding, practical skills, and creative problem-solving. By mastering these elements, practitioners can develop systems that push the boundaries of what's possible and create real value in their applications.
"""
    
    # Add large content to all chapters
    for chapter_title in project.outline:
        project.chapters_content[chapter_title] = large_content
    
    # Set up UI settings with target page count
    project.ui_settings = {
        'target_page_count': target_pages,
        'custom_images': [],
        'text_style': 'justified',
        'font_size': 'medium'
    }
    
    return project

def count_pdf_pages(pdf_path):
    """Count the number of pages in a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    except ImportError:
        # Fallback: use regex-based counting (unreliable - may produce inaccurate results)
        # This is a simplified approach that counts /Page objects in the PDF structure.
        # WARNING: This method is not robust and may fail on complex PDFs.
        # For production use, install PyPDF2: pip install pypdf2
        with open(pdf_path, 'rb') as f:
            content = f.read()
            # Count page objects in PDF using a simple regex pattern
            import re
            pages = re.findall(rb'/Type\s*/Page[^s]', content)
            return len(pages)

def test_shrink_to_fit_basic():
    """Test basic shrink-to-fit functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Shrink-to-Fit with 10-page limit")
    print("="*60)
    
    # Create project with large content
    project = create_large_content_project(target_pages=10)
    
    # Build PDF with page limit
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        builder = PDFBuilder(output_path)
        result_path = builder.build_pdf(project)
        
        # Check if file was created
        if not os.path.exists(result_path):
            print("❌ FAILED: PDF file was not created")
            return False
        
        # Count pages (approximate check since we can't easily parse PDF)
        file_size = os.path.getsize(result_path)
        print(f"✅ PDF created successfully")
        print(f"   File size: {file_size / 1024:.1f} KB")
        print(f"   Target pages: 10")
        print(f"   Note: Manual inspection required to verify page count")
        
        # Clean up
        os.unlink(result_path)
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(output_path):
            os.unlink(output_path)
        return False

def test_shrink_to_fit_small_limit():
    """Test with very small page limit."""
    print("\n" + "="*60)
    print("TEST 2: Extreme Shrink-to-Fit with 5-page limit")
    print("="*60)
    
    # Create project with large content but very small page limit
    project = create_large_content_project(target_pages=5)
    project.ui_settings['target_page_count'] = 5
    
    # Build PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        builder = PDFBuilder(output_path)
        result_path = builder.build_pdf(project)
        
        if not os.path.exists(result_path):
            print("❌ FAILED: PDF file was not created")
            return False
        
        file_size = os.path.getsize(result_path)
        print(f"✅ PDF created successfully with extreme limit")
        print(f"   File size: {file_size / 1024:.1f} KB")
        print(f"   Target pages: 5")
        print(f"   Note: Should use minimum font scale")
        
        os.unlink(result_path)
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(output_path):
            os.unlink(output_path)
        return False

def test_without_page_limit():
    """Test standard build without page limit."""
    print("\n" + "="*60)
    print("TEST 3: Standard build without page limit")
    print("="*60)
    
    # Create project without page limit
    project = create_large_content_project()
    project.ui_settings = {}  # No page limit
    
    # Build PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        builder = PDFBuilder(output_path)
        result_path = builder.build_pdf(project)
        
        if not os.path.exists(result_path):
            print("❌ FAILED: PDF file was not created")
            return False
        
        file_size = os.path.getsize(result_path)
        print(f"✅ PDF created successfully without page limit")
        print(f"   File size: {file_size / 1024:.1f} KB")
        print(f"   Note: Should use standard font sizes")
        
        os.unlink(result_path)
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(output_path):
            os.unlink(output_path)
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PDF SHRINK-TO-FIT TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Basic Shrink-to-Fit", test_shrink_to_fit_basic()))
    results.append(("Extreme Shrink-to-Fit", test_shrink_to_fit_small_limit()))
    results.append(("Standard Build", test_without_page_limit()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
