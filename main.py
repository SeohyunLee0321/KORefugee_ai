import io
import os
from google.cloud import storage
from PIL import Image
from fastapi import FastAPI

app = FastAPI()


@app.get("/translate/{original_file_path:path}_/{download_file_path:path}/{trans_target_lang}")
async def translate(original_file_path: str, download_file_path: str, trans_target_lang: str):
    upload_file(original_file_path)
    translate_v3(original_file_path, trans_target_lang)
    download_file(original_file_path, download_file_path, trans_target_lang)

    return {"all done!"}

from google.cloud import translate_v3beta1 as translate

# 서비스 키
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"korefugees-ee87e097969a.json"

client = translate.TranslationServiceClient()
storage_client = storage.Client()

location = "us-central1"
parent = f"projects/korefugees/locations/us-central1"

bucket_name = 'korefugee_trans'
bucket = storage_client.bucket(bucket_name)


def upload_file(original_file_path: str):
    last_slash = original_file_path.rfind("/")
    last_dot = original_file_path.rfind(".")

    # 파일 형식, 파일명만 parsing
    file_type = original_file_path[last_dot + 1:]
    file_name = original_file_path[last_slash + 1: last_dot]

    blob_name = 'original/' + file_name + '.pdf'
    blob = bucket.blob(blob_name)

    if file_type == "jpeg" or file_type == "jpg":
        img = Image.open(original_file_path)

        byte_arr = io.BytesIO()
        img.save(byte_arr, format="pdf")

        f = blob.open("wb")
        f.write(byte_arr.getvalue())
        f.close()

    else:
        blob.upload_from_filename(original_file_path)


def translate_v3(original_file_path: str, trans_target_lang: str):
    last_slash = original_file_path.rfind("/")
    last_dot = original_file_path.rfind(".")

    # 파일 형식, 파일명만 parsing
    file_name = original_file_path[last_slash + 1: last_dot]

    blob = bucket.blob('original/' + file_name + '.pdf')
    blob_target = bucket.blob('translated/' + file_name + '_' + trans_target_lang + '.pdf')

    with blob.open("rb") as document:
        document_content = document.read()

    document_input_config = {
        "content": document_content,
        "mime_type": 'application/pdf',
    }

    response = client.translate_document(
        request={
            "parent": parent,
            "target_language_code": trans_target_lang,
            "document_input_config": document_input_config,
        }
    )

    f = blob_target.open("wb")
    f.write(response.document_translation.byte_stream_outputs[0])
    f.close()


def download_file(original_file_path: str, download_file_path: str, trans_target_lang: str):
    last_slash = original_file_path.rfind("/")
    last_dot = original_file_path.rfind(".")

    # 파일 형식, 파일명만 parsing
    file_name = original_file_path[last_slash + 1: last_dot] + "_" + trans_target_lang
    blob_name = 'translated/' + file_name + '.pdf'

    file_path = download_file_path + file_name + '.pdf'

    blob = bucket.blob(blob_name)
    blob.download_to_filename(file_path)