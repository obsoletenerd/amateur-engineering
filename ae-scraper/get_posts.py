#!/usr/bin/env python3
"""
Aggregates Posts for AmateurEngineering.com Blog

Goals:
    - Take the JSON file and break it out into the types of sources we need to pull
    - RSS feeds are turned into mini posts with some custom metadata so we can format it appropriately
    - Clone user repos and copy their content files into /sources/userdomain.tld/ in their original format
    - Convert each file to suit our Pelican blog and copy to /content/userdomain.tld/
        - Modify their metadata to suit, add our specific fields we want
        - Convert image paths to absolute paths with the user's domain at the start
    - Pushes to the Amateur Engineering repo for Cloudflare worker to build
"""


import json
import os
from urllib.parse import urlparse
import re


def parse_git_url(posts_url):
    """
    Parse a git repository URL to extract platform, repo name, and path.
    Returns: (platform, repo_name, path)
    """
    if not posts_url:
        return None, None, None

    # Handle GitHub URLs
    if "github.com" in posts_url:
        # Example: https://github.com/obsoletenerd/obsoletenerd.com/tree/main/content
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/[^/]+/(.+)', posts_url)
        if match:
            username, repo_name, path = match.groups()
            return "github", repo_name, f"/{path}"

    # Handle GitLab URLs
    elif "gitlab.com" in posts_url:
        # Example: https://gitlab.com/robertlayton/dmoges/-/tree/main/content/posts?ref_type=heads
        match = re.match(r'https://gitlab\.com/([^/]+)/([^/]+)/-/tree/[^/]+/(.+?)(?:\?.*)?$', posts_url)
        if match:
            username, repo_name, path = match.groups()
            return "gitlab", repo_name, f"/{path}"

    return None, None, None


def get_member_type_info(member):
    """
    Analyze a member entry and return information about what actions would be taken.
    """
    member_type = member.get("type", "unknown")
    name = member.get("name", "Unknown")
    author = member.get("author", "Unknown")
    url = member.get("url", "")
    posts_url = member.get("posts", "")

    info = {
        "name": name,
        "author": author,
        "url": url,
        "type": member_type,
        "platform": None,
        "repo_name": None,
        "path": None,
        "action_description": ""
    }

    if member_type == "rss":
        info["action_description"] = f'is an RSS feed from the website "{url}". This will be added as a mini-post to the RSS category in our Pelican blog.'

    elif member_type in ["pelican", "hugo"]:
        platform, repo_name, path = parse_git_url(posts_url)
        info["platform"] = platform
        info["repo_name"] = repo_name
        info["path"] = path

        if platform and repo_name and path:
            platform_name = platform.capitalize()
            blog_type = member_type.capitalize()

            if member_type == "pelican":
                format_info = "are already formatted for Pelican"
            else:  # hugo
                format_info = "are formatted for Hugo so the posts need converting before they will work in Pelican"

            info["action_description"] = f'from the blog url "{url}", which is a {blog_type} blog with content hosted on {platform_name}. Posts should be pulled from the {path} directory and {format_info}.'
        else:
            info["action_description"] = f'from the blog url "{url}", which is a {blog_type} blog, but the posts URL could not be parsed properly.'

    else:
        info["action_description"] = f'has an unknown type "{member_type}".'

    return info


def main():
    """
    Main function to process the members.json file and print what actions would be taken.
    """
    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    members_file = os.path.join(script_dir, "members.json")

    try:
        with open(members_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {members_file}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse JSON file: {e}")
        return

    feeds = data.get("feeds", [])
    total_members = len(feeds)

    print(f"{total_members} members in members.json")

    for i, member in enumerate(feeds, 1):
        info = get_member_type_info(member)

        if info["type"] == "rss":
            print(f'Member {i} is "{info["author"]}" which {info["action_description"]}')
        else:
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')


if __name__ == "__main__":
    main()
