from channels.consumer import SyncConsumer

import logging
import time

logger = logging.getLogger('email')


class SendEmailConsumer(SyncConsumer):
    def send_invite(self, message):
        logger.info("We receive a request to send email to: " + message.get('email'))
        logger.info("Message: " + message.get('message'))
        time.sleep(10)
        logger.info("Email sent successfully!")

