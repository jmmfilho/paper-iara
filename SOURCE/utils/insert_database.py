import os
from config import *

# CONECTAR BANCO DE DADOS
def conect_database():

    conexao = 'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}'.format(
                DB_USER=DB_USER,
                DB_PASSWORD=DB_PASSWORD,
                DB_HOST=DB_HOST,
                DB_PORT=DB_PORT,
                DB_DATABASE=DB_DATABASE)
    return conexao
