from controllers.controller_whatsapp import get_message, send_message


if __name__ == '__main__':
    print('Iniciando whatsapp iarabot')

    loop = True
    while loop:
        msg = get_message()
        if msg:
            send_message(msg)