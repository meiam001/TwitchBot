import logging

logging.basicConfig(
    filename='app.log',
    filemode='a+',
    format='%(asctime)s - %(filename)s - %(funcName)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)
