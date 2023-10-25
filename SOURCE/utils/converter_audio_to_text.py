import speech_recognition as sr


def transcribe_audio(arquivo):
    r = sr.Recognizer()
    with sr.AudioFile(arquivo) as source:
        audio = r.record(source)
        texto_audio = r.recognize_google(audio, language="pt-BR")
        return texto_audio

