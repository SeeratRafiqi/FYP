#imports the function to extract text from a PDF file
from pdfminer.high_level import extract_text

def extract_text_from_pdf(pdf_path):
    # here we try to extract all the text from the PDF file 
    try:
        text = extract_text(pdf_path)
        return text
    # if an exception occured
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
    
    #Purpose: To extract plain text content from PDF files. This is essential if the user uploads their resume as a PDF.