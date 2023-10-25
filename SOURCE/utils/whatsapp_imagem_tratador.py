import pathlib
import requests
import json
import datetime
import os

from config import URL_BASE_IARABOT


def extrairCaminho(caminho_arquivo):
    caminhho = pathlib.Path(caminho_arquivo)
    return str(caminhho.parent)+'/'


def extrairNome(caminho_arquivo):
    caminho = pathlib.Path(caminho_arquivo)
    return os.path.basename(caminho)


def extrairMime_type(nome_arquivo):
    return f'image/{nome_arquivo.split(".")[-1].lower()}'


def nomeSemExtencao(nome_arquivo):
    return f'{nome_arquivo.split(".")[0].lower()}'


def realizar_upload(caminho):
    # caminho_arquivo, nome_arquivo, mime_type
    caminho_arquivo = extrairCaminho(caminho)
    nome_arquivo = extrairNome(caminho)
    mime_type = extrairMime_type(nome_arquivo)
    data_atual = datetime.datetime.now()
    chave = data_atual.strftime("1234.%Y.%m.%d")
    url_token = URL_BASE_IARABOT + "/gerarToken"
    payload_token = json.dumps({
        "chave": chave,
        "mensagem": "upload"
    })
    headers_token = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url_token, headers=headers_token, data=payload_token)
    token = response.text
    url_upload = URL_BASE_IARABOT + "/upload"
    payload_upload={}
    files=[
        ('arquivo',(nome_arquivo, open(caminho_arquivo + nome_arquivo,'rb'), mime_type))
    ]
    headers_upload = {
        'token': token
    }

    response = requests.request("POST", url_upload, headers=headers_upload, data=payload_upload, files=files)
    nome_arq_servidor = response.text

    return nome_arq_servidor
