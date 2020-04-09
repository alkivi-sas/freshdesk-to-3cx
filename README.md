# freshdesk-to-3cx

A script that link [Freshdesk](http://freshdesk.com/) helpdesk contacts to 3CX IPBX

3CX import is made using PostgreSQL database

## Requirements

You need postgresql-server-dev-X.Y installed on the server
You also need python3-dev.
If using Debian based system :

```bash
PSQL_VERION='9.6'
apt-get install postgresql-server-dev-${PSQL_VERION} python3-dev
```

You also need to create a PostgreSQL Role to be able to write to the specific database.
As the postgres user on the server :

```bash
psql
CREATE ROLE freshdesk_to_3cx NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN PASSWORD 'password' VALID UNTIL 'infinity';
GRANT CONNECT ON DATABASE database_single TO freshdesk_to_3cx;
exit

psql database_single
GRANT USAGE ON SCHEMA public TO freshdesk_to_3cx;
GRANT ALL ON public.phonebook TO freshdesk_to_3cx;
GRANT ALL ON public.sqphonebook TO freshdesk_to_3cx;
# Create a index on the column where we store freshdesk id
CREATE INDEX pv_an6_idx ON phonebook (pv_an6);
```

You also need to add an enterprise entry on one contact to enable extra columns in database.

By default, you have
```bash
psql database_single
psql (9.6.17)
Type "help" for help.

database_single=# \d phonebook
                                  Table "public.phonebook"
     Column     |          Type          |                     Modifiers
----------------+------------------------+---------------------------------------------------
 idphonebook    | integer                | not null default nextval('sqphonebook'::regclass)
 firstname      | character varying(255) | default ''::character varying
 lastname       | character varying(255) | default ''::character varying
 phonenumber    | character varying(255) | default ''::character varying
 fkidtenant     | integer                |
 fkiddn         | integer                |
 company        | character varying      |
 tag            | character varying      |
 pv_an3         | character varying      |
 pv_an5         | character varying      |
 pv_an6         | character varying      |
 pv_an1         | character varying      |
 pv_crm_contact | character varying      |
Indexes:
    "idphonebook_pkey" PRIMARY KEY, btree (idphonebook)
    "pv_an6_idx" btree (pv_an6)
Check constraints:
    "phonebook_check" CHECK (fkiddn IS NOT NULL OR fkidtenant IS NOT NULL)
Foreign-key constraints:
    "phonebook_fkiddn_fkey" FOREIGN KEY (fkiddn) REFERENCES dn(iddn) ON DELETE CASCADE
    "phonebook_fkidtenant_fkey" FOREIGN KEY (fkidtenant) REFERENCES tenant(idtenant) ON DELETE CASCADE
```

After contact update you should have
```bash
psql database_single
database_single=# \d phonebook
                                  Table "public.phonebook"
     Column     |          Type          |                     Modifiers
----------------+------------------------+---------------------------------------------------
 idphonebook    | integer                | not null default nextval('sqphonebook'::regclass)
 firstname      | character varying(255) | default ''::character varying
 lastname       | character varying(255) | default ''::character varying
 phonenumber    | character varying(255) | default ''::character varying
 fkidtenant     | integer                |
 fkiddn         | integer                |
 company        | character varying      |
 tag            | character varying      |
 pv_an3         | character varying      |
 pv_an5         | character varying      |
 pv_an6         | character varying      |
 pv_an1         | character varying      |
 pv_crm_contact | character varying      |
 pv_an0         | character varying      |
 pv_an2         | character varying      |
 pv_an4         | character varying      |
 pv_an7         | character varying      |
 pv_an8         | character varying      |
 pv_an9         | character varying      |
Indexes:
    "idphonebook_pkey" PRIMARY KEY, btree (idphonebook)
    "pv_an6_idx" btree (pv_an6)
Check constraints:
    "phonebook_check" CHECK (fkiddn IS NOT NULL OR fkidtenant IS NOT NULL)
Foreign-key constraints:
    "phonebook_fkiddn_fkey" FOREIGN KEY (fkiddn) REFERENCES dn(iddn) ON DELETE CASCADE
    "phonebook_fkidtenant_fkey" FOREIGN KEY (fkidtenant) REFERENCES tenant(idtenant) ON DELETE CASCADE
```


## Installation

The easiest way to install is inside a virtualenv

1. Create the virtualenv (Python 3!) and activate it:

```bash
git clone https://github.com/alkivi-sas/freshdesk-to-3cx
virtualenv -p python3 ~/venv/freshdesk-to-3cx
source ~/venv/freshdesk-to-3cx/bin/activate
pip install -r requirements.txt
```

2. Change the conf file :

```bash
cp .config-example .config
vim .config
```

## Usage
1. From a terminal :

```bash
source ~/venv/freshdesk-to-3cx/bin/activate
./sync-contacts.sh
```

2. A restart of the 3CX service is necessary, we are currently looking how to avoid it
