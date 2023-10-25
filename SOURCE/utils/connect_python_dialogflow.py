from google.cloud import dialogflow_v2 as dialogflow
from os import environ


def agent_dialogflow_to_python(texto):
    environ["GOOGLE_APPLICATION_CREDENTIALS"] = "ga.json"
    client = dialogflow.SessionsClient()
    session = client.session_path(project="telegrambot-kjis", session="me")
    text_input = dialogflow.TextInput(text=texto, language_code="pt-BR")
    query_input = dialogflow.QueryInput(text=text_input)
    response = client.detect_intent(query_input=query_input, session=session)
    #dialogue = (response.query_result.fulfillment_text)
    return response
