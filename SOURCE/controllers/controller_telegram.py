import os
import json
import spacy
import shutil
import random
import PyPDF2
import telepot
import requests
import psycopg2
import numpy as np
import pytesseract
from PIL import Image
import pandas as panda
from urllib import request
import moviepy.editor as mpe
from docx2txt import process
from pydub import AudioSegment
import speech_recognition as sr
from tempfile import NamedTemporaryFile
from sqlalchemy import create_engine, text
from os import path, rename, environ, listdir
from google.cloud import dialogflow_v2 as dialogflow
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


from utils.extract_text_from_image import extract_text_from_image
from utils.connect_python_dialogflow import agent_dialogflow_to_python
from utils.insert_database import conect_database
from config import *
from utils.classifier import *

from utils.converter_audio_to_text import *
from utils.insert_database import conect_database



class Bot_telegram():

    def __init__(self):
        self.engine = None
        self.nlp = spacy.load("pt_core_news_sm")
        token = TELEGRAM_TOKEN
        # Ler mensagens
        self.url_base = f'https://api.telegram.org/bot{token}/'

    # Iniciar o Bot
    def Iniciar(self):
        update_id = None
        while True:
            atualizacao = self.obter_mensagens(update_id)
            mensagens = atualizacao['result'] if atualizacao else None
            if mensagens:
                for mensagem in mensagens:
                    update_id = mensagem['update_id']


    def extrairFoto(self, chat_id, message, token_img_voix_video, doc_video_text=""):
        token_formato = telepot.Bot(TELEGRAM_TOKEN)
        token_formato.sendMessage(chat_id, str("Aguarde enquanto analizo seu conteúdo."))
        if doc_video_text == "image/jpeg" or doc_video_text == "image/png":
            file_id = message['document']['file_id']
        else:
            file_id = message['photo'][len(message['photo']) - 1]['file_id']
        getFile = requests.get(f'{self.url_base}getFile?file_id={file_id}').json()
        file_path = getFile['result']['file_path']
        photo_url = f"https://api.telegram.org/file/bot{token_img_voix_video}/{file_path}"

        """path_photo = './baixar/imagem'"""
        path_photo = '../baixados/imagens'
        nome_arquivo = path.basename(photo_url)
        caminho_imagem = path.join(path_photo, nome_arquivo)
        request.urlretrieve(photo_url, caminho_imagem)

        """Chamar a função para extrair texto da imagem"""
        texto_extraido = extract_text_from_image(caminho_imagem)
        return texto_extraido
    def extrairAudio(self, chat_id, message, token_img_voix_video):
        token_formato = telepot.Bot(TELEGRAM_TOKEN)
        token_formato.sendMessage(chat_id, str("Aguarde enquanto analizo seu conteúdo."))

        if ("voice" in message):
            file_ident = message['voice']['file_id']
        else:
            file_ident = message['audio']['file_id']
        pagaFile = requests.get(f'{self.url_base}getFile?file_id={file_ident}').json()
        file_path = pagaFile['result']['file_path']
        voice_url = f"https://api.telegram.org/file/bot{token_img_voix_video}/{file_path}"
        pasta_destino = "baixados/audio"
        """Obtém o nome do arquivo da URL """
        nome_arquivo = voice_url.split("/")[-1]
        """Inserir arquivo no caminho para pasta"""
        caminho_destino = path.normpath(path.join(pasta_destino, nome_arquivo))
        """Faça o download do arquivo diretamente para a pasta de destino"""
        response = requests.get(voice_url)
        """ Verifique se o download foi bem-sucedido (código de resposta HTTP 200)"""
        if response.status_code == 200:
            """ Abra o arquivo de destino em modo binário ('wb') e escreva o conteúdo da resposta"""
            with open(caminho_destino, 'wb') as file:
                file.write(response.content)
            print(f"Arquivo baixado com sucesso em: {caminho_destino}")
        else:
            print(f"Falha ao baixar o arquivo. Código de resposta HTTP: {response.status_code}")
        """ Converter audio para wav"""
        pathOgg = path.join(pasta_destino, "voice_converter.ogg")
        request.urlretrieve(voice_url, pathOgg)
        arquivo = AudioSegment.from_file(pathOgg)
        pathWav = path.join(pasta_destino, "voice_converter.wav")
        arquivo.export(pathWav, format=("wav"))
        arquivo = pathWav

        """Camar a função para extrair arquivo"""
        texto_extraido = transcribe_audio(arquivo)
        return texto_extraido
    def extrairVideo(self, chat_id, message, token_img_voix_video, doc_video_text=""):
        token_formato = telepot.Bot(TELEGRAM_TOKEN)
        token_formato.sendMessage(chat_id, str("A análise do seu video pode demorar alguns minutos, agurde."))
        if doc_video_text == "video/mp4":
            file_ident = message['document']['file_id']
        else:
            file_ident = message['video']['file_id']
        tomarFile = requests.get(f'{self.url_base}getFile?file_id={file_ident}').json()
        file_path = tomarFile['result']['file_path']
        video_url = f"https://api.telegram.org/file/bot{token_img_voix_video}/{file_path}"
        path_video = "../baixados/video"
        # Baixar Video do telegram
        arquivo_temp = NamedTemporaryFile(delete=False)
        request.urlretrieve(video_url, arquivo_temp.name)
        nome_audio = path.basename(video_url)
        caminho_audio = path.join(path_video, nome_audio)
        rename(arquivo_temp.name, caminho_audio)
        pathMp4 = path.join(path_video, "video_converter.mp4")
        request.urlretrieve(video_url, pathMp4)
        arquivo = mpe.VideoFileClip(pathMp4)
        pathWav = path.join(path_video, "video_converter.wav")
        arquivo.audio.write_audiofile(pathWav)
        arquivo = pathWav
        """Camar a função para cnverter áudio em texto"""
        texto_extraido = transcribe_audio(arquivo)
        return texto_extraido
    def extrairWord(self, message, token_img_voix_video):
        file_ident = message['document']['file_id']
        pagaFile = requests.get(f'{self.url_base}getFile?file_id={file_ident}').json()
        file_path = pagaFile['result']['file_path']
        word_url = f"https://api.telegram.org/file/bot{token_img_voix_video}/{file_path}"

        path_word = '../baixados/docs'
        nome_arquivo = path.basename(word_url)
        caminho_arquivo = path.join(path_word, nome_arquivo)
        request.urlretrieve(word_url, caminho_arquivo)
        data = process(caminho_arquivo)
        return data
    def extrairTxt(self, message, token_img_voix_video):
        file_ident = message['document']['file_id']
        pagaFile = requests.get(f'{self.url_base}getFile?file_id={file_ident}').json()
        file_path = pagaFile['result']['file_path']
        textos_url = f"https://api.telegram.org/file/bot{token_img_voix_video}/{file_path}"
        path_doc = '../baixados/docs'
        nome_arquivo = path.basename(textos_url)
        # print(nome_arquivo)
        caminho_arquivo = path.join(path_doc, nome_arquivo)
        request.urlretrieve(textos_url, caminho_arquivo)
        with open(caminho_arquivo, "r") as arquivo:
            data = arquivo.read()
            return data
    def extrairPDF(self, message, token_img_voix_video):
        file_ident = message['document']['file_id']
        pagaFile = requests.get(f'{self.url_base}getFile?file_id={file_ident}').json()
        file_path = pagaFile['result']['file_path']
        pdf_url = f"https://api.telegram.org/file/bot{token_img_voix_video}/{file_path}"
        path_pdf = '../baixados/docs'
        # Abre a URL e baixa o arquivo
        with request.urlopen(pdf_url) as response:
            # Salva o conteúdo em um arquivo temporário
            with NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(response.read())
                # Move o arquivo temporário para o destino final
                shutil.move(tmp_file.name, path_pdf)
                pathDoc = path.join(path_pdf, "doc.pdf")
                request.urlretrieve(pdf_url, pathDoc)
                arq_pdf = open(pathDoc, 'rb')
                ler_pdf = PyPDF2.PdfReader(arq_pdf)
                # Página e o numero de página
                result_pdf = ""
                for n in range(len(ler_pdf.pages)):
                    pagina = ler_pdf.pages[n]
                    result_pdf = result_pdf + pagina.extract_text()
                return result_pdf

    # Obter menssagens
    def obter_mensagens(self, update_id):
        global dfc
        link_requisicao = f'{self.url_base}getUpdates?timeout=100'
        if update_id:
            link_requisicao = f'{link_requisicao}&offset={update_id + 1}'
        resultado = requests.get(link_requisicao)
        dados_json = resultado.json()

        # Construir Dataframe
        panda.set_option('display.max_columns', None)
        df = panda.json_normalize(dados_json, record_path=['result'])
        print(df)

        # Verificar entrada dos Dados
        #TODO Verificar se existe mensagem
        if "message.text" in df.columns:
            print('Tem mensagem enviada')
        elif "message.photo" in df.columns:
            print('Tem foto enviada')
        elif "message.voice.file_id" in df.columns:
            print('Tem voz enviado')
        elif "message.audio.file_id" in df.columns:
            print('Tem áudio enviado')
        elif "message.document.mime_type" in df.columns:
            print('Tem Documento enviado')
        elif "message.video.mime_type" in df.columns:
            print('Tem video enviado')
        elif 'callback_query.from.first_name' in df.columns:
            print('Botão apertado')
        else:
            print('Não tem mensagem enviado')
            return

        """Verificação de conteudo para converção"""
        token_img_voix_video = (TELEGRAM_TOKEN)
        results = dados_json['result']
        last_update_num = len(results) - 1
        update = results[last_update_num]
        if 'message' in update:
            message = update['message']
            chat_id = message['chat']['id']

            if ("photo" in message):
                df['message.text'] = self.extrairFoto(chat_id, message, token_img_voix_video)
                print(df)

            # converção de Voz para Texto
            elif ("voice" in message or "audio" in message):

                df['message.text'] = self.extrairAudio(chat_id, message, token_img_voix_video)
                print(df)

            # Converter Video em audio e depois em Texto
            elif ("video" in message):

                df['message.text'] = self.extrairVideo(chat_id, message, token_img_voix_video)

            # Converter Video no formato documento para audio e depois para Texto
            elif "message.document.mime_type" in df.columns:
                token_formato = telepot.Bot(TELEGRAM_TOKEN)
                token_formato.sendMessage(chat_id, str("Aguarde enquanto analizo seu conteúdo."))
                for i in range(len(df)):
                    doc_video_text = df.loc[i, "message.document.mime_type"]
                    print(doc_video_text)
                    if doc_video_text == "video/mp4":
                        df['message.text'] = self.extrairVideo(chat_id, message, token_img_voix_video, doc_video_text)
                        print(df)

                    # Converter Imagem recebida em formato de documento para texto
                    elif doc_video_text == "image/jpeg" or doc_video_text == "image/png":
                        df['message.text'] = self.extrairFoto(chat_id, message, token_img_voix_video, doc_video_text)

                    # Extrair documento word
                    elif doc_video_text == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        df['message.text'] = self.extrairWord(message, token_img_voix_video)

                        # Extrair documento .txt
                    elif doc_video_text == "text/plain" or doc_video_text == "text/html" or doc_video_text == "text/xml":
                        df['message.text'] = self.extrairTxt(message,token_img_voix_video)

                    # Extrair documento PDF
                    elif doc_video_text == "application/pdf":
                        df['message.text'] = self.extrairPDF(message, token_img_voix_video)
                    else:
                        token_formato = telepot.Bot(TELEGRAM_TOKEN)
                        token_formato.sendMessage(chat_id, str(" Trabalho com seguintes formatos: "
                                                                "\nPDF, WORD, TXT, HTML, XML,jpg, png, MP4. mp3, waw, m4a, 3gp."
                                                                "\n \nOu Copiar o texto do seu documento e colar aqui."))



        # Renomear as colunas
        df = df.rename(columns={'update_id': 'update_id', 'message.message_id': 'message_id',
                                'message.from.id': 'message_from_id',
                                'message.from.is_bot': 'message_from_is_bot',
                                'message.from.first_name': 'message_from_first_name',
                                'message.from.last_name': 'message_from_last_name',
                                'message.chat.id': 'message_chat_id',
                                'message.chat.type': 'message_chat_type',
                                'message.date': 'message_date', 'message.text': 'message_text'})

        """Criar a coluna message_from_last_name se não existir
        Devido a configuração do usuário, caso não configurou o aplicativo do telegram com seu apelido,
        os dados recebidos desse usuário não tem coluna message_from_last_name e isso dá inconsistencia da culuna
        na inserção ao banco de dados"""
        if "message_from_last_name" not in df.columns:
            df = df.reindex(columns = df.columns.tolist() + ["message_from_last_name"])

        # Organizar as colunas que precisamos num novo dataframe
        df2 = df.filter(items=['update_id', 'message_id', 'message_from_id',
                               'message_from_is_bot', 'message_from_first_name',
                               'message_from_last_name', 'message_chat_id',
                               'message_chat_type', 'message_date', 'message_text'])


        if "message_text" in df2.columns:
            df3 = df2[df2['message_text'].notnull()]
            df3 = df3.fillna('Null', inplace=False)
            # Reindexar linhas para evitar erro de localizar colunas a travês de indice
            df3 = df3.reset_index(drop=True)
            df3['number_of_words'] = np.nan
            df3['number_of_characteres'] = np.nan
            # Contagem das palavras e caracteres
            for i in range(len(df3)):
                df3.iloc[i, df3.columns.get_loc('number_of_words')] = len(
                    self.nlp(df3.iloc[i, df3.columns.get_loc('message_text')]))
                df3.iloc[i, df3.columns.get_loc('number_of_characteres')] = len(
                    df3.iloc[i, df3.columns.get_loc('message_text')])

            df4 = df3[df3['number_of_words'] >= 20]
            df4.message_text = df4.message_text.str.replace("\n", " ")
            df4 = df4.reset_index(drop=True)



            """Nesta seção os serão considerados os conteúdos que contenha 
            a partir de 20 palavra no seu conteúdo para serem analizados"""
            for i in range(len(df4)):

                groupe = df4.loc[i, "message_chat_type"]
                token_prob = TELEGRAM_TOKEN
                msg = df4.iloc[i, df4.columns.get_loc('message_text')]

                """ACIONAR CLASSIFICADOR a partir de arquivo classifier
                   Esta seção é acionada para analizar o conteúdo enviado por usuário"""
                classificador_message = classifier_bot(msg)
                # Verifica se a resposta do classificador é a porcentagem ou texto
                if len(str(classificador_message).split()) == 1:
                    # formatar para float com duas (2) casas decimais
                    n_formatado_float = "{:.2f}".format(float(classificador_message))
                    formatar_ponto = n_formatado_float.replace('.', '')
                    # Formatar para numero inteiro
                    n_formatado_int = int(formatar_ponto)
                    # Formatar em percentual
                    percentual = ("{}%".format(n_formatado_int))
                    # Frases definidas em config.py
                    frase_aleatoria = random.choice(frases)
                    resposta_gerada = f'{frase_aleatoria} {percentual}'
                    df4['probability'] = percentual

                    """Responder usuário"""
                    bot_chatID = str(df4.iloc[i, df4.columns.get_loc('message_chat_id')])
                    bot_messageID = str(df4.iloc[i, df4.columns.get_loc('message_id')])
                    # Enviar a probabilidade do conteudo só quando for enviado no privado (Conta pessoal)
                    if groupe == 'private':
                        send_text = 'https://api.telegram.org/bot' + token_prob + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&reply_to_message_id=' + bot_messageID + '&parse_mode=Markdown&text=' + resposta_gerada
                        requests.get(send_text)
                    # Enviar a probabilidade do conteudo nos grupos só quando tem uma elevada porcentagem de ser Desinformação
                    elif groupe == ('group' or 'supergroup') and n_formatado_int >= 90 :
                        send_text = 'https://api.telegram.org/bot' + token_prob + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&reply_to_message_id=' + bot_messageID + '&parse_mode=Markdown&text=' + '🚨 ATENÇÃO 🧨' + resposta_gerada
                        responsa = requests.get(send_text)



                #CONECÇÃO COM BANCO DE DADOS POSTGRESQL
                #Nesta seção os dados analizados são guardados em um bamco de dados

                engine = create_engine(conect_database())
                # Resolvendo problemas de aspas simples (Apóstrofe) no texto
                df4.message_text = df4.message_text.str.replace("'", "")
                df4.message_text = df4.message_text.str.replace('"', '')
                query = text(f""" 
                                    INSERT INTO iara_bot.tb_detector(update_id, message_id, message_from_id, message_from_is_bot, message_from_first_name, message_from_last_name, message_chat_id, message_chat_type, message_date, message_text, number_of_words, number_of_characteres, probability)
                                    VALUES {','.join([str(i) for i in list(df4.to_records(index=False))]).replace('"', "'")}
                                    ON CONFLICT (update_id)
                                    DO UPDATE SET
                                    message_id= excluded.message_id, 
                                    message_from_id= excluded.message_from_id, 
                                    message_from_is_bot= excluded.message_from_is_bot, 
                                    message_from_first_name= excluded.message_from_first_name, 
                                    message_from_last_name=  excluded.message_from_last_name,  
                                    message_chat_id= excluded.message_chat_id, 
                                    message_chat_type= excluded.message_chat_type, 
                                    message_date= excluded.message_date, 
                                    message_text= excluded.message_text,
                                    number_of_words= excluded.number_of_words,
                                    number_of_characteres= excluded.number_of_characteres,
                                    probability= excluded.probability
                                """)
                engine.execute(query)
                break

            # Area de Diálogo
            bot_token = telepot.Bot(TELEGRAM_TOKEN)
            for i in range(len(df3)):
                texto = df3.loc[i, "message_text"]
                grup = df3.loc[i, "message_chat_type"]
                # O Bot vai dialogar só na conta privada do usuario por enquanto
                if grup == 'group':
                    print('Não dialogo no grupo')
                if grup == 'private':
                    lista = df3["message_chat_id"].tolist()
                     # converter em string
                    chat_id = str(lista)
                    # Retirar os colchetes
                    chat_id = str(chat_id).strip('[]')

                    """ CONECTAR PYTHON COM DIALOGFLOW
                    Esta seção encaminha para dialogflow a mensagem enviada de telegram
                    e em seguida rencaminha para telegram a resposta dada por dialogflow"""

                    num_caracteres = len(texto)
                    #print(num_caracteres)
                    if num_caracteres < 256:
                        #TODO CREDENCIAIS GOOGLE
                        # Chamar a função Dialogflow
                        resultado_dialogflow = agent_dialogflow_to_python(texto)
                        dialogue = (resultado_dialogflow.query_result.fulfillment_text)

                        """Verificar se o valor de display_name é igual a Menssagem de Boas Vindas"""
                        if resultado_dialogflow.query_result.intent.display_name == "Menssagem de Boas Vindas":
                            bot_token.sendMessage(chat_id, dialogue)
                            """Verificar  se o valor de display_name é igual a Educação Midiática"""
                        elif resultado_dialogflow.query_result.intent.display_name == "Educação Midiática":
                            bot_token.sendMessage(chat_id, dialogue)
                            """Criar um botão com texto"""
                            button = InlineKeyboardButton("1ᵃ DICA", callback_data='botao_clicado')
                            """Adicionando o botão a um  teclado em linha"""
                            keyboard = InlineKeyboardMarkup([[button]])
                            """Envia a mensagem com o teclado"""
                            mensagem = "clique no botão abaixo"

                            bot_token.sendMessage(chat_id, mensagem,
                                                  reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                            """Verificar se a variável contém texto"""
                        elif isinstance(dialogue, str) and dialogue != "":
                            bot_token.sendMessage(chat_id, dialogue)



                    #EXEMPLOS DAS DICAS
                    # Primeiro Exemplo
                    if texto == '/iarabotprimeiradica':
                        pasta_de_imagens = "./imagens/dica_1/"
                        # Obtendo a lista de arquivos dentro da pasta
                        lista_arquivos = listdir(pasta_de_imagens)
                        # # Selecionando um arquivo aleatório da lista
                        arquivo_aleatorio = random.choice(lista_arquivos)
                        caminho_da_imagem = path.join(pasta_de_imagens, arquivo_aleatorio)
                        imagem = Image.open(caminho_da_imagem)
                        with NamedTemporaryFile(suffix='.jpg') as arquivo_temporario:
                            imagem.save(arquivo_temporario.name)
                            arquivo_temporario.seek(0)
                            bot_token.sendPhoto(chat_id=chat_id, photo=arquivo_temporario)
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("2ᵃ DICA", callback_data='segunda_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique em segunda dica Para continuar, pois são 7 dicas valiosas"
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                        break

                    # Segundo Exemplo
                    elif texto == '/iarabotsegundadica':
                        # from PIL import Image
                        pasta_de_imagens = "./imagens/dica_2"
                        # Obtendo a lista de arquivos dentro da pasta
                        lista_arquivos = listdir(pasta_de_imagens)
                        # Selecionando um arquivo aleatório da lista
                        arquivo_aleatorio = random.choice(lista_arquivos)
                        caminho_da_imagem = path.join(pasta_de_imagens, arquivo_aleatorio)
                        imagem = Image.open(caminho_da_imagem)
                        with NamedTemporaryFile(suffix='.jpg') as arquivo_temporario:
                            imagem.save(arquivo_temporario.name)
                            arquivo_temporario.seek(0)
                            bot_token.sendPhoto(chat_id=chat_id, photo=arquivo_temporario)
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("3ᵃ DICA", callback_data='terceira_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Vamos la, clique no botão em baixo para terceira dica."
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                        break

                    # Terceiro Exemplo
                    elif texto == '/iarabotterceiradica':
                        # from PIL import Image
                        pasta_de_imagens = "./imagens/dica_3"
                        # Obtendo a lista de arquivos dentro da pasta
                        lista_arquivos = listdir(pasta_de_imagens)
                        # # Selecionando um arquivo aleatório da lista
                        arquivo_aleatorio = random.choice(lista_arquivos)
                        caminho_da_imagem = path.join(pasta_de_imagens, arquivo_aleatorio)
                        imagem = Image.open(caminho_da_imagem)
                        with NamedTemporaryFile(suffix='.jpg') as arquivo_temporario:
                            imagem.save(arquivo_temporario.name)
                            arquivo_temporario.seek(0)
                            bot_token.sendPhoto(chat_id=chat_id, photo=arquivo_temporario)
                        # bot_token.sendMessage(chat_id, str("Continua, falta pouca para terminar."))
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("4ᵃ DICA", callback_data='quarta_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no \nbotão abaixo"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                        break

                        # Quinto Exemplo
                    elif texto == '/iarabotquartadica':
                        # from PIL import Image
                        pasta_de_imagens = "./imagens/dica_4"
                        # Obtendo a lista de arquivos dentro da pasta
                        lista_arquivos = listdir(pasta_de_imagens)
                        # # Selecionando um arquivo aleatório da lista
                        arquivo_aleatorio = random.choice(lista_arquivos)
                        caminho_da_imagem = path.join(pasta_de_imagens, arquivo_aleatorio)
                        imagem = Image.open(caminho_da_imagem)
                        with NamedTemporaryFile(suffix='.jpg') as arquivo_temporario:
                            imagem.save(arquivo_temporario.name)
                            arquivo_temporario.seek(0)
                            bot_token.sendPhoto(chat_id=chat_id, photo=arquivo_temporario)
                        # bot_token.sendMessage(chat_id, str("Está quase Terminando, só falta mais duas dicas."))
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("5ᵃ DICA", callback_data='quinta_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        #print(keyboard)
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                        break

                    # Quinto Exemplo
                    elif texto == '/iarabotquintadica':
                        # from PIL import Image
                        pasta_de_imagens = "./imagens/dica_5"
                        # Obtendo a lista de arquivos dentro da pasta
                        lista_arquivos = listdir(pasta_de_imagens)
                        # # Selecionando um arquivo aleatório da lista
                        arquivo_aleatorio = random.choice(lista_arquivos)
                        caminho_da_imagem = path.join(pasta_de_imagens, arquivo_aleatorio)
                        imagem = Image.open(caminho_da_imagem)
                        with NamedTemporaryFile(suffix='.jpg') as arquivo_temporario:
                            imagem.save(arquivo_temporario.name)
                            arquivo_temporario.seek(0)
                            bot_token.sendPhoto(chat_id=chat_id, photo=arquivo_temporario)
                        # bot_token.sendMessage(chat_id, str("Está quase Terminando, só falta mais duas dicas."))
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("6ᵃ DICA", callback_data='sexta_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        #print(keyboard)
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão \nabaixo para \nproceguir"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                        break


                    # Sexto Exemplo
                    elif texto == '/iarabotsextadica':
                        pasta_de_imagens = "./imagens/dica_6"
                        # Obtendo a lista de arquivos dentro da pasta
                        lista_arquivos = os.listdir(pasta_de_imagens)
                        # # Selecionando um arquivo aleatório da lista
                        arquivo_aleatorio = random.choice(lista_arquivos)
                        caminho_da_imagem = os.path.join(pasta_de_imagens, arquivo_aleatorio)
                        imagem = Image.open(caminho_da_imagem)
                        with NamedTemporaryFile(suffix='.jpg') as arquivo_temporario:
                            imagem.save(arquivo_temporario.name)
                            arquivo_temporario.seek(0)
                            bot_token.sendPhoto(chat_id=chat_id, photo=arquivo_temporario)
                        # bot_token.sendMessage(chat_id, str("Agora va para ultuma dica."))
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("7ᵃ DICA", callback_data='setima_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))
                        break

                    elif texto.lower() in ('2', 'aprender como analisar um texto para não cair em fake news'):
                        print()
                        #TODO Remover
                    """else:
                        # Utilização de Chatgpt com python
                        openai.api_key = ""
                        modelo = "text-davinci-003"
                        pergunta = texto
                        resposta = openai.Completion.create(
                            engine=modelo,
                            prompt=pergunta,
                            max_tokens=1024
                        )
                        print(resposta.choices[0].text)
                        bot_token.sendMessage(chat_id, resposta.choices[0].text)"""



        # DICAS A PARTIR DE UM CLIQUE NO BOTÃO
        if 'callback_query.from.first_name' in df.columns:
            if "callback_query.data" in df.columns:
                bot_token = telepot.Bot(TELEGRAM_TOKEN)
                lista = df["callback_query.from.id"].tolist()
                # converter em string
                chat_id = str(lista)
                # Retirar os colchetes
                chat_id = str(chat_id).strip('[]')
                for i in range(len(df)):
                    text_dica = df.loc[i, "callback_query.data"]
                    if text_dica == 'botao_clicado':
                        message_dica = "*1⃣ => Você verificou fonte e autor?*" \
                                       "\n\nTextos de desinformação não costumam ter fontes e autores assinando o texto," \
                                       " muitas vezes são criadas em perfis de redes sociais que desejam espalhar desinformação. " \
                                       " Ou são compartilhadas a partir de sites criados apenas com essa finalidade," \
                                       " sem renome ou respaldo na mídia tradicional." \
                                       "\n\nFrequentemente, sites, blogs e canais no Youtube são criados exclusivamente para propagar desinformação." \
                                       " Cuidado, muitas vezes esses conteúdos são espalhados por perfis falsos ou inautênticos," \
                                       " por isso sempre verifique a fonte do conteúdo." \
                                       "\n\nPor exemplo, se você fizer uma busca rápida no Google poderá observar que eles não existem (foram inventados)." \
                                       "\n\nSe quiser ver exemplo deste tipo de conteúdo, clique no link abaixo." \
                                       "\n\nVeja exemplo:👉 /iarabotprimeiradica"
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")

                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("2ᵃ DICA", callback_data='segunda_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo para segunda dica"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'segunda_dica':
                        message_dica = "*2⃣ => O título é muito chamativo?*" \
                                       "\n\nTítulos chamativos que evoquem sentimento de revolta ou descontentamento" \
                                       " fazem parte de uma tática dos criadores de desinformação para chamar atenção " \
                                       " provocar medo ou indignação e criar revolta no leitor." \
                                       "\n\nNão somente o título como o corpo do texto muitas vezes é repleto de palavras e frases " \
                                       " que preveem grandes catástrofes ou conquistas, além de seu conteúdo incitar emoções fortes como raiva ou tristeza." \
                                       "\n\nAqui está um exemplo deste tipo de conteúdo" \
                                       "\nVeja exemplo:👉 /iarabotsegundadica\n\n"
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("3ᵃ DICA", callback_data='terceira_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo para proceguir"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'terceira_dica':
                        message_dica = "*3⃣ => Você leu o texto completo?*" \
                                       "\n\nÉ importante ler o texto e não apenas o título." \
                                       " Muitas vezes os autores de notícias falsas criam um texto com informações desconexas" \
                                       " ou apenas cópias de notícias comuns confiando que a maioria dos leitores irão ler apenas o título." \
                                       " Por isso leia a matéria completa antes de compartilha-lo ou tirar sua conclusões." \
                                       "\n\nFique ligad@! Não se deixe enganar. Aproveite e verifique se o texto contém erros gramaticais." \
                                       " Em geral, os conteúdos contendo desinformação possuem erros gramaticais," \
                                       " uma vez que não foram produzidos por jornalistas da imprensa tradicional isso pode indicar a falta de profissionalismo" \
                                       " e justamente a possibilidade de ser uma notícia falsa. " \
                                       "\n\nVeja exemplo:👉 /iarabotterceiradica\n\n"
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("4ᵃ DICA", callback_data='quarta_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'quarta_dica':
                        message_dica = "*4⃣ => Você verificou a data da notícia?*" \
                                       "\n\nAlgumas vezes autores de desinformação tentam enganar os leitores utilizando notícias reais " \
                                       " porém em outro contexto temporal, utilizando notícias antigas, isto é eles compartilham novamente uma notícia como se fossem recentes." \
                                       "\n\nVai por mim, verifique a data da publicação para garantir que a notícia seja atual." \
                                       "\n\nVeja exemplo:👉 /iarabotquartadica\n\n"
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("5ᵃ DICA", callback_data='quinta_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "clique no botão abaixo para proceguir para quinta dica"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'quinta_dica':
                        message_dica = "*5⃣ => Você verificou os nomes dos especialistas citados em algum buscador?*" \
                                       "\n\nÉ comum em conteúdo desinformativo utilizarem nomes de supostos especialistas para tentar dar respaldo a notícia," \
                                       " porém muitas vezes esses especialistas não existem ou não possuem renome na comunidade científica." \
                                       "\n\nNeste caso  procure por outras fontes confiáveis Se não encontrar confirmação," \
                                       " é possível que o conteúdo seja falso." \
                                       "\n\nVeja exemplo:👉 /iarabotquintadica\n\n"
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("6ᵃ DICA", callback_data='sexta_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo para proceguir"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'sexta_dica':
                        message_dica = "*6⃣ => Você notou o incentivo ao compartilhamento desta notícia?*" \
                                       "\n\nSe a notícia for complexa pela questões técnicas ou científicas," \
                                       " consulte fontes confiáveis nessa área ou especialistas em detecção automática de desinformação com eu para obter um esclarecimento. " \
                                       "\n\nOs autores de desinformação desejam que seu conteúdo atinja o máximo de pessoas possíveis," \
                                       " então pedem aos leitores que compartilhem de forma veemente utilizando termos fortes." \
                                       " como por exemplo." \
                                       "\n\nVeja exemplo:👉 /iarabotsextadica\n\n"
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")
                        # Criando um botão com texto "Clique aqui!"
                        button = InlineKeyboardButton("7ᵃ DICA", callback_data='setima_dica')
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup([[button]])
                        # Envia a mensagem com o teclado
                        mensagem = "Clique no botão abaixo"
                        # bot_token.sendMessage(chat_id=123456789, text=mensagem, reply_markup=keyboard.json.dumps())
                        bot_token.sendMessage(chat_id, mensagem,
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'setima_dica':
                        message_dica = "*7⃣ => Você verificou se a notícia saiu nas grandes mídias?*" \
                                       "\n\nNotícias importantes saem em mais de um canal comunicativo da imprensa e grande mídia," \
                                       " então verifique se  o mesmo contéudo é publicado em diferentes meios de comunicação de notícias confiáveis," \
                                       " como: G1, UOL, R7, Folha, Estadão, Terra, BBC e CNN." \
                                       "\n\nAh! Você pode também certificar se essa notícia já foi verificada pelas agências de checagem. " \
                                       " Seguem algumas que eu recomendo bastante: Aos Fatos, Lupa, Fato ou Fake, FactCheck.org."\
                                       "\n\nAo pesquisar em buscadores se a notícia não aparece em sites de renome isso pode indicar que " \
                                       " o mesmo precisa ser verificado e é provável que exista uma desinformação."
                        bot_token.sendMessage(chat_id, message_dica, parse_mode="Markdown")
                        # Criando um botão com texto "Clique aqui!"
                        buttonfim = InlineKeyboardButton("Encerrar", callback_data='finalisação')
                        buttoninicio = InlineKeyboardButton("Menu Inicial", callback_data='inicio')
                        button = [[buttonfim, buttoninicio]]
                        # Adicionando o botão a um teclado em linha
                        keyboard = InlineKeyboardMarkup(button)
                        # Envia a mensagem com o teclado
                        mensagem = "*Como deseja seguir?* \nUse os botões abaixo para continuar"
                        bot_token.sendMessage(chat_id, mensagem, parse_mode="Markdown",
                                              reply_markup=json.dumps(keyboard.to_dict()).encode('utf-8'))

                    elif text_dica == 'finalisação':
                        message_fim = "Meus parabéns pelo mini-curso sobre Desinformação." \
                                      "\nSe você aplicar essas dicas que acabou de aprender na sua vida cotidiana," \
                                      " estará preparado(a) para identificar desinformação e ajudar a combate-la." \
                                      "\n\nSe você gostou das minhas dicas, compartilhe este link t.me/IAra_UFC_bot ," \
                                      "para que eu possa ajudar mais pessoas."
                        bot_token.sendMessage(chat_id, message_fim)

                    elif text_dica == 'inicio':
                        bot_token.sendMessage(chat_id,
                                              str("Certo!"
                                                  "\n\nPara iniciar, escolha uma das opções a seguir:"
                                                  "\n\n1⃣ => Verificação automática de conteúdo."
                                                  "\n\n2⃣ => Aprender como analisar um conteudo para não cair em fake news."
                                                  "\n\n3⃣ => Não desejo utilizar o chatbot agora, obrigad@.."
                                                  "\n\nDigite o número correspondente a sua ação desejada."))
        return json.loads(resultado.content)


# bot = Bot_telegram()
# bot.Iniciar()
