# main.py

from datetime import datetime, timedelta
import os
import json
from dotenv import load_dotenv
from nettskjema_utils import get_submissions, fetch_files_for_submission
from nettskjema_api import delete_submissions
from pdf_utils import combine_pdfs
from tripletex_utils import Tripletex
from utils import sanitize_filename

load_dotenv()

def clear_output_directory(directory):
    """ This function clears all files in the specified directory."""
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                for nested_filename in os.listdir(file_path):
                    nested_file_path = os.path.join(file_path, nested_filename)
                    os.unlink(nested_file_path)
                os.rmdir(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

def process_and_upload_form(form_id, form_type, specific_element_id, output_directory, tripletex):
    submissions = get_submissions(form_id)
    if not submissions:  # Check if submissions is None or empty and if so skip processing
        print(f"No submissions found for form_id: {form_id}. Skipping processing.")
        return

    for submission in submissions:
        pdf_streams = fetch_files_for_submission(submission)

        # Default title to use in case the specific element isn't found
        pdf_title = f"{submission['submissionId']}_combined"

        # Check if specific element exists in this submission and use the text as filename
        if specific_element_id in submission['elements']:
            element = submission['elements'][specific_element_id]
            pdf_title = element.get('textAnswer', pdf_title)

        # Sanitize pdf_title to avoid any issues with file naming
        pdf_title = sanitize_filename(pdf_title)
        output_path = os.path.join(output_directory, f"{form_type}_{pdf_title}.pdf")
        combine_pdfs(pdf_streams, output_path)
        print(f"Combined PDF created: {output_path}")

        # Upload to Tripletex
        with open(output_path, 'rb') as pdf_file:
            response_status_code = tripletex.upload_file(pdf_file, filename=f"{form_type}_{pdf_title}.pdf")

        # If upload is successful, delete the submission in Nettskjema so to not upload it again
        if response_status_code == 201:
            re = delete_submissions(form_id, [submission['submissionId']])

            if re.status_code == 204:
                print(f"Successfully deleted submission with id {submission['submissionId']} from Nettskjema.")
            else:
                print(f"Failed to delete submission with id {submission['submissionId']} from Nettskjema. Status code: {re.status_code}, Response: {re.text}")

def main():
    # Environment variables for Nettskjema form IDs
    kort_skjema = int(os.environ.get("KORTSKJEMA_ID"))
    utleggs_skjema = int(os.environ.get("UTLEGGSKJEMA_ID"))
    output_directory = "kombinerte_skjemaer"
    os.makedirs(output_directory, exist_ok=True)

    # Tripletex credentials from environment variables or hardcode them here
    tripletex_api_url = "https://tripletex.no/v2"
    CONSUMER_TOKEN = os.environ.get("TRIPLETEX_CONSUMER_TOKEN")
    EMPLOYEE_TOKEN = os.environ.get("TRIPLETEX_EMPLOYEE_TOKEN")
    expiration_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    tripletex = Tripletex(tripletex_api_url, CONSUMER_TOKEN, EMPLOYEE_TOKEN, expiration_date)

    # Clear the output directory at the beginning
    clear_output_directory(output_directory)

    # Process both forms with their respective specific element IDs
    kort_skjema_specific_element_id = 6120909  # Specific element ID for the "kortkjøp" form
    utleggs_skjema_specific_element_id = 6934022  # Specific element ID for the "utlegg" form

    if kort_skjema:
        process_and_upload_form(kort_skjema, "kortkjøp", kort_skjema_specific_element_id, output_directory, tripletex)

    if utleggs_skjema:
        process_and_upload_form(utleggs_skjema, "utlegg", utleggs_skjema_specific_element_id, output_directory, tripletex)

if __name__ == "__main__":
    main()
