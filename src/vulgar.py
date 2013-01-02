#==============================================================================
#   Copyright 2013 James Magnarelli
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#==============================================================================

"""vulgar.py: A very naughty twitter bot"""

__author__ = "James Magnarelli"
__version__ = "1.0"


#==============================================================================
# Code written by James Magnarelli (GitHub user jmagnare)
#==============================================================================

# To the best of my knowledge, this file conforms to the Google Python Style
# Guide (http://google-styleguide.googlecode.com/svn/trunk/pyguide.html)

# TODO (jmagnare): Add logging

from argparse import ArgumentParser
import random
import re
import sqlite3
from twitter import Twitter, OAuth


class Vulgar_Exception(Exception):
    """Base class for exceptions in this project"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class Text_Utils(object):
    """Class to handle interaction with the textual dictionary"""

    _VULGAR_DICT_PATH = "../data/vulgar.txt"
    """The location of the raw dictionary text"""

    @staticmethod
    def get_dictionary_dict():
        """Return a dict containing terms and definitions from the raw text

        @return: A dict of form {"term": "definition",
                                "term": "definition"...} mapping all terms
                                in the raw dictionary text to their
                                definitions"""

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
            """Strip newlines and extraneous whitespace from the given text

            @param defin: The text from which to strip newlines and extra
                            whitespace

            @return: The given text, with the undesired characters removed"""

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
    """The location of the dictionary database, if it exists"""

    def _build_new_db(self, conn):
        """Construct a new dictionary database from raw text file

        Commits changes to disk when done.

        @param conn: An initialized sqlite3 connection to the desired DB
                    file"""

        c = conn.cursor()

        # Create the table
        c.execute("CREATE TABLE vulgar (term text, used integer, def text)")

        # Get the dictionary into memory
        vulgar_dict = Text_Utils.get_dictionary_dict()

        # Insert all that fancy booklearnin'
        c.executemany("INSERT INTO vulgar (term, used, def) VALUES (?, 0, ?)",
                      vulgar_dict.items())

        # Save changes
        conn.commit()

    def _handle_used_db(self, conn):
        """Marks all terms in dictionary db as unused

        This will only be run once the entire dictionary has been posted.

        @param conn: An initialized sqlite3 connection to the database file"""

        c = conn.cursor()
        c.execute("UPDATE vulgar SET used=0")

        # Save changes
        conn.commit()

    def _open_vulgar_db(self):
        """Establish a sqlite3 connection to the database file

        NOTE: Builds the database if it does not exist

        @return: A sqlite3.Connection for the term database file"""

        conn = sqlite3.connect(DB_Utils._VULGAR_DB_PATH)

        # Check whether vulgar db already exists

        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'\
        AND name='vulgar'")
        if not c.fetchall():
            self._build_new_db(conn)
        return conn

    def get_new_word(self):
        """Return an unused (word, definition) from the dict, and note its use

        @return: An unused (word, definition) pairing from the term database"""

        # Open our dictionary
        conn = self._open_vulgar_db()
        c = conn.cursor()

        # Determine number of remaining unused words

        c.execute("SELECT COUNT (*) FROM vulgar WHERE used = 0")
        num_unused = c.fetchall()[0]

        # Handle case where all words have been used
        if num_unused == 0:
            self._handle_used_db(conn)

        # Build collection of unused words

        c.execute("SELECT term, def FROM vulgar WHERE used = 0")
        unused_terms = c.fetchall()

        # Choose a random word
        chosen_term = random.choice(list(unused_terms))

        # Note its use, and update dictionary file
        c.execute("UPDATE vulgar SET used=1 WHERE term=?", [chosen_term[0]])

        # Save changes and close
        conn.commit()
        conn.close()

        return chosen_term


class Word_Poster(object):
    """Class to handle posting a retrieved word"""

    _TWITTER_NAME = "1811 Vulgar Words"

    # Let's say we're posting from London
    _MY_LATITUDE = 51.5171
    _MY_LONGITUDE = -0.1062

    def __init__(self, key, csecret, token, asecret):
        """Initialize a Word_Poster, connecting to Twitter via OAuth

        @param key: The OAuth consumer key
        @param csecret: The OAuth consumer secret
        @param token: The OAuth access token
        @param asecret: The OAuth access token secret"""

        # Establish a connection to twitter
        self.conn = Twitter(auth=OAuth(token, asecret, key, csecret))

        # Check to make sure we connected successfully

        settings = self.conn.account.verify_credentials()
        if settings['name'] != Word_Poster._TWITTER_NAME:
            raise Vulgar_Exception("Failed to connect to Twitter")

    def post(self, term_pairing):
        """Post the given (term, definition) pairing to Twitter

        NOTE: Concatenates the two and truncates to 140 characters.

        @param term_pairing: The (term, definition) pairing to post."""

        # Append term and definition
        post_text_full = term_pairing[0] + " " + term_pairing[1]

        # Truncate for twitter
        post_text_trunc = post_text_full[:140]

        # Post the thing
        self.conn.statuses.update(status=post_text_trunc,
                                  lat=Word_Poster._MY_LATITUDE,
                                  long=Word_Poster._MY_LONGITUDE)


def post_word(key, csecret, token, asecret):
    """Post a new vulgar word with the given OAuth information

    @param key: The OAuth consumer key
    @param csecret: The OAuth consumer secret
    @param token: The OAuth access token
    @param asecret: The OAuth access token secret"""

    poster = Word_Poster(key, csecret, token, asecret)
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
