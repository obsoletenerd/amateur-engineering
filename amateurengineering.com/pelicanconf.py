AUTHOR = 'Amateur Engineering'
SITENAME = 'Amateur Engineering'
SITESUBTITLE = '"Perfect is the enemy of done"'
SITEURL = ""

PATH = "content"
STATIC_PATHS = ['images','css']
USE_FOLDER_AS_CATEGORY = True

TIMEZONE = 'Australia/Melbourne'

DEFAULT_LANG = 'en'

THEME = 'themes/ae'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ("Pelican", "https://getpelican.com/"),
    ("Python.org", "https://www.python.org/"),
    ("Jinja2", "https://palletsprojects.com/p/jinja/"),
)

# Social widget
SOCIAL = (
    ("Github", "https://github.com/obsoletenerd/amateur-engineering"),
    ("Mastodon", "#"),
)

DEFAULT_PAGINATION = 25

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True
