AUTHOR = 'Amateur Engineering'
SITENAME = 'Amateur Engineering'
SITESUBTITLE = '"Perfect is the enemy of done"'
SITEURL = ""

PATH = "content"
STATIC_PATHS = ['../images','../css']
USE_FOLDER_AS_CATEGORY = True

TIMEZONE = 'Australia/Melbourne'

DEFAULT_LANG = 'en'

THEME = 'themes/ae'
DEFAULT_CATEGORY = "Random"

DISPLAY_CATEGORIES_ON_MENU = True
DISPLAY_PAGES_ON_MENU = False

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ("Obsolete Nerd", "https://obsoletenerd.com/"),
    ("Dmoges", "https://dmoges.com/"),
)

# Social widget
SOCIAL = (
    ("Github", "https://github.com/obsoletenerd/amateur-engineering"),
    ("Mastodon", "#"),
)

DEFAULT_PAGINATION = 25

# Uncomment following line if you want document-relative URLs when developing
# RELATIVE_URLS = True
