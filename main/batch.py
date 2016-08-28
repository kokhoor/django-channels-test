import logging
import time

logger = logging.getLogger('email')


def send_invite(message):
    logger.info("We receive a request to send email to: " + message.get('email'))
    logger.info("Message: " + message.get('message'))
    time.sleep(10)
    logger.info("Email sent successfully!")
