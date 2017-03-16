# freshdesk-to-3cx

A script that link [Freshdesk](http://freshdesk.com/) helpdesk contacts to 3CX IPBX

3CX import is made using PostgreSQL database

## Requirements

You need postgresql-server-dev-X.Y installed on the server
You also need python3-dev.
If using Debian based system :

    ```
    $ apt-get install postgresql-server-dev-9.4 python3-dev
    ```

You also need to create a PostgreSQL Role to be able to write to the specific database.
As the postgres user on the server :

    ```
    $ psql
    $ CREATE ROLE freshdesk_to_3cx NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN PASSWORD 'password' VALID UNTIL 'infinity';
    $ GRANT CONNECT ON DATABASE database_single TO freshdesk_to_3cx;
    $ GRANT USAGE ON SCHEMA public TO freshdesk_to_3cx;
    $ GRANT ALL ON public.phonebook TO freshdesk_to_3cx;
    $ GRANT ALL ON public.sqphonebook TO freshdesk_to_3cx;
    # Create a index on the column where we store freshdesk id
    $ CREATE INDEX pv_an6_idx ON phonebook (pv_an6);
    ```

## Installation

The easiest way to install is inside a virtualenv

1. Create the virtualenv (Python 3!) and activate it:

    ```
    $ git clone https://github.com/alkivi-sas/freshdesk-to-3cx
    $ virtualenv -p python3 ~/venv/freshdesk-to-3cx
    $ source ~/venv/freshdesk-to-3cx/bin/activate
    $ pip install -r requirements.txt
    ```

2. Change the conf file :

    ```
    $ cp .config-example .config
    $ vim .config
    ```

## Usage
1. From a terminal :

   ```
   $ source ~/venv/freshdesk-to-3cx/bin/activate
   $ ./sync-contacts.sh
   ```

2. A restart of the 3CX service is necessary, we are currently looking how to avoid it
