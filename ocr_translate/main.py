import uvicorn
from fastapi import FastAPI
# http://127.0.0.1:8000/docs

from fastapi import FastAPI, UploadFile, File

app = FastAPI()

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=7000)

@app.post("/OCR/")
async def image_ocr(target_lang, file: UploadFile = File(...)):
    file_location = f"{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())

    text = detect_text_trans(file_location, target_lang)

    return text


import os
import io
from google.cloud import vision
from google.cloud import translate_v2 as translate
import pandas as pd

credential_path = "KORefugeeServiceAccount.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path


def detect_text_trans(path: str, target_lang) -> str:
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()
    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations

    df = pd.DataFrame(columns=['locale', 'description'])
    for text in texts:
        df = df.append(
            dict(
                locale=text.locale,
                description=text.description
            ),
            ignore_index=True
        )

    trans_client = translate.Client()
    result = trans_client.translate(df['description'][0], source_language='ko', target_language=target_lang)

    # ocr : 문서의 텍스트만 반환, trans : 텍스트를 번역하여 반환
    text = {'ocr': df['description'][0], 'trans': result['translatedText']}

    return text