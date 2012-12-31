#!/usr/bin/python2

"""vulgar.py: A very naughty twitter bot"""

__author__="James Magnarelli"
__version__="pre-alpha"


#==============================================================================
# Code written by James Magnarelli (GitHub user jmagnare)
# All rights reserved. Not licensed for use without express permission.
#==============================================================================
# TODO (jmagnare): Docstrings everywhere

from argparse import ArgumentParser
import json
import random
import re
import sqlite3
import twitter


class Text_Utils(object):
    """Class to handle interaction with the textual dictionary"""

    _VULGAR_DICT_PATH = "../data/vulgar.txt"

    @staticmethod
    def get_dictionary_dict(self):
        # Open the dict file for reading ('with' will close when finished)
        with open(Text_Utils._VULGAR_DICT_PATH) as f:
            # Read it into memory
            full_dict = f.read()

        # Parse that baby
        # Pull out a list of (word, definition) pairs

        pair_pat = re.compile('(?P<word>^.*?[A-Z][.,]) (?P<def>(?:.+\\n)+)\\n',
                              re.MULTILINE)
        def_pairs = pair_pat.findall(full_dict)

        # Maps words to definitions
        vulgar_dict = {}

        def __format_raw_def(defin):
            """Strip newlines and extraneous whitespace from raw definitions"""
            temp = defin.replace("  ", " ")
            temp = temp.replace("\n", " ")
            temp = temp.strip()
            return temp

        # Strip out newlines from definitions and store in dict
        for def_pair in def_pairs:
            term = def_pair[0]
            defin = __format_raw_def(def_pair[1])

            vulgar_dict[term] = defin

        return vulgar_dict

class DB_Utils(object):
    """Class to handle retrieving words from the vulgar dictionary"""

    _VULGAR_DB_PATH = "../data/vulgardb"
    _VULGAR_TABLE_NAME = "vulgardict"

    def __init__(self):
        """Initialize a WordGetter, loading the dictionary file"""
        pass

    def _build_new_db(self, conn):
        c = conn.cursor()

        # Create the table
        c.execute("CREATE TABLE ? (term text, used integer, def text)",
             DB_Utils._VULGAR_TABLE_NAME)

        # Get the dictionary into memory
        vulgar_dict = Text_Utils.get_dictionary_dict()

        # Insert all that fancy booklearnin'
        for t, d in vulgar_dict:
            c.execute("INSERT INTO ? (term, used, def) VALUES (?, 0, ?)",
                      DB_Utils._VULGAR_TABLE_NAME, t, d)

        # Save changes
        conn.commit()

    def _handle_used_db(self, conn):
        """Marks all terms in dictionary db as unused"""
        c = conn.cursor()
        c.execute("UPDATE ? SET used=0")

        # Save changes
        conn.commit()

    def _open_vulgar_db(self):

        conn = sqlite3.connect(DB_Utils._VULGAR_DB_NAME)

        # Check whether vulgar db already exists

        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'\
        AND name=?", DB_Utils._VULGAR_TABLE_NAME)
        if not c.fetchall():
            self._build_new_db(conn)

        return conn

    def get_new_word(self):
        """Return an unused (word, definition) from the dict, and note use"""

        # Open our dictionary
        conn = self._open_vulgar_db

        # Handle case where all words have been used
        self._handle_used_db(conn)

        # Build collection of unused words

        c = conn.cursor()
        c.execute("SELECT term, def FROM dict WHERE used = 0")
        unused_terms = c.fetchall()

        # Choose a random word
        chosen_term = random.choice(list(unused_terms))

        # Note its use, and update dictionary file
        c.execute("UPDATE dict SET used=1 WHERE term=?", chosen_term[0])

        # Save changes and close
        conn.commit()
        conn.close()

        return chosen_term


class WordPoster(object):
    """Class to handle posting a retrieved word"""
    # TODO (jmagnare): write this
    pass


def post_word(key, csecret, token, asecret):
    """Post a new vulgar word with the given credentials"""
    poster = WordPoster(key, csecret, token, asecret)
    db = DB_Utils()

    # Get the daily posting (word, def) for today
    post_data = db.get_new_word()
    poster.post(post_data)


def main():
    parser = ArgumentParser()
    parser.add_argument("--consumer_key", default=None, required=True,
                        help="specify consumer key for Vulgar Bot")
    parser.add_argument("--consumer_secret", default=None, required=True,
                        help="specify consumer secret for Vulgar Bot")
    parser.add_argument("--access_token", default=None, required=True,
                        help="specify access token for Vulgar Bot")
    parser.add_argument("--access_secret", default=None, required=True,
                        help="specify access token secret for Vulgar Bot")
    args = parser.parse_args()

    post_word(key=args.consumer_key, csecret=args.consumer_secret,
              token=args.access_token, asecret=args.access_secret)

if __name__ == '__main__':
    main()
