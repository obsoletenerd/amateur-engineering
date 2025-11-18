---
Title: "What is Amateur Engineering?"
Author: Amateur Engineering
Author-URL: https://amateurengineering.com
Date: 2025-01-01 13:37
Modified: 2025-01-01 13:37
Summary: Amateur Engineering is the act of building stuff for the sake of building stuff, rather than because you were paid to do it for someone else. Putting as much effort and skill as you can into making a project for no other reason than to see it made. This article explains the goals behind AmateurEngineering.com, and more about what we mean when we refer to Amateur Engineering as a phrase.
Category: AmateurEngineering
Tags: Random
Status: published
---

Amateur Engineering is the act of building stuff for the sake of building stuff, rather than because you were paid to do it for someone else. Putting as much effort and skill as you can into making a project for no other reason than to see it made. Whether it's custom PCBs for a personal project, wood and metal fabrication done in your shed, or software projects coded to scratch that 2am idea-itch. You might consider yourself a maker, a hacker, a tinkerer, an inventor, an artist, or just someone who likes to create stuff for fun.

AmateurEngineering.com is an old-school blog done in a very new-school way. The individual posts are pulled from each member's personal website/blog via their source files in git directly, and the content is then fed into the belly of the beast and compiled into a single community where everyone can see what everyone else is up to.

It's a way to share personal projects with the group while also sharing it with the world, but still maintaining full control over your own content and not having to worry about submitting it to more than one site.

Currently our system supports [Pelican](https://getpelican.com) and [Hugo](https://gohugo.io) blogs hosted in either Github or Gitlab (and RSS sources are in testing for non-git/non-static blogs), but the system is modular so we can add support for any other blog systems members use.

We keep a list of current contributors [in a JSON](https://github.com/obsoletenerd/amateur-engineering/blob/main/contributors.json) file, which lets the script check their personal git repos for new posts, pulls them over into the AmateurEngineering.com repo, does some magic to reformat the posts and merge metadata and insert author credit and so forth, then builds this static site you're reading now.

The ultimate goal is to expand all of this with more source-types, more contributors, and more everything, to create an active community of amateur engineers sharing what they're working on.
