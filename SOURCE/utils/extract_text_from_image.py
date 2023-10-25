from pytesseract import pytesseract
from PIL import Image


def extract_text_from_image(path):
    img = Image.open(path)
    read_text = pytesseract.image_to_string(img)
    return read_text
