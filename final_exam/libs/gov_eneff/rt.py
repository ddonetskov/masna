# data access
import sqlalchemy as sa

# data handling
import json

# system tools
import logging
import os
import sys
import time

"""
Prepare the runtime configuration for all other modules
"""

config    = None
logger    = None
db_engine = {}

def init_logger():

    """Initialization of the logging service
    :return:            logger
    """

    # create logger
    logger = logging.getLogger('main')

    if (logger.hasHandlers()):
        logger.handlers.clear()

    logger.addHandler(logging.StreamHandler(sys.stdout))
    logger.handlers[-1].setFormatter(logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s',
                                                       datefmt='%Y-%m-%d %H:%M:%S'))

    logger.setLevel(logging.DEBUG)

    return(logger)

def init_config(config_file = ''):

    """Initialization of the execution context

     :param conf_file:  path to the configuration file, it reconstructed from the env. settings if empty
     :returns:          config
    """

    logger.debug("Trying to load the configuration file %s" % config_file)

    # reading the configuration file
    if not os.path.isfile(config_file):
        logger.error("The configuration file (%s) not found." % config_file)
        sys.exit(1)

    with open(config_file, encoding='utf-8') as f:
        config = json.load(f)

    logger.info("The configuration file has been loaded.")

    return(config)


def init(config_file = ''):

    global logger
    logger = init_logger()

    global config
    config = init_config(config_file)

    logger.setLevel(config['common']['log_level'])

    ################################################################################
    # Database engine initialization

    global db_engine
    db_engine = {}

    for key, item in config['db'].items():
        try:
            db_engine[key] = sa.create_engine(item)
        except sa.exc.NoSuchModuleError:
            logger.error('Could not load the module for creating the SQLAlchemy engine for %s' % key)

    return
