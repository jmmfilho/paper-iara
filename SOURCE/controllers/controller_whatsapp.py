import json
import logging
import random
from os import path, listdir
from urllib import request

import PyPDF2
import moviepy.editor as mpe
from utils.whatsapp_imagem_tratador import realizar_upload, extrairMime_type, nomeSemExtencao

import redis
from docx2txt import process
from pydub import AudioSegment

from utils.classifier import classifier_bot
from utils.connect_python_dialogflow import agent_dialogflow_to_python
from utils.converter_audio_to_text import transcribe_audio
from utils.extract_text_from_image import extract_text_from_image
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD, WHATSAPP_LIST_COLETA, WHATSAPP_LIST_DIFUSAO, \
    WHATSAPP_API, frases


conn_redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                         password=REDIS_PASSWORD, charset="utf-8", decode_responses=True)


def get_message():
    try:
        msg_redis = conn_redis.lpop(WHATSAPP_LIST_COLETA)
        if msg_redis:
            msg_dict = json.loads(msg_redis)
            return msg_dict
    except Exception as e:
        msg_erro = '[ERRO]: {}'.format(str(e))
        logging.error(msg_erro)
        return None


#TRATAMENTO DE MENSAGEM
def avaliarMandar(msg):
    nPalavras = len(msg['text_content'].split())
    n_formatado_int = 0
    if (nPalavras > 20):
        classificacao = classifier_bot(msg['text_content'])
        n_formatado_float = "{:.2f}".format(float(classificacao))
        formatar_ponto = n_formatado_float.replace('.', '')
        # Formatar para numero inteiro
        n_formatado_int = int(formatar_ponto)
        # Formatar em percentual
        percentual = ("{}%".format(n_formatado_int))
        frase_aleatoria = random.choice(frases)
        msg['text_content'] = f"{frase_aleatoria} {percentual}"
    else:
        msg['text_content'] = "esta image não tem informmação o suficiente para ser avaliada"
    if '@g.us' not in msg['id_group']:
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    elif '@g.us' in msg['id_group'] and n_formatado_int>90:
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    else:
        print("não respondo grupo")
    return msg


def limparMensagem(msg):
    msg['message_type'] = "Texto"
    msg['media'] = ""
    msg['media_type'] = ""
    msg['media_md5'] = ""
    return msg

#erviços administrativos
#comunicação regis
#upload do arquivo por serviço
#edereço da midia

#CONVERSÃO DE ARQUIVOS
def extrairImagem(msg):
    arquvio = msg['media']

    #corrigir problema não enviando mensagens sem arquivo
    msg = limparMensagem(msg)
    msg['text_content'] = "aguarde enquanto avalio seu conteúdo"
    msg_json = json.dumps(msg)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    path_photo = '../baixados/imagens'
    caminho_imagem = path.join(path_photo, arquvio)
    photo_url = f"{WHATSAPP_API}file?name={arquvio}"
    request.urlretrieve(photo_url,caminho_imagem)
    texto_extraido = extract_text_from_image(caminho_imagem)
    msg['text_content'] = texto_extraido.replace("\n"," ")
    msg = avaliarMandar(msg)
    return msg


def extrairAudio(msg):
    arquvio = msg['media']
    media = msg['media_md5']
    msg = limparMensagem(msg)
    msg['text_content'] = "aguarde enquanto avalio seu conteúdo, pode demorar um pouco"
    msg_json = json.dumps(msg)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    path_audio = '../baixados/audio'
    caminho_audio = path.join(path_audio, arquvio)
    audio_url = f"{WHATSAPP_API}file?name={arquvio}"
    request.urlretrieve(audio_url, caminho_audio)
    arquivo = AudioSegment.from_file(caminho_audio)
    path_Wav = path.join(path_audio,f"{media}.wav")
    arquivo.export(path_Wav, format="wav")
    textoExtraido = transcribe_audio(path_Wav)
    msg['text_content'] = textoExtraido
    msg = avaliarMandar(msg)
    return msg


