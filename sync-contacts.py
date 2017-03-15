#!/usr/bin/env python
# -*-coding:utf-8 -*

"""
Script to do CTI with 3CX and Freshdesk on macOS
"""

import sys
import logging
import configparser
import getopt
import requests
import json
import os

from freshdesk.api import API
from models import Phonebook, IPBXBinder

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(ROOT_DIR, 'freshdesk-to-3cx.log')
logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
logger = logging.getLogger(__name__)

def usage():
    """Small helper to use when --help is pass
    """
    print('Usage: '+sys.argv[0]+' -h -d -your own options'+'\n')
    print('-h     --help            Display help')
    print('-d     --debug           Enable debug')

def main(argv):
    """Where the magic happen
    """

    # Variable that opt use
    try:
        opts, dummy_args = getopt.getopt(argv, 'hd',
                ['help', 'caller_number=', 'debug'])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ['-h', '--help']:
            usage()
            sys.exit()
        elif opt in ['-d', '--debug']:
            logger.setLevel(logging.DEBUG)
            logger.debug('Debug activated')

    logger.info('Loading conf file')

    config_file = os.path.join(ROOT_DIR, '.config')
    logger.info(config_file)
    config = configparser.RawConfigParser()
    config.read(config_file)

    # Freshdesk
    domain = config.get('freshdesk', 'domain')
    api_key = config.get('freshdesk', 'api_key')
    agent_id = int(config.get('freshdesk', 'agent_id'))

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
    for contact in contacts:
        if _need_sync(contact):
            _sync_contact_to_3cx(contact, freshdesk_client, ipbx_client)


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
    test = session.query(Phonebook).filter(Phonebook.other==str(contact.id)).first()
    if not test:
        _create_contact(contact, ipbx_client)
    else:
        _update_contact(contact, ipbx_client)
    exit(0)

def _create_contact(contact, ipbx_client):
    """Create the contact in database."""

    # We have to modulate id to match postgres

    data = {
            'firstname': contact.company,
            'lastname': contact.name,
            'company': contact.company,
            'mobile': contact.mobile,
            'business': contact.phone,
            'email': contact.email,
            'fkidtenant': 1,
            'other': contact.id,
        }

    entry = Phonebook(**data) 
    session = ipbx_client.get_session()
    session.add(entry)
    session.commit()
                

def _update_contact(contact, ipbx_client):
    """Update the contact in database."""
    pass




if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as exception:
        print(exception)
