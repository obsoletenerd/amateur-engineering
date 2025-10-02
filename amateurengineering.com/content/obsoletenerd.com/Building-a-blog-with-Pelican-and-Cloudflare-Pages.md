---
Title: Building a personal website using Pelican and Cloudflare
Date: 2025-07-24 11:33
Modified: 2025-07-27 15:26
Summary: How I built this personal website and static blog with automated build-process and effectively-free hosting, using Markdown-formatted text files to write the posts, Pelican/Python to incorporate Jinja templates and build static HTML output, GitHub for version control and source hosting, and Cloudflare pages to serve the static content to the web on my personald domain name. This post will evolve into more of a tutorial/guide later. For now it is a dumping ground for my notes as I build out the site. These are the steps I took to spin up this very website. It took about 2 hours start-to-finish.
Category: Projects
Tags: Software, Projects
Status: Published
Author: ObsoleteNerd
Author-URL: https://obsoletenerd.com
---

This post will evolve into more of a tutorial/guide later. For now it is a dumping ground for my notes as I build out the site. These are the steps I took to spin up this very website. It took about 2 hours start-to-finish.

The site uses Pelican (a Python-based static-site generator) to take a folder of Markdown-formatted text files, compile them into static HTML and CSS, then deploy it to Cloudflare Pages for free hosting. I write the posts in vim or zed, then when I push changes to the Github repo Cloudflare automatically pulls the repo, builds an instance of Pelican on their servers, runs it to compile the static files from my Markdown content and Jinja templates, and then hosts/serves the static HTML on my personal domain.

It breaks down into 3 main steps:

 - [Setting up Pelican locally](#setting-up-pelican) so you can test your posts, develop your theme, iterate on your content, etc.
 - [Creating a Github repo](#creating-a-github-repo) and pushing your content to it.
 - [Configuring Cloudflare Pages](#configuring-cloudflare-pages) to pull the repo, run the build process, and host the outputted content on your domain.

<a id="setting-up-pelican"></a>
## Set up Pelican locally

```bash
uv init obsoletenerd.com
cd obsoletenerd.com
```

Edit `pyproject.toml` and use the following as an example:

```bash
[project]
name = "obsoletenerd-com"
version = "0.1.0"
description = "ObsoleteNerd.com"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "pelican[markdown]>=4.11.0",
]

[project.optional-dependencies]
markdown = [
    "pelican>=4.11.0",
]
```

Save, then run the Pelican setup script in the terminal with `uv run pelican-quickstart`

Answer all the questions and it will create the basic website structure.

Put a quick sample post into `/content/`, using this as an example:

```markdown
---
Title: "Welcome to my new website!"
Date: 2025-01-01 13:37
Date: 2025-01-01 13:37
Summary: This is where the summary for this post goes, which will be used in the template where appropriate, eg on the index page where it shows a summary of each post.
Category: [blog]
Tags: [tag1, tag2]
Status: published
---

This is the content for a test post on my new Pelican-based website.
```

In the terminal do `uv run pelican` to build the site locally with the new test post, then run `uv run pelican -r -l` to spin up a local webserver and have a look at the website to make sure it's all working. It will show up at `http://127.0.0.1:8000`.

If you keep that server running in the terminal, you can then go edit your posts in your IDE and whenever you save, Pelican will detect the changes to the files and re-build it automatically, letting you just refresh the browser and iterate on posts/layouts/etc quickly locally before actually uploading anything. This is a great way to write your posts and dial in formatting, or work on the theme/layout/templates for the site.

In the `.gitignore` file add the following to the bottom:
```
# Pelican output
output/
```

This will stop your locally-compiled website output being pushed up to Github. It's not super important, but as the site will be re-compiled remotely, there's just no use pushing all your test content to Github (and on to Cloudflare). As your site grows, this can save significant time in the process.

Lastly (**and importantly**) before continuing to the next step, type this in the terminal to lock your dependencies into a `requirements.txt` for Cloudflare's build process:

`uv pip compile pyproject.toml -o requirements.txt`

Cloudflare uses basic Python and `pip` and doesn't have `uv`, so we need the `requirements.txt` ready for it to run Pelican on their servers later.

<a id="creating-a-github-repo"></a>
## Set up a Github repository for the website

This assumes you already have a Github account and know the basics of what you're doing.

Go to [https://repo.new/](https://repo.new/) to create a new repository (it's just a shortcut to the normal Github page to create repos). Create the repo, then back in your terminal in the root folder of the Pelican website, do the following:

```bash
git init
git remote add origin https://github.com/<your-gh-username>/<repository-name>
git add .
git commit -m "Initial commit"
git branch -M main
git push -u origin main
```

(This is the standard "get a new project going in Github" stuff)

This has pushed your content to Github, ready for Cloudflare to grab it and build the website.

<a id="configuring-cloudflare-pages"></a>
## Configuring Cloudflare Pages to deploy your website

In your [Cloudflare dashboard](https://dash.cloudflare.com/) left menu:

 - Click on "Compute (Workers)" and then "Workers & Pages".
 - Select the "Pages" tab.
 - Click on "Import an existing Git repository" and follow the instructions to connect to your Github account and the appropriate repository.
 - In the "Build Settings" section choose "Pelican" as the "Frameworks preset".
 - Modify the "Build Command" to be this: `pip install -r requirements.txt && pelican content -s publishconf.py`
 - Select "Environment variables (advanced)" and add `PYTHON_VERSION = 3.13` (or whatever is current when you do this)
 - Continue through the build process.

If all goes well, you should get given a test URL like `https://obsoletenerd-com.pages.dev` to test it all worked.

Next, connect your custom domain to Cloudflare following their instructions ("Custom Domains" in the "Workers & Pages" section)

Voila... you now have the most ridiculously over-engineered static HTML and CSS hosting possible. There's no kill like over-kill.

I do miss the simpler times of websites, but modern tech is fun to learn and has its place. I can now write/edit posts from any device including my phone via the Github web interface, and changes are pushed almost instantly to my site. This is also a great method for doing simple multi-user blogs or websites, as anyone can submit changes via Github and you can approve/merge the changes from anywhere. No more "Can you please email me the updated content via ZIP file so I can FTP it to the server?" etc.