def extrairVideo(msg):
    arquvio = msg['media']
    media = msg['media_md5']
    msg = limparMensagem(msg)
    msg['text_content'] = "aguarde enquanto avalio seu conteúdo, pode demorar um pouco"
    msg_json = json.dumps(msg)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    path_video = '../baixados/video'
    caminho_video = path.join(path_video, arquvio)
    video_url = f"{WHATSAPP_API}file?name={arquvio}"
    request.urlretrieve(video_url, caminho_video)
    arquivo = mpe.VideoFileClip(caminho_video)
    pathWav = path.join(path_video, f"{media}.wav")
    arquivo.audio.write_audiofile(pathWav)
    textoExtraido = transcribe_audio(pathWav)
    msg['text_content'] = textoExtraido
    msg = avaliarMandar(msg)
    return msg


def extrairPDF(msg):
    arquvio = msg['media']
    media = msg['media_md5']
    msg = limparMensagem(msg)
    msg['text_content'] = "aguarde enquanto avalio seu conteúdo."
    msg_json = json.dumps(msg)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    path_doc = '../baixados/docs'
    caminho_doc = path.join(path_doc, arquvio)
    audio_url = f"{WHATSAPP_API}file?name={arquvio}"
    request.urlretrieve(audio_url, caminho_doc)
    arq_pdf = open(caminho_doc, 'rb')
    ler_pdf = PyPDF2.PdfReader(arq_pdf)
    # Página e o numero de página
    result_pdf = ""
    for n in range(len(ler_pdf.pages)):
        pagina = ler_pdf.pages[n]
        result_pdf = result_pdf + pagina.extract_text()
    msg['text_content'] = result_pdf
    msg = avaliarMandar(msg)
    return msg


def extrairTXT(msg):
    arquvio = msg['media']
    msg = limparMensagem(msg)
    msg['text_content'] = "aguarde enquanto avalio seu conteúdo."
    msg_json = json.dumps(msg)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    path_doc = '../baixados/docs'
    caminho_doc = path.join(path_doc, arquvio)
    audio_url = f"{WHATSAPP_API}file?name={arquvio}"
    request.urlretrieve(audio_url, caminho_doc)
    with open(caminho_doc, "r") as arquivo:
        data = arquivo.read()
        msg['text_content'] = data
        msg = avaliarMandar(msg)
    return msg


def extrairDoc(msg):
    arquvio = msg['media']
    msg = limparMensagem(msg)
    msg['text_content'] = "aguarde enquanto avalio seu conteúdo."
    msg_json = json.dumps(msg)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    path_doc = '../baixados/docs'
    caminho_doc = path.join(path_doc, arquvio)
    audio_url = f"{WHATSAPP_API}file?name={arquvio}"
    request.urlretrieve(audio_url, caminho_doc)
    resultado = process(caminho_doc)
    msg['text_content'] = resultado
    msg = avaliarMandar(msg)
    return msg


#DIALOGO
def inciarDialogo(msg, atual):
    resposta = msg
    texto = msg['text_content']
    msg = limparMensagem(msg)
    if texto == "DICA" or texto == "dica":
        if atual <=7:
            atual += 1
            responderDica(resposta,atual)
    resultado_dialogflow = agent_dialogflow_to_python(texto)
    dialogue = (resultado_dialogflow.query_result.fulfillment_text)
    if atual == 0 or resultado_dialogflow.query_result.intent.display_name == 'Negar':
        if resultado_dialogflow.query_result.intent.display_name == 'Negar':
            atual = 0
        if resultado_dialogflow.query_result.intent.display_name == "Menssagem de Boas Vindas":
            resposta  = limparMensagem(resposta)
            resposta['text_content']=dialogue
            msg_json = json.dumps(msg)
            conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        elif resultado_dialogflow.query_result.intent.display_name == "Educação Midiática":
            resposta = limparMensagem(resposta)
            resposta['text_content'] = dialogue
            msg_json = json.dumps(msg)
            conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
            resposta['text_content'] = "digite DICA para avançar para a próxima dica"
            msg_json = json.dumps(msg)
            conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        elif isinstance(dialogue, str) and dialogue != "":
            resposta = limparMensagem(resposta)
            resposta['text_content'] = dialogue
            msg_json = json.dumps(msg)
            conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    #msg['text_content']=texto
    #msg_json = json.dumps(msg)
    #conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
    if atual == 8:
        atual = 0
    while True:
        try:
            msg_redis = conn_redis.lpop(WHATSAPP_LIST_COLETA)
            if msg_redis:
                msg_dict = json.loads(msg_redis)
                if msg_dict['media_type']=='' and len(msg_dict['text_content'].split())<20:
                    inciarDialogo(msg_dict,atual)
                else :
                    send_message(msg_dict)
        except Exception as e:
            msg_erro = '[ERRO]: {}'.format(str(e))
            logging.error(msg_erro)
            return None


