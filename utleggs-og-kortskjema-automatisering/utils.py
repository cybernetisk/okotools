import string

def sanitize_filename(filename, max_length=100):
    # Define valid characters, including æ, ø, å
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}æøåÆØÅ"
    sanitized_filename = ''.join(char if char in valid_chars else '_' for char in filename)
    return sanitized_filename[:max_length]
