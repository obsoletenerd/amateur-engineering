#!/usr/bin/env python3
"""
Aggregates Posts for AmateurEngineering.com Blog

Goals:
    - Take the JSON file and break it out into the types of sources we need to pull
    - If they have a Pelican blog, use the get_pelican(git) function, passing "gitlab" or "github" so we know how to handle it.
    - If they have a Hugo blog, use the get_hugo(git) function, passing as per above.
    - If they have defined an RSS feed, use the get_rss() function, which puts the RSS feed items into their own post files with "Author-Source: RSS" in the metadata for us to style later.
    - For Hugo and Pelican, clone the user repos and copy their post content files into /sources/userdomain.tld/ in their original format
    - Convert each file to suit Pelican's metadata/markdown requrements, and then copy to /content/userdomain.tld/
        - Modify their metadata to suit, converting the metadata formatting and add our specific fields we want such as "Author:" and their name, and "Author-URL:" and their website URL.
        - Convert image paths to absolute paths with the user's domain at the start, this may require tweaking per blog to suit how authors do their image paths.
    - When all the post files are converted to Pelican markdown and in the /content/userdomain.tld/ folders, we can push to git for CI/CD to take over.

Status:
    - Currently (kinda) works for blogs that are already Pelican formatted.
"""


import json
import os
import subprocess
import shutil
import argparse
import urllib.request
from urllib.parse import urlparse
import re
from pathlib import Path


MEMBERS_JSON_URL = "https://raw.githubusercontent.com/obsoletenerd/amateur-engineering/refs/heads/main/ae-scraper/members.json"
OUTPUT_BASE_DIR = "content"
SOURCES_DIR = "sources"


def parse_git_url(posts_url):
    """
    Parse a git repository URL to extract platform, repo name, and path.
    Returns: (platform, repo_name, path)
    """
    if not posts_url:
        return None, None, None

    # Handle GitHub URLs
    if "github.com" in posts_url:
        # Example: https://github.com/username/reponame/tree/main/content
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/[^/]+/(.+)', posts_url)
        if match:
            username, repo_name, path = match.groups()
            return "github", repo_name, f"/{path}"

    # Handle GitLab URLs
    elif "gitlab.com" in posts_url:
        # Example: https://gitlab.com/username/reponame/-/tree/main/content/posts?ref_type=heads
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


def clone_git_repo(repo_url, destination_path):
    """
    Clone a git repository to the specified destination path.
    Returns True if successful, False otherwise.
    """
    try:
        # Remove destination if it already exists
        if os.path.exists(destination_path):
            shutil.rmtree(destination_path)

        # Clone the repository
        subprocess.run(['git', 'clone', repo_url, destination_path],
                      check=True, capture_output=True, text=True)
        print(f"Successfully cloned {repo_url} to {destination_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error cloning repository {repo_url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error cloning repository {repo_url}: {e}")
        return False


def get_git_clone_url(posts_url):
    """
    Convert a posts URL to a git clone URL.
    """
    if "github.com" in posts_url:
        # Extract username and repo from GitHub tree URL
        match = re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/[^/]+/(.+)', posts_url)
        if match:
            username, repo_name, path = match.groups()
            return f"https://github.com/{username}/{repo_name}.git"
    elif "gitlab.com" in posts_url:
        # Extract username and repo from GitLab tree URL
        match = re.match(r'https://gitlab\.com/([^/]+)/([^/]+)/-/tree/[^/]+/(.+?)(?:\?.*)?$', posts_url)
        if match:
            username, repo_name, path = match.groups()
            return f"https://gitlab.com/{username}/{repo_name}.git"
    return None


def copy_markdown_files(source_dir, dest_dir):
    """
    Recursively copy all .md files from source_dir to dest_dir.
    Returns list of copied files.
    """
    copied_files = []

    if not os.path.exists(source_dir):
        print(f"Source directory does not exist: {source_dir}")
        return copied_files

    # Create destination directory if it doesn't exist
    os.makedirs(dest_dir, exist_ok=True)

    # Walk through source directory and copy .md files
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.md'):
                source_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)

                try:
                    shutil.copy2(source_file, dest_file)
                    copied_files.append(dest_file)
                    print(f"Copied: {file}")
                except Exception as e:
                    print(f"Error copying {file}: {e}")

    return copied_files