def enviarDicaAleatoria(pathPasta, msg):
    lista_arquivos = listdir(pathPasta)
    arquivo_aleatorio = random.choice(lista_arquivos)
    caminho_da_imagem = path.join(pathPasta, arquivo_aleatorio)
    nome_servidor = realizar_upload(caminho_da_imagem)
    nome_servidor = nome_servidor.replace('\'','')
    resposta = msg
    resposta['message_type']='Imagem'
    resposta['text_content']=''
    resposta['media']=nome_servidor
    resposta['media_type']=extrairMime_type(nome_servidor)
    resposta['media_md5']=nomeSemExtencao(nome_servidor)
    resposta['media_url']=f'https://localhost/file?name={nome_servidor}'
    #resposta['media_url']=nome_servidor
    msg_json = json.dumps(resposta)
    conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)


def responderDica(msg,atual):
    if atual == 1:
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
        msg['text_content']= message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        pasta_de_imagens = "./imagens/dica_1/"
        enviarDicaAleatoria(pasta_de_imagens,msg)
    elif atual == 2:
        message_dica = "*2⃣ => O título é muito chamativo?*" \
                       "\n\nTítulos chamativos que evoquem sentimento de revolta ou descontentamento" \
                       " fazem parte de uma tática dos criadores de desinformação para chamar atenção " \
                       " provocar medo ou indignação e criar revolta no leitor." \
                       "\n\nNão somente o título como o corpo do texto muitas vezes é repleto de palavras e frases " \
                       " que preveem grandes catástrofes ou conquistas, além de seu conteúdo incitar emoções fortes como raiva ou tristeza." \
                       "\n\nAqui está um exemplo deste tipo de conteúdo" \
                       "\nVeja exemplo:👉 /iarabotsegundadica\n\n"
        msg['text_content'] = message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        pasta_de_imagens = "./imagens/dica_2/"
        enviarDicaAleatoria(pasta_de_imagens, msg)
    elif atual == 3:
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
        msg['text_content'] = message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        pasta_de_imagens = "./imagens/dica_3/"
        enviarDicaAleatoria(pasta_de_imagens, msg)
    elif atual == 4:
        message_dica = "*4⃣ => Você verificou a data da notícia?*" \
                       "\n\nAlgumas vezes autores de desinformação tentam enganar os leitores utilizando notícias reais " \
                       " porém em outro contexto temporal, utilizando notícias antigas, isto é eles compartilham novamente uma notícia como se fossem recentes." \
                       "\n\nVai por mim, verifique a data da publicação para garantir que a notícia seja atual." \
                       "\n\nVeja exemplo:👉 /iarabotquartadica\n\n"
        msg['text_content'] = message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        pasta_de_imagens = "./imagens/dica_4/"
        enviarDicaAleatoria(pasta_de_imagens, msg)
    elif atual == 5:
        message_dica = "*5⃣ => Você verificou os nomes dos especialistas citados em algum buscador?*" \
                       "\n\nÉ comum em conteúdo desinformativo utilizarem nomes de supostos especialistas para tentar dar respaldo a notícia," \
                       " porém muitas vezes esses especialistas não existem ou não possuem renome na comunidade científica." \
                       "\n\nNeste caso  procure por outras fontes confiáveis Se não encontrar confirmação," \
                       " é possível que o conteúdo seja falso." \
                       "\n\nVeja exemplo:👉 /iarabotquintadica\n\n"
        msg['text_content'] = message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        pasta_de_imagens = "./imagens/dica_5/"
        enviarDicaAleatoria(pasta_de_imagens, msg)
    elif atual == 6:
        message_dica = "*6⃣ => Você notou o incentivo ao compartilhamento desta notícia?*" \
                       "\n\nSe a notícia for complexa pela questões técnicas ou científicas," \
                       " consulte fontes confiáveis nessa área ou especialistas em detecção automática de desinformação com eu para obter um esclarecimento. " \
                       "\n\nOs autores de desinformação desejam que seu conteúdo atinja o máximo de pessoas possíveis," \
                       " então pedem aos leitores que compartilhem de forma veemente utilizando termos fortes." \
                       " como por exemplo." \
                       "\n\nVeja exemplo:👉 /iarabotsextadica\n\n"
        msg['text_content'] = message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        pasta_de_imagens = "./imagens/dica_6/"
        enviarDicaAleatoria(pasta_de_imagens, msg)
    elif atual == 7:
        message_dica = "*7⃣ => Você verificou se a notícia saiu nas grandes mídias?*" \
                       "\n\nNotícias importantes saem em mais de um canal comunicativo da imprensa e grande mídia," \
                       " então verifique se  o mesmo contéudo é publicado em diferentes meios de comunicação de notícias confiáveis," \
                       " como: G1, UOL, R7, Folha, Estadão, Terra, BBC e CNN." \
                       "\n\nAh! Você pode também certificar se essa notícia já foi verificada pelas agências de checagem. " \
                       " Seguem algumas que eu recomendo bastante: Aos Fatos, Lupa, Fato ou Fake, FactCheck.org." \
                       "\n\nAo pesquisar em buscadores se a notícia não aparece em sites de renome isso pode indicar que " \
                       " o mesmo precisa ser verificado e é provável que exista uma desinformação."
        msg['text_content'] = message_dica
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)
        message_fim = "Meus parabéns pelo mini-curso sobre Desinformação." \
                      "\nSe você aplicar essas dicas que acabou de aprender na sua vida cotidiana," \
                      " estará preparado(a) para identificar desinformação e ajudar a combate-la." \
                      "\n\nSe você gostou das minhas dicas, compartilhe este link t.me/IAra_UFC_bot ," \
                      "para que eu possa ajudar mais pessoas."
        msg['text_content'] = message_fim
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)


