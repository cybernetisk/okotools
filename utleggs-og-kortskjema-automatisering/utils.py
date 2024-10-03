import string

def sanitize_filename(filename):
    # Define valid characters, including æ, ø, å
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}æøåÆØÅ"
    return ''.join(char if char in valid_chars else '_' for char in filename)
