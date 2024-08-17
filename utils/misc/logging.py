import logging

logging.basicConfig(
    format="%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s",
    level=logging.INFO,
    # Can be changed to another logging level
    # level=logging.DEBUG,
)
