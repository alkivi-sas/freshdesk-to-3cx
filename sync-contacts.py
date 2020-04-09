#!/usr/bin/env python
# -*-coding:utf-8 -*

"""
Script to do CTI with 3CX and Freshdesk on macOS
"""

import sys
import logging
import configparser
import getopt
import os
import atexit

from alkivi.logger import Logger
from scriptlock import Lock
from freshdesk.api import API
from models import Phonebook, IPBXBinder
from helpers import need_sync, format_contact, set_logger

# Define the global logger
logger = Logger(min_log_level_to_mail=logging.WARNING,
                min_log_level_to_save=logging.DEBUG,
                min_log_level_to_print=logging.INFO,
                emails=['monitoring@alkivi.fr'])
set_logger(logger)


LOCK = Lock()
atexit.register(LOCK.cleanup)

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
DRY = False


def usage():
    """Small helper to use when --help is pass
    """
    print('Usage: '+sys.argv[0]+' -h -d -your own options'+'\n')
    print('-h     --help            Display help')
    print('-d     --debug           Enable debug')
    print('       --dry  --dryrun   Dont do shit')


def main(argv):
    """Where the magic happen
    """

    # Variable that opt use
    try:
        opts, dummy_args = getopt.getopt(argv, 'hd', ['help',
                                                      'debug',
                                                      'dry', 'dryrun'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit()
        elif opt in ['--dry', '--dryrun']:
            global DRY
            DRY = True
        elif opt in ['-d', '--debug']:
            logger.set_min_level_to_print(logging.DEBUG)
            logger.debug('Debug activated')
            logger.set_min_level_to_mail(None)
            logger.set_min_level_to_syslog(None)

    logger.info('Loading conf file')

    config_file = os.path.join(ROOT_DIR, '.config')
    logger.info(config_file)
    config = configparser.RawConfigParser()
    config.read(config_file)

    # Freshdesk
    domain = config.get('freshdesk', 'domain')
    api_key = config.get('freshdesk', 'api_key')

    # 3CX
    db = config.get('3cx', 'database')
    dbuser = config.get('3cx', 'user')
    dbpass = config.get('3cx', 'password')

    # Do your code here
    logger.info("Program Start")

    # Setup Freshdesk API
    freshdesk_client = API(domain, api_key, version=2)
    ipbx_client = IPBXBinder(db, dbuser, dbpass)

    contacts = freshdesk_client.contacts.list_contacts()

    logger.new_loop_logger()
    for contact in contacts:
        logger.new_iteration(prefix=contact.name)
        if need_sync(contact):
            _sync_contact_to_3cx(contact, freshdesk_client, ipbx_client)
    logger.del_loop_logger()


def _sync_contact_to_3cx(contact, freshdesk_client, ipbx_client):
    """
    Sync a unique contact between freshdesk in 3CX.

    Check if the contact exists in 3CX based on phonenumber.
    Update other field if necessary.
    Using SQLAlchemy Model of 3CX contacts.
    """
    logger.debug('Going to sync {0}'.format(contact.name))
    company_id = contact.company_id
    if not company_id:
        logger.debug('No company, skipping')
    company = freshdesk_client.companies.get_company(company_id)
    setattr(contact, 'company', company.name)

    # Match id of the contact
    session = ipbx_client.get_session()
    ipbx_contact = session.query(Phonebook).filter(
            Phonebook.other == str(contact.id)).first()
    if not ipbx_contact:
        _create_contact(contact, ipbx_client)
    else:
        _update_contact(ipbx_contact, contact, ipbx_client)


def _create_contact(contact, ipbx_client):
    """Create the contact in database."""
    logger.debug('Creating contact')
    data = format_contact(contact)

    ipbx_contact = Phonebook(**data)
    if DRY:
        logger.debug('DRY: would have created a contact with data', data)
    else:
        session = ipbx_client.get_session()
        session.add(ipbx_contact)
        session.commit()
        logger.info('Contact {0} created'.format(contact.name))


def _update_contact(ipbx_contact, real_contact, ipbx_client):
    """Update the contact in database."""
    logger.debug('Updating contact')
    data = format_contact(real_contact)

    should_update = False
    for k, v in data.items():
        test_v = getattr(ipbx_contact, k)
        logger.debug('Testing key {0}: '.format(k) +
                     'Freshdesk: {0} '.format(v) +
                     '3CX: {0}'.format(test_v))
        if test_v != v:
            logger.info('Updating {0}: {1} => {2}'.format(k,
                                                          test_v,
                                                          v))
            setattr(ipbx_contact, k, v)
            should_update = True

    if should_update:
        if DRY:
            logger.info('DRY: would have update the contact with data')
        else:
            session = ipbx_client.get_session()
            session.add(ipbx_contact)
            session.commit()
            logger.info('Contact {0} updated'.format(real_contact.name))
    else:
        logger.info('No need to update')


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exception:
        logger.exception(exception)
