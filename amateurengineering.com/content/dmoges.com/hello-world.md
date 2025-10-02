---
Title: Hello World
Date: 2025-07-09
Tags: devblog, hello
Author: dmoges
Author-URL: https://dmoges.com
Category: dmoges
Status: published
Cover: https://dmoges.com/<../../assets/hello-world/BRAIN monogramlogo.svg>
---

Time to create a devblog. Details are in this post.

The stack for this is:
- **Hugo**: Static site generator
- **Custom Theme**: Built directly into the project. Stupidly simple, no external dependencies.
- **AWS S3**: Hosting the static site
- **AWS CloudFront**: CDN for the site
- **Gitlab CI**: For deployment automation
- **git**: Version control
- **MathJax**: For rendering math equations in posts


The code for the site is available on [Gitlab](https://gitlab.com/robertlayton/dmoges#).
Feel free to patch it, fork it, or just read the code.

As its just me, everything is done in the main branch in git.

Typically I'll be using VS code for development, but at the end of the day, its just text files so anything will work.

Here's a VS Code hint: For adding images in markdown, you can copy the image and paste it into the markdown editor you are using to write the post.
Setting the VS Code setting (CTRL + `,`) `markdown.copyFiles.destination` to `assets` will ensure that the image is copied to the `assets` directory in the post.
I have this set so that `**/*` maps to `${documentWorkspaceFolder}/assets/${documentBaseName}/${fileName}` so that images are copied to a subdirectory in `assets` based on the post name.

Here's an example:
![alt text](<../../assets/hello-world/BRAIN monogramlogo.svg>)

## AI Usage with Claude

I'm also uses Claude Code (claude.ai/code) to help with code generation and editing.
The goal there is to learn about AI-assisted development and see how it can improve my workflow.
Using it in a low-stakes project like this is a good way to experiment.

To do that, I created a file called `CLAUDE.md` in the root of the repository.
Claude will use that files to understand the project and provide relevant code suggestions.
For more hints on using Claude, and AI assisted code in general, I strongly recommend reading [Claude Code: Best practices for agentic coding](https://www.anthropic.com/engineering/claude-code-best-practices).
If you aren't getting good results from Claude, ensure you are following the guidance in that article.