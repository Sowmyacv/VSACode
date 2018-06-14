"""
Main file for all the utilities of Virtual Sever

Method:

get_utils_path - get the utils path of VSA Automation

get_testdata_path - path where testdata needs to copied
"""

import os
import base64
from AutomationUtils import logger
from Cryptodome.Cipher import AES
from Cryptodome import Random

UTILS_PATH = os.path.dirname(os.path.realpath(__file__))
BLOCK_SIZE = 16
key = b'515173A5C402A03398D79B5353B2A080'


def get_testdata_path(machine):
    """
    get the test data path provided base directory

    Args:

        machine         (obj)   - Machine object of controller

    returns:
        _test_data_path (str)   - Test data Path where test data can be generated
        False           (bool)  - if testdata path cannot be retreived

    Exception:
        if failed to create directory

    """
    log = logger.get_log()
    try:
        _vserver_path = os.path.dirname(UTILS_PATH)
        _testdata_path = os.path.join(_vserver_path, "TestCases", "TestData")

        log.info("checking if directory exist %s" % _testdata_path)

        if not machine.check_directory_exists(_testdata_path):
            machine.create_directory(_testdata_path)

        return _testdata_path.replace('/', '\\')

    except Exception:
        log.exception("Error: can't find the VirtualServer utils Path")
        return False


def find_live_browse_db_file(machine, db_path):
    """

    :param machine: Machine object of MA machine used for live browse
    :param db_path: DB path where the live browse db is located
    :return:
        db_name :   (str)   : name of the db used in live browse

    Raise:
        Exception if DB file is not found
    """
    log = logger.get_log()
    try:

        file_name = None
        file_in_path = machine.get_files_in_path(db_path)
        if isinstance(file_in_path, str):
            file_in_path = [file_in_path]
        for each_file in file_in_path:
            if each_file.strip().endswith(".db"):
                file_name = each_file
                break

        if file_name is None:
            raise Exception("no file found with that extension")

        return os.path.join(db_path, file_name)

    except Exception as err:
        log.exception("An error Occurred in getting live browse db path")
        raise err


def encode_password(message):
    """
    :param value: value of the text needed to be encoded
    :return: encoded value of the password
    """

    if not isinstance(message, bytes):
        message = message.encode()
    IV = Random.new().read(BLOCK_SIZE)
    aes = AES.new(key, AES.MODE_CFB, IV)
    return base64.b64encode(IV + aes.encrypt(message)).decode()


def decode_password(message):
    """
        :param value: value of the text needed to be decoded
        :return: decoded value of the password
        """
    encrypted = base64.b64decode(message)
    IV = encrypted[:BLOCK_SIZE]
    aes = AES.new(key, AES.MODE_CFB, IV)
    cipher = aes.decrypt(encrypted[BLOCK_SIZE:])
    return cipher.decode("utf-8")