def process_pelican_metadata(file_path, author_name, author_url, domain):
    """
    Process a Pelican markdown file to ensure proper metadata format.
    Updates Author and Author-URL fields, and converts image paths to absolute URLs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split content into metadata and body
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                metadata_section = parts[1].strip()
                body_section = parts[2].strip()
            else:
                print(f"Warning: Could not parse metadata in {file_path}")
                return
        else:
            print(f"Warning: No metadata found in {file_path}")
            return

        # Parse existing metadata
        metadata_lines = metadata_section.split('\n')
        metadata_dict = {}

        for line in metadata_lines:
            if ':' in line:
                key, value = line.split(':', 1)
                metadata_dict[key.strip()] = value.strip()

        # Update/add our required fields
        metadata_dict['Author'] = author_name
        metadata_dict['Author-URL'] = author_url

        # Convert relative image paths to absolute URLs
        # Look for ![alt](path), <img src="path">, and {static}/path patterns
        img_pattern_md = re.compile(r'!\[([^\]]*)\]\((/[^)]+)\)')
        img_pattern_html = re.compile(r'<img([^>]*)\s+src="(/[^"]+)"')
        static_pattern = re.compile(r'\{static\}(/[^"\s)>]+)')

        def replace_img_md(match):
            alt_text = match.group(1)
            img_path = match.group(2)
            if img_path.startswith('/'):
                absolute_url = f"https://{domain}{img_path}"
                return f"![{alt_text}]({absolute_url})"
            return match.group(0)

        def replace_img_html(match):
            other_attrs = match.group(1)
            img_path = match.group(2)
            if img_path.startswith('/'):
                absolute_url = f"https://{domain}{img_path}"
                return f"<img{other_attrs} src=\"{absolute_url}\""
            return match.group(0)

        def replace_static(match):
            img_path = match.group(1)
            absolute_url = f"https://{domain}{img_path}"
            return absolute_url
        body_section = img_pattern_md.sub(replace_img_md, body_section)
        body_section = img_pattern_html.sub(replace_img_html, body_section)
        body_section = static_pattern.sub(replace_static, body_section)

        # Rebuild the file content
        new_metadata = []
        for key, value in metadata_dict.items():
            new_metadata.append(f"{key}: {value}")

        new_content = f"---\n{chr(10).join(new_metadata)}\n---\n\n{body_section}"

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"Updated metadata in {os.path.basename(file_path)}")

    except Exception as e:
        print(f"Error processing metadata in {file_path}: {e}")


def get_pelican(member, force_refresh=False):
    """
    Process a Pelican blog member by cloning their repo and copying posts.
    """
    print(f"\nProcessing Pelican blog for {member['author']}")

    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Parse the posts URL to get clone info
    posts_url = member.get("posts", "")
    platform, repo_name, posts_path = parse_git_url(posts_url)

    if not all([platform, repo_name, posts_path]):
        print(f"Error: Could not parse git URL for {member['author']}")
        return False

    # Get clone URL
    clone_url = get_git_clone_url(posts_url)
    if not clone_url:
        print(f"Error: Could not determine clone URL for {member['author']}")
        return False

    # Extract domain from member URL
    domain = urlparse(member.get("url", "")).netloc
    if not domain:
        print(f"Error: Could not extract domain from {member.get('url', '')}")
        return False

    # Set up paths
    sources_dir = os.path.join(script_dir, SOURCES_DIR, domain)
    content_dir = os.path.join(script_dir, OUTPUT_BASE_DIR, domain)

    # Check if already processed (skip if content directory already exists)
    if os.path.exists(content_dir) and not force_refresh:
        print(f"Content directory already exists for {member['author']}, skipping...")
        return True

    # Clone the repository
    if not clone_git_repo(clone_url, sources_dir):
        return False

    # Copy markdown files from the posts path to our content directory
    source_posts_dir = os.path.join(sources_dir, posts_path.lstrip('/'))
    copied_files = copy_markdown_files(source_posts_dir, content_dir)

    if not copied_files:
        print(f"No markdown files found to copy for {member['author']}")
        return False

    # Process each copied file to update metadata and image paths
    author_name = member.get("author", "Unknown")
    author_url = member.get("url", "")

    for file_path in copied_files:
        process_pelican_metadata(file_path, author_name, author_url, domain)

    print(f"Successfully processed {len(copied_files)} posts for {member['author']}")
    return True


def load_members_json(use_remote=True):
    """
    Load members.json either from remote URL or local file.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_members_file = os.path.join(script_dir, "members.json")

    if use_remote:
        try:
            print(f"Fetching members.json from: {MEMBERS_JSON_URL}")
            with urllib.request.urlopen(MEMBERS_JSON_URL) as response:
                data = json.loads(response.read().decode())
            print("Successfully loaded remote members.json")
            return data
        except Exception as e:
            print(f"Error fetching remote members.json: {e}")
            print("Falling back to local file...")

    # Fallback to local file
    try:
        print(f"Loading local members.json from: {local_members_file}")
        with open(local_members_file, 'r') as f:
            data = json.load(f)
        print("Successfully loaded local members.json")
        return data
    except FileNotFoundError:
        print(f"Error: Could not find local file {local_members_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Could not parse local JSON file: {e}")
        return None


def main():
    """
    Main function to process the members.json file and handle Pelican blogs.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Aggregate posts from member blogs',
        epilog=f'Remote URL: {MEMBERS_JSON_URL}\nOutput directory: {OUTPUT_BASE_DIR}',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--force', '-f', action='store_true',
                       help='Force refresh even if content already exists')
    parser.add_argument('--pelican-only', action='store_true',
                       help='Process only Pelican blogs')
    parser.add_argument('--local', action='store_true',
                       help='Use local members.json file instead of remote URL')
    args = parser.parse_args()

    # Load members data
    data = load_members_json(use_remote=not args.local)
    if data is None:
        return

    feeds = data.get("feeds", [])
    total_members = len(feeds)

    print(f"{total_members} members in members.json")
    print(f"Output directory: {os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_BASE_DIR)}")

    if args.force:
        print("Force refresh enabled - will re-process existing content")

    # Process each member
    processed_count = 0
    for i, member in enumerate(feeds, 1):
        info = get_member_type_info(member)

        if info["type"] == "rss" and not args.pelican_only:
            print(f'Member {i} is "{info["author"]}" which {info["action_description"]}')
        elif info["type"] == "pelican":
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')
            # Process Pelican blogs
            if get_pelican(member, force_refresh=args.force):
                processed_count += 1
        elif info["type"] == "hugo" and not args.pelican_only:
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')
            print("Hugo processing not yet implemented.")
        elif not args.pelican_only:
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')

    print(f"\nCompleted processing. Successfully processed {processed_count} Pelican blogs.")


if __name__ == "__main__":
    main()
