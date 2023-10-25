import os

# Postgres
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', '')
DB_DATABASE = os.getenv('DB_DATABASE', '')
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Redis
REDIS_HOST = os.getenv('REDIS_HOST', '')
REDIS_PORT = os.getenv('REDIS_PORT', )
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = os.getenv('REDIS_DB', 0)
WHATSAPP_LIST_COLETA = os.getenv('WHATSAPP_LIST_COLETA', '')
WHATSAPP_LIST_DIFUSAO = os.getenv('WHATSAPP_LIST_DIFUSAO', '')

# Whatsapp
WHATSAPP_API = os.getenv('WHATSAPP_API', '')
URL_BASE_IARABOT = os.getenv('URL_BASE_IARABOT', '')


# Telegram
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
URL_CLASSIFICADOR_FAROLDIGITAL = os.getenv('URL_CLASSIFICADOR_FAROLDIGITAL', '')



# Frases para dar probabilidade aos usuários
frases = ["A probabilidade do conteúdo  analisado conter desinformação é de:",
          "A probabilidade do seu conteúdo conter desinformação, após minha análise é de:",
          "Após analisar seu conteúdo, aqui está a probabilidade dele conter desinformação:",
          "O seu conteúdo analizado apresenta uma probabilidade de conter desinformação do nivel:",
          "O nivel probabilístico do seu conteudo ser desinformação é de:"
]
