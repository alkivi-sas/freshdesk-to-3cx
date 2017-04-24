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
import re
import atexit

from alkivi.logger import Logger
from scriptlock import Lock
from freshdesk.api import API
from models import Phonebook, IPBXBinder

# Define the global logger
logger = Logger(min_log_level_to_mail=logging.WARNING,
                min_log_level_to_save=logging.DEBUG,
                min_log_level_to_print=logging.INFO,
                emails=['monitoring@alkivi.fr'])


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
        if _need_sync(contact):
            _sync_contact_to_3cx(contact, freshdesk_client, ipbx_client)
    logger.del_loop_logger()


def _need_sync(contact):
    """
    According to the contact return True or False

    Checks :
      - We want to sync only if mobile or phone is present.
      - contact.phone != contact.name
      - company_id is present
    """
    if not contact.phone and not contact.mobile:
        return False
    elif contact.phone == contact.name:
        return False
    elif not contact.company_id:
        return False
    else:
        return True


def _sync_contact_to_3cx(contact, freshdesk_client, ipbx_client):
    """
    Sync a unique contact between freshdesk in 3CX.

    Check if the contact exists in 3CX based on phonenumber.
    Update other field if necessary.
    Using SQLAlchemy Model of 3CX contacts.
    """
    logger.debug('Going to sync {0}'.format(contact.name))
    company = freshdesk_client.companies.get_company_from_contact(contact)
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
    data = _format_contact(contact)

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
    data = _format_contact(real_contact)

    should_update = False
    for k, v in data.items():
        if getattr(ipbx_contact, k) != v:
            logger.debug('Update {0} to {1}'.format(k, v))
            setattr(ipbx_contact, k, v)
            should_update = True

    if should_update:
        if DRY:
            logger.debug('DRY: would have update the contact with data')
        else:
            session = ipbx_client.get_session()
            session.add(ipbx_contact)
            session.commit()
            logger.info('Contact {0} updated'.format(real_contact.name))


def _format_contact(contact):
    """Parse the contact to extract data."""
    data = {
        'company': contact.company,
        'email': contact.email,
        'fkidtenant': 1,
        'other': contact.id,
    }

    name_split = contact.name.split(' ')
    if len(name_split) > 1:
        data['firstname'] = name_split[0]
        data['lastname'] = ' '.join(name_split[1:])
    else:
        data['firstname'] = contact.name
        data['lastname'] = 'Inconnu'

    regexp = r"(\s+|\xc2+)"
    if contact.mobile:
        test_mobile = re.sub(regexp, "", contact.mobile, flags=re.UNICODE)
        test_mobile = _format_phone_number(test_mobile)
    else:
        test_mobile = ''

    if contact.phone:
        test_business = re.sub(regexp, "", contact.phone, flags=re.UNICODE)
        test_business = _format_phone_number(test_business)
    else:
        test_business = ''

    if _is_phone_mobile(test_mobile):
        data['mobile'] = test_mobile
        data['business'] = test_business
    elif _is_phone_mobile(test_business):
        data['mobile'] = test_business
        data['business'] = test_mobile
    else:
        data['mobile'] = test_mobile
        data['business'] = test_business

    return data


def _is_phone_mobile(number):
    """Return True or False according to tests."""
    test = ['+336', '+337', '06', '07', '00336', '00337']
    for start in test:
        if number.startswith(start):
            return True
    return False


def _format_phone_number(number):
    """Always add a +33 in front of the number."""
    logger.debug('Going to format {0}'.format(number))
    if number.startswith('+'):
        return number
    elif number.startswith('0'):
        if len(number) == 10:
            return '+33{0}'.format(number[1:])
        else:
            logger.warning('Weird number {0} '.format(number) +
                           'not formatting.')
            return number


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exception:
        logger.exception(exception)
