import io
import os

from google.cloud import storage
from PIL import Image
from fastapi import FastAPI
import urllib.request

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/translate/{original_file_path:path}/{target_lang}")
async def translate(original_file_path: str, target_lang: str):
    last_slash = original_file_path.rfind("/")
    last_dot = original_file_path.rfind(".")
    file_name = original_file_path[last_slash + 1: last_dot]

    convert_file(file_name, original_file_path)
    return translate_v3(file_name, target_lang)


from google.cloud import translate_v3beta1 as translate

# 서비스 키
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"korefugees-ee87e097969a.json"

client = translate.TranslationServiceClient()
storage_client = storage.Client()

location = "us-central1"
parent = f"projects/korefugees/locations/us-central1"

bucket_name = 'korefugee_trans'
bucket = storage_client.bucket(bucket_name)


def convert_file(original_file_name: str, original_file_path: str):

    last_dot = original_file_path.rfind(".")
    file_type = original_file_path[last_dot + 1:]

    blob_name = 'original/' + original_file_name + '.pdf'
    blob = bucket.blob(blob_name)

    urllib.request.urlretrieve(original_file_path, "test.jpg")

    if file_type == "jpeg" or file_type == "jpg":
        img = Image.open("test.jpg")

        byte_arr = io.BytesIO()
        img.save(byte_arr, format="pdf")

        f = blob.open("wb")
        f.write(byte_arr.getvalue())
        f.close()


def translate_v3(file_name: str, trans_target_lang: str):
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

    return blob_target.public_url