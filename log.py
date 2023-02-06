import logging
import os


class Log():
    def __init__(self):
        currentFile = os.path.abspath(__file__)
        baseDir = os.path.dirname(currentFile)
        logging.basicConfig(filename=os.path.join(baseDir, 'pyrectus.log'), level=logging.INFO,
                                format='%(asctime)s %(levelname)s %(message)s')

    def info(self, message=''):
        if message:
            logging.info(message)

    def error(self, message=''):
        if message:
            logging.error(message)

    def warning(self, message=''):
        if message:
            logging.warning(message)


if __name__ == '__main__':
    Log().info('test')