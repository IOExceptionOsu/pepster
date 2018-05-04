import logging
import logging.handlers
import os
import traceback
import urllib.request
from tempfile import NamedTemporaryFile
from urllib.request import urlretrieve


def create_logger(name):
    L = logging.getLogger(name)
    L.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler("logs/{}.log".format(name), maxBytes=20000, backupCount=5)
    L.addHandler(handler)
    return L


chat_logger = create_logger("chatlogger")
queue_logger = create_logger("queuelogger")

def get_attachment(message):
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0')]
    urllib.request.install_opener(opener)

    tmpdir = os.path.join(os.getcwd(), "tmp")
    logger = logging.getLogger()
    logger.error("ATTACHMENTS:" + repr(message.attachments))
    if not message.attachments:
        return None
    f = NamedTemporaryFile(dir=tmpdir, suffix=".png", delete=False)
    attachment = message.attachments[0]
    logger.error("getting url: " + attachment["proxy_url"])
    try:
        p, _ = urlretrieve(attachment["proxy_url"], f.name)
        logger.error("p = " + p + " / " + f.name)
        return f
    except Exception:
        logger.error(traceback.format_exc())
        return None
