import requests


class TelegramNotifier:
    URL = 'https://api.telegram.org/bot'
    TOKEN = '435390630:AAFoLa89q6BWhQWrHY_ab0UTfqVnbKmlNDM'

    def notify(self, message):
        requests.post('{}{}{}'.format(TelegramNotifier.URL, TelegramNotifier.TOKEN, '/sendMessage'),
                      data={'chat_id': 358750312, 'text': message})