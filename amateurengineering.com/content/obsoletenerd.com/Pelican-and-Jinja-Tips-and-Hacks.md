---
Title: Pelican and Jinja Tips and Hacks
Date: 2025-07-27 16:16
Modified: 2025-07-27 16:16
Summary: In this post I go over some of the hacks and customisations I've done to this site's back-end (Pelican), and the Jinja templates used inside it. None of them are anything ground-breaking, but they're things I had to figure out along the way so I figured someone else might learn from them one day (... if searching the web for help still stays a thing post-AIpocalypse).
Category: Projects
Tags: Software, Projects
Status: Draft
Author: ObsoleteNerd
Author-URL: https://obsoletenerd.com
---

In this post I go over some of the hacks and customisations I've done to this site's back-end ([Pelican](https://getpelican.com)), and the Jinja templates used inside it.

None of them are anything ground-breaking, but they're things I had to figure out along the way so I figured someone else might learn from them one day (... if searching the web for help still stays a thing post-AIpocalypse).

### Adding the ability to do calculations against dates in your templates

Jinja templating (which is the template engine used by Pelican and lots of other static-site-generators) doesn't have proper access to Python's `datetime` functions by default, so you need to do some trickery if we want to do calculations in the article/post/page metadata, like how I have added the new.gif icons on posts less than a month old.

When you run the Pelican build-step after adding/editing content, Pelican loads the `pelicanconf.py` file to pull in your settings, so we can inject it there and create a Jinja filter.

In `pelicanconf.py` add the following:

```python
# ... all your other settings are here ...

# Relative-time calculations in posts (eg to add a new.gif next to a post link)
from datetime import datetime, timedelta

def days_since(date):
    return (datetime.now().date() - date.date()).days

JINJA_FILTERS = {
    'days_since': days_since
}
```

Now in `/themes/theme-name/templates/index.html` you can do stuff like this (inside the `for articles in article` loop):

```html
    <h3>
        <a href="{{ SITEURL }}/{{ article.url }}" rel="bookmark" title="Permalink to {{ article.title|striptags }}">{{ article.title }}</a>
        {% if article.date | days_since <= 14 %}<img src="https://obsoletenerd.com/theme/images/new.gif" />{% endif %}
    </h3>
```

That last bit checks if `article.date` (the "Date" field in every post's metadata) is newer than the current date minus 14 days, and if so, adds the `<img>` tag.

### Embedding PICO-8 games in a custom Jinja template

Once you realise that you can invent any random metadata you want for pages/articles, and pass that data to templates, you can do some really fun things. In my case I built a custom template that merges a Pelican page template with the PICO-8 "Export to HTML" template, letting me embed games directly into my site.

Eg each playable game is a "page" added to Pelican ([example on Github](https://github.com/obsoletenerd/obsoletenerd.com/blob/main/content/pages/beltalowda.md)) with these special metadata tags at the top:

```markdown
---
Title: Beltalowda
Date: 2025-01-25
Template: pico8
Status: hidden
Game_js: beltalowda.js
Game_thumb: data:image/png;base64,iVBORw0KGgoAAA[...clipped because it's long]
---
```

`Template: pico8` tells the page to not use the normal `page.html` template like other pages, but instead use `pico8.html` from the `/templates/` folder instead. That template ([Github link]((https://github.com/obsoletenerd/obsoletenerd.com/blob/main/themes/nouveau/templates/pico8.html)) has variables pulling in data from the page metadata, like:

```js
e.src = "/{{ THEME_STATIC_DIR }}/games/{{ page.game_js }}";
```

`page.game_js` in the code above is pulling the `Game_js` field from the page metadata, letting me add the link to that game's static JS exported from PICO-8. I just export the game from PICO-8, add the JS file it creates to my `/themes/theme-name/static/games/` folder in Pelican, and then the page template embeds it from there.

The power of doing it this way is you get the games embedded in your overall page template, and not in the default template spat out by PICO-8. It leads to some cool stuff you can do using shaders to give your games a CRT look, or pulling scores out of the PICO-8 cart savedata and having leaderboards on your site (coming soon), and lots more.

`Game_thumb` is optional and is the screenshot/cover of the game encoded in base64, and it shows up as the background of the game before the user hits play.

`Status: hidden` just means each individual game doesn't show up in the site menu, but I can link to it on the [Games](/pages/games/) page directly.