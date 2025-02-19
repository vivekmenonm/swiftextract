import time
import base64
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
import vertexai
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Google Cloud project details
project = os.getenv("GENAI_PROJECT")
location = os.getenv("GENAI_LOCATION")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "peppy-linker-332510-c7733d076051.json"


def extract_text_from_image(image_path, prompt, page_number):
    max_retries = 10  # Maximum retry attempts
    backoff_factor = 2  # Exponential backoff (2, 4, 8, 16 sec)
    max_wait_time = 30  # **Maximum time allowed (30 seconds)**
    start_time = time.time()

    extracted_data = []  # **Store extracted results**
    skipped_pages = []  # **Track skipped pages**
    timeout_reached = False  # **Flag if timeout occurs**

    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

        vertexai.init(project=project, location=location)
        image_part = Part.from_data(mime_type="image/png", data=base64.b64decode(encoded_image))
        model = GenerativeModel("gemini-1.5-flash-002")
        chat = model.start_chat()

        for attempt in range(max_retries):
            elapsed_time = time.time() - start_time

            if elapsed_time > max_wait_time:
                print(f"Timeout reached ({max_wait_time} sec). Skipping Page {page_number}...")
                skipped_pages.append(page_number)  # ✅ Mark this page as skipped
                timeout_reached = True
                break  # **Stop trying this page**

            try:
                response = chat.send_message(
                    [image_part, prompt],
                    generation_config={"max_output_tokens": 8192, "temperature": 1, "top_p": 0.95, "response_mime_type": "application/json"},
                    safety_settings = [
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=SafetySetting.HarmBlockThreshold.OFF
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=SafetySetting.HarmBlockThreshold.OFF
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=SafetySetting.HarmBlockThreshold.OFF
                ),
                SafetySetting(
                    category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=SafetySetting.HarmBlockThreshold.OFF
                ),
            ]
                )

                response_text = response.text.strip().strip("```json").strip("```")

                if response_text:
                    extracted_data = json.loads(response_text)  # **Store results**
                    return {
                        "extracted_data": extracted_data,
                        "skipped_pages": skipped_pages,  # **Pages that were not processed**
                        "timeout": timeout_reached
                    }

            except Exception as e:
                if "429" in str(e):
                    wait_time = backoff_factor ** attempt  # Exponential wait (2, 4, 8 sec)
                    print(f"Rate limit hit (429), retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"Error extracting text from Page {page_number}: {e}")
                    break  # **Skip this page if another error occurs**

        print(f"Max retries exceeded for Page {page_number}. Skipping...")
        skipped_pages.append(page_number)  # **Mark page as skipped**
        return {
            "extracted_data": extracted_data,
            "skipped_pages": skipped_pages,
            "timeout": timeout_reached
        }

    except Exception as e:
        print(f"Critical error extracting text from Page {page_number}: {e}")
        return {
            "extracted_data": [],
            "skipped_pages": [page_number],
            "timeout": timeout_reached
        }