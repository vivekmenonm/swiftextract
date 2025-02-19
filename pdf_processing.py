from pdf2image import convert_from_path
import tempfile
import os
import time
from data_extraction import extract_text_from_image
import psycopg2
import psycopg2.extras

# ✅ PostgreSQL Configuration
DB_HOST = os.getenv("POSTGRES_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")


# ✅ PostgreSQL Database Connection
def get_db():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def save_extraction_history(username, document_name, total_rows, total_time):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO extraction_history (username, document_name, total_rows, total_time)
        VALUES (%s, %s, %s, %s)
    """, (username, document_name, total_rows, total_time))
    conn.commit()
    conn.close()

def process_pdf(pdf_path, prompt, username, queue, total_pages_global):
    document_name = os.path.basename(pdf_path)
    print(f"Started processing: {document_name}", flush=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            images = convert_from_path(pdf_path, output_folder=temp_dir, fmt="jpeg")
            total_pages = len(images)  
            all_data = []
            skipped_pages = []
            start_time = time.time()

            for idx, image in enumerate(images):
                page_number = idx + 1
                image_path = os.path.join(temp_dir, f"page_{page_number}.jpg")
                image.save(image_path, "JPEG")

                # ✅ Extract text
                extraction_result = extract_text_from_image(image_path, prompt, page_number)

                if extraction_result["extracted_data"]:
                    for item in extraction_result["extracted_data"]:
                        item["page_number"] = page_number
                        item["document_name"] = document_name
                        all_data.append(item)

                if extraction_result["skipped_pages"]:
                    skipped_pages.extend(extraction_result["skipped_pages"])

                # ✅ Per-document progress
                doc_progress = round((page_number / total_pages) * 100, 2)

                # ✅ Global progress update
                queue.put({
                    "document_name": document_name,
                    "page_number": page_number,
                    "total_pages": total_pages,
                    "progress": doc_progress,
                    "total_pages_global": total_pages_global,
                    "current_page_processed": 1  # ✅ Used for dynamic total progress
                })

            total_time = round(time.time() - start_time, 2)
            total_rows_extracted = len(all_data)
            avg_time_per_field = round(total_time / total_rows_extracted, 2) if total_rows_extracted > 0 else 0
            save_extraction_history(username, document_name, total_rows_extracted, total_time)
            # ✅ Send final extracted data
            queue.put({
                "completed": True,
                "document_name": document_name,
                "total_time": total_time,
                "total_rows_extracted": total_rows_extracted,
                "avg_time_per_row": avg_time_per_field,
                "skipped_pages": skipped_pages,
                "extracted_data": all_data
            })

        except Exception as e:
            print(f"Error processing {document_name}: {str(e)}", flush=True)
            queue.put({"error": str(e)})