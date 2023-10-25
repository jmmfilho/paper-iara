import requests
from config import *


def classifier_bot(msg):
    payload = {'msg': msg}
    files = []
    headers = {}
    response = requests.request("POST", URL_CLASSIFICADOR_FAROLDIGITAL, headers=headers, data=payload, files=files)
    classificador_message = response.text

    return classificador_message
