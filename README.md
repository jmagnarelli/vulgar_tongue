Vulgar Tongue
============

This is a Twitter bot that tweets a word of the day from Francis Grose's 1811
Dictionary of the Vulgar Tongue.

I found the book on [Project Gutenberg](http://www.gutenberg.org) and I just
couldn't resist.

------
## Technologies Used
1. Python
2. Sqlite

Basically, the bot runs as a cron job on a machine of your choice. When run, the
bot will check for a word database (a collection of words and definitions, with
already-posted words marked off to avoid duplication). If the database is not
present, it will parse the book's text (included) and create one, then post a
word. If the database is present, it will post an as-yet unused word. No words
will be re-posted until the entire definitions set has been used.

That's about it. It uses a twitter api wrapper to actually post to its own
account, [@daily1811slang](https://twitter.com/daily1811slang).

License: Apache 2.0