def send_message(msg: dict):
    atual = 0
    if msg['media_type']=="image/jpeg":
        msg = extrairImagem(msg)
    elif msg['media_type']=="audio/mpeg":
        msg = extrairAudio(msg)
    elif msg['media_type']=="video/mp4":
        msg = extrairVideo(msg)
    elif msg['media_type']=="application/pdf":
        msg = extrairPDF(msg)
    elif msg['media_type']=="application/octet-stream":
        msg = extrairTXT(msg)
    elif msg['media_type']=='application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        msg = extrairDoc(msg)
    elif msg['media_type']=='' and len(msg['text_content'].split())>=20:
        texto = msg['text_content']
        msg = limparMensagem(msg)
        msg['text_content']=texto
        msg = avaliarMandar(msg)
    elif msg['media_type']=='' and len(msg['text_content'].split())<20 and '@g.us' not in msg['id_group']:
        inciarDialogo(msg,atual)
    elif '@g.us' not in msg['id_group']:
        msg = limparMensagem(msg)
        msg['text_content'] = {" Trabalhamos com seguintes formatos: "
                                "\nPDF, WORD, TXT, HTML, XML,jpg, png, MP4. mp3, waw, m4a, 3gp."
                                "\n \nOu Copiar o texto do seu documento e colar aqui."}
        msg_json = json.dumps(msg)
        conn_redis.rpush(WHATSAPP_LIST_DIFUSAO, msg_json)

