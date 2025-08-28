import sys
import os
import subprocess
import json

# Add the project root to the Python path to find the 'src' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.pdf_extractor import PDFExtractor

def main(pdf_path):
    """
    Runs the PDF extraction process on a single file using the project's
    internal components and prints the results.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    print(f"\n--- Testing: {os.path.basename(pdf_path)} ---")
    
    try:
        # Use a command-line utility to extract text, mimicking how the
        # containerized application environment would operate.
        result = subprocess.run(['pdftotext', pdf_path, '-'], capture_output=True, text=True, check=True)
        pdf_text = result.stdout
        
        extractor = PDFExtractor(pdf_text)
        data = extractor.extract()
        
        if not data:
            print("Extraction failed. No data returned.")
            return

        print("\n✅ VIOLATIONS (Code Description Only):")
        violations = data.get('violations', [])
        if violations:
            for v in violations:
                print(f"  - Code {v['violation_code']}: {v['code_description']}")
        else:
            print("  No violations found.")

    except FileNotFoundError:
        print("\nError: 'pdftotext' not found in the execution environment.")
        print("This script assumes 'pdftotext' (from poppler-utils) is available,")
        print("as it likely is in the production Docker container.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dev-tools/run_extraction_test.py <path_to_pdf>")
        sys.exit(1)
    
    # Process all file paths provided as arguments
    for file_path in sys.argv[1:]:
        main(file_path)
