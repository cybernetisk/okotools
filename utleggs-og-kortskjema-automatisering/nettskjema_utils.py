import io
from nettskjema_api import (
    load_token, obtain_token, save_token,
    get_form_submissions, get_submission_pdf,
    get_submission_attachment
)
from pdf_utils import convert_image_to_pdf, extract_images_from_word, convert_images_to_pdfs, combine_pdfs

def get_submissions(form_id):
    token_data = load_token()
    if not token_data:
        token_data = obtain_token()
    save_token(token_data)

    form_submissions = get_form_submissions(form_id)

    # Create a dictionary to group submissions by submissionId to have simpler JSON
    # since Nettskjema has a kinda wierd and hard to work with JSON format
    submissions_dict = {}
    for answer in form_submissions:
        submission_id = answer.get('submissionId')
        element_id = answer.get('elementId')
        
        if submission_id not in submissions_dict:
            submissions_dict[submission_id] = {'submissionId': submission_id, 'elements': {}}
        
        submissions_dict[submission_id]['elements'][element_id] = answer

    submissions = list(submissions_dict.values())

    return submissions

def fetch_files_for_submission(submission):
    pdfs = []

    submission_id = submission['submissionId']
    submission_pdf_response = get_submission_pdf(submission_id)
    pdfs.append(io.BytesIO(submission_pdf_response.content))

    for element_id, element in submission['elements'].items():
        if element['elementType'] == 'ATTACHMENT':
            attachment_id = element['answerAttachmentId']
            media_type = element['mediaType']
            attachment_response = get_submission_attachment(attachment_id)
            
            # used to save the files for debugging
            # filename = str(attachment_id) + mimetypes.guess_extension(media_type)  # Convert attachment_id to string
            # with open(filename, 'wb') as out_file:
            #     out_file.write(attachment_response.content)
            # print(f"Downloaded {filename}")

            if media_type == 'application/pdf':
                pdfs.append(io.BytesIO(attachment_response.content))
            # Handle image types
            elif media_type in ['image/jpeg', 'image/png']:
                image_pdf = convert_image_to_pdf(attachment_response.content, image_format=media_type)
                pdfs.append(image_pdf)
            # Handle Word documents
            elif media_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                images = extract_images_from_word(attachment_response.content)
                image_pdfs = convert_images_to_pdfs(images)
                pdfs.extend(image_pdfs)

    return pdfs
