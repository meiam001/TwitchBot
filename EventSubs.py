import os
import requests
import json

class Events:

    def __init__(self):
        self.TWITCH_MESSAGE_ID = 'Twitch-Eventsub-Message-Id'
        self.TWITCH_MESSAGE_TIMESTAMP = 'Twitch-Eventsub-Message-Timestamp'
        self.TWITCH_MESSAGE_SIGNATURE = 'Twitch-Eventsub-Message-Signature'
        self.HMAC_PREFIX = 'sha256='
        self.secret = self.get_secret()

    def authenticate(self, request):
        response_sig = request.headers[self.TWITCH_MESSAGE_SIGNATURE]
        message = self.getHmacMessage(request)

    @staticmethod
    def get_secret():
        return os.urandom(32)

    def getHmacMessage(self, request: requests.request):
        return (request.headers[self.TWITCH_MESSAGE_ID] +
            request.headers[self.TWITCH_MESSAGE_TIMESTAMP] +
            json.dumps(request.body))

    def create_webhook_subscription(self, streamer_id, webhook_callback, secret):
        """

        :param streamer_id:
        :param webhook_callback:
        :param secret:
        :return:
        """
        webhook_payload = {}
        webhook_payload['type'] = "channel.follow"
        webhook_payload['version'] = "1"
        webhook_payload['condition'] = {"broadcaster_user_id": streamer_id}
        webhook_payload['transport'] = {"method": "webhook", "callback": webhook_callback, "secret": secret}

        print(json.dumps(webhook_payload))
        my_headers = self.headers
        my_headers['Content-Type'] = "application/json"

        response = requests.post(
            "https://api.twitch.tv/helix/eventsub/subscriptions",
            headers=my_headers,
            data=json.dumps(webhook_payload)
        )

        print(response)
        print(response.text)
