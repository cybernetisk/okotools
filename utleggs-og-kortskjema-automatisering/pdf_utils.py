import io
from PIL import Image
import PyPDF2
from docx import Document

A4_WIDTH_PX = int(8.27 * 300)
DPI = 300

def convert_image_to_pdf(image_bytes, rotate_if_wide=True, image_format=None):
    image = Image.open(io.BytesIO(image_bytes))

    if image.mode != 'RGB':
        image = image.convert('RGB')

    # Since the jpg images (taken from phones) often get put sideways we rotate them 
    # 90 degrees with the clock if the width is bigger than the height.
    # This is an assumptiom but most of the time it is correct 
    if rotate_if_wide and image_format != 'image/png' and image.width > image.height:
        image = image.rotate(270, expand=True)

    # Scale image to fit the width of A4 while maintaining aspect ratio
    image_ratio = image.width / image.height
    new_width = A4_WIDTH_PX
    new_height = int(A4_WIDTH_PX / image_ratio)

    image = image.resize((new_width, new_height), Image.LANCZOS)

    # Create a new PDF page with the same size as the image
    pdf_io = io.BytesIO()
    converted_image = Image.new("RGB", (new_width, new_height), "white")
    converted_image.paste(image, (0, 0))

    # Save the new image as a PDF
    converted_image.save(pdf_io, format="PDF", resolution=DPI)
    pdf_io.seek(0)

    return pdf_io

def extract_images_from_word(word_bytes):
    """on an offchance someone uploads a word document with a picture 
    in it instead of just an actual picture (actually happens for some reason)"""
    # Load the Word document
    doc = Document(io.BytesIO(word_bytes))

    images = []

    for rel in doc.part.rels:
        if "image" in doc.part.rels[rel].target_ref:
            image = doc.part.rels[rel].target_part.blob
            images.append(image)

    return images

def convert_images_to_pdfs(images):
    pdf_streams = []
    for image in images:
        image_pdf = convert_image_to_pdf(image)
        pdf_streams.append(image_pdf)
    return pdf_streams

def combine_pdfs(pdf_streams, output_path):
    merger = PyPDF2.PdfMerger()
    for pdf in pdf_streams:
        merger.append(pdf)

    with open(output_path, 'wb') as f:
        merger.write(f)
