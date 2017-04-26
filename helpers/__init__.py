import logging
import re

logger = logging.getLogger(__name__)


def set_logger(l):
    """Hack to pass logger."""
    global logger
    logger = l


def need_sync(contact):
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


def format_name(name):
    """To capitalize correctly."""
    # Thanks python :)
    return name.title()


def format_contact(contact):
    """Parse the contact to extract data."""
    data = {
        'company': contact.company,
        'email': contact.email,
        'fkidtenant': 1,
        'other': str(contact.id),
    }

    name_split = contact.name.split(' ')
    if len(name_split) > 1:
        data['firstname'] = format_name(name_split[0])
        data['lastname'] = format_name(' '.join(name_split[1:]))
    else:
        data['firstname'] = format_name(contact.name)
        data['lastname'] = 'Inconnu'

    regexp = r"(\s+|\xc2+)"
    if contact.mobile:
        test_mobile = re.sub(regexp, "", contact.mobile, flags=re.UNICODE)
        test_mobile = format_phone_number(test_mobile)
    else:
        test_mobile = ''

    if contact.phone:
        test_business = re.sub(regexp, "", contact.phone, flags=re.UNICODE)
        test_business = format_phone_number(test_business)
    else:
        test_business = ''

    if is_phone_mobile(test_mobile):
        data['mobile'] = test_mobile
        data['business'] = test_business
    elif is_phone_mobile(test_business):
        data['mobile'] = test_business
        data['business'] = test_mobile
    else:
        data['mobile'] = test_mobile
        data['business'] = test_business

    return data


def is_phone_mobile(number):
    """Return True or False according to tests."""
    test = ['+336', '+337', '06', '07', '00336', '00337']
    for start in test:
        if number.startswith(start):
            return True
    return False


def format_phone_number(number):
    """Always add a +33 in front of the number."""
    formated = None
    if number.startswith('+'):
        formated = number
    elif number.startswith('00'):
        formated = '+{0}'.format(number[2:])
    elif number.startswith('0'):
        if len(number) == 10:
            formated = '+33{0}'.format(number[1:])

    if not formated:
        logger.warning('Weird number {0} '.format(number) +
                       'not formatting.')
        return number
    else:
        logger.debug('Formatted {0} to {1}'.format(number, formated))
        return formated
