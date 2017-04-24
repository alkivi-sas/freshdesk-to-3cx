from helpers import is_phone_mobile, format_phone_number


def test_mobile():
    mobile_ok = ['0612345678', '0712345678',
                 '+33612345678', '+33712345678',
                 '00336123456787', '0033712345678']

    mobile_ko = ['0812345678', '0112345678',
                 '+33812345678', '+33112345678',
                 '00338123456787', '0033112345678']

    for mobile in mobile_ok:
        assert is_phone_mobile(mobile) is True

    for mobile in mobile_ko:
        assert is_phone_mobile(mobile) is False


def test_format():

    to_test = {
        '0112345678': '+33112345678',
        '+33612345678': '+33612345678',
        '0033612345678': '+33612345678',
        '0032612345678': '+32612345678',
    }

    for k, v in to_test.items():
        assert format_phone_number(k) == v
