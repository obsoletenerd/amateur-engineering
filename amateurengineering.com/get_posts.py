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
        - Modify their metadata to suit, converting the metadata formatting and add our specific fields we want such as "Author:" and their name, and "AuthorURL:" and their website URL.
        - Convert image paths to absolute paths with the user's domain at the start, this may require tweaking per blog to suit how authors do their image paths.
    - When all the post files are converted to Pelican markdown and in the /content/userdomain.tld/ folders, we can push to git for CI/CD to take over.

Status:
    - Currently (kinda) works for blogs that are already Pelican formatted or use similar formatting.
"""


import json
import os
import subprocess
import shutil
import argparse
import urllib.request
from urllib.parse import urlparse
import re
import xml.etree.ElementTree as ET
import html
from datetime import datetime



MEMBERS_JSON_URL = "https://raw.githubusercontent.com/obsoletenerd/amateur-engineering/refs/heads/main/contributors.json"
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
    Analyze members from contributors.json and return information about what actions would be taken.
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
        info["action_description"] = f'is an RSS feed from the website "{url}". This will be added as a mini-post to the RSS category.'

    elif member_type in ["pelican", "hugo"]:
        platform, repo_name, path = parse_git_url(posts_url)
        info["platform"] = platform
        info["repo_name"] = repo_name
        info["path"] = path
        blog_type = member_type.capitalize()

        if platform and repo_name and path:
            platform_name = platform.capitalize()

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


def cleanup_sources_directory(sources_dir, author_name):
    """
    Clean up the sources directory after processing a user.
    """
    try:
        if os.path.exists(sources_dir):
            shutil.rmtree(sources_dir)
            print(f"Cleaned up sources directory for {author_name}: {sources_dir}")
    except Exception as e:
        print(f"Warning: Could not clean up sources directory {sources_dir}: {e}")


def extract_last_image_url(content, domain=None):
    """
    Extract the last image URL from post content so we can use it as a cover/thumbnail.
    Returns the full URL of the last image found, or placeholder if none found.
    """
    image_urls = []

    # Pattern for markdown images: ![alt](url)
    md_pattern = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
    md_matches = md_pattern.findall(content)
    image_urls.extend(md_matches)

    # There's gotta be a better way to do this...

    # Pattern for HTML img tags: <img ... src="url" ...>
    html_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', re.IGNORECASE)
    html_matches = html_pattern.findall(content)
    image_urls.extend(html_matches)

    # Pattern for Hugo figure shortcodes: {{< figure src="url" ... >}}
    hugo_pattern = re.compile(r'\{\{<\s*figure\s+src=["\']([^"\']+)["\']', re.IGNORECASE)
    hugo_matches = hugo_pattern.findall(content)
    image_urls.extend(hugo_matches)

    # Pattern for Pelican static paths: {static}/path
    static_pattern = re.compile(r'\{static\}(/[^"\s)>]+)')
    static_matches = static_pattern.findall(content)
    if domain:
        # Convert static paths to absolute URLs
        static_urls = [f"https://{domain}{path}" for path in static_matches]
        image_urls.extend(static_urls)
    else:
        image_urls.extend(static_matches)

    # Convert relative URLs to absolute URLs if domain is provided
    if domain:
        absolute_urls = []
        for url in image_urls:
            if url.startswith('/') and not url.startswith('//'):
                # Relative path, make it absolute
                absolute_urls.append(f"https://{domain}{url}")
            elif url.startswith('http://') or url.startswith('https://'):
                # Already absolute
                absolute_urls.append(url)
            else:
                # Relative path without leading slash, make it absolute
                absolute_urls.append(f"https://{domain}/{url}")
        image_urls = absolute_urls

    # Return the last image URL found, or placeholder if none
    if image_urls:
        return image_urls[-1]
    else:
        return "/images/placeholder.jpg"


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
    Updates Author and AuthorURL fields, and converts image paths to absolute URLs.
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

        # Collect existing categories and tags
        existing_categories = []
        existing_tags = []

        # Parse existing categories
        if 'Category' in metadata_dict:
            cat_value = metadata_dict['Category']
            if cat_value:
                existing_categories = [c.strip() for c in cat_value.split(',') if c.strip()]

        # Parse existing tags
        if 'Tags' in metadata_dict:
            tag_value = metadata_dict['Tags']
            if tag_value:
                existing_tags = [t.strip() for t in tag_value.split(',') if t.strip()]

        # Move original categories to tags
        all_tags = existing_tags + existing_categories

        # Update/add our required fields
        metadata_dict['Author'] = author_name
        metadata_dict['AuthorURL'] = author_url
        metadata_dict['Category'] = author_name  # Use author name as category

        # Set combined tags (original tags + original categories)
        if all_tags:
            metadata_dict['Tags'] = ', '.join(all_tags)

        # Extract cover image from post content
        cover_image_url = extract_last_image_url(body_section, domain)
        metadata_dict['Cover'] = cover_image_url

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


def process_hugo_metadata(file_path, author_name, author_url, domain):
    """
    Process a Hugo markdown file and convert it to Pelican format.
    Converts Hugo frontmatter (--- or +++) to Pelican metadata format.
    Updates Author and AuthorURL fields, and converts image paths to absolute URLs.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Determine frontmatter delimiter (--- or +++)
        frontmatter_delim = None
        if content.startswith('---'):
            frontmatter_delim = '---'
        elif content.startswith('+++'):
            frontmatter_delim = '+++'
        else:
            print(f"Warning: No Hugo frontmatter found in {file_path}")
            return False

        # Split content into frontmatter and body
        parts = content.split(frontmatter_delim, 2)
        if len(parts) < 3:
            print(f"Warning: Could not parse Hugo frontmatter in {file_path}")
            return False

        frontmatter_section = parts[1].strip()
        body_section = parts[2].strip()

        # Parse Hugo frontmatter
        hugo_metadata = {}

        if frontmatter_delim == '+++':
            # TOML format - simple key = value parsing
            for line in frontmatter_section.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    hugo_metadata[key] = value
        else:
            # YAML format - key: value parsing
            for line in frontmatter_section.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    hugo_metadata[key] = value

        # Convert Hugo metadata to Pelican format
        pelican_metadata = {}

        # Required fields - must have title and date
        title = hugo_metadata.get('title', '').strip()
        date = hugo_metadata.get('date', '').strip()

        if not title:
            print(f"Warning: No title found in {file_path}, skipping")
            return False
        if not date:
            print(f"Warning: No date found in {file_path}, skipping")
            return False

        pelican_metadata['Title'] = title
        pelican_metadata['Date'] = date

        # Optional fields
        if hugo_metadata.get('summary'):
            pelican_metadata['Summary'] = hugo_metadata['summary']
        elif hugo_metadata.get('description'):
            pelican_metadata['Summary'] = hugo_metadata['description']

        # Handle categories - Hugo might use 'categories' or 'category'
        # We'll add these to tags instead of using them as categories
        categories = []
        if hugo_metadata.get('categories'):
            # Could be a list or comma-separated string
            cat_value = hugo_metadata['categories']
            if '[' in cat_value and ']' in cat_value:
                # Parse array format like ["cat1", "cat2"]
                categories = [c.strip().strip('"').strip("'") for c in cat_value.strip('[]').split(',') if c.strip().strip('"').strip("'")]
            elif ',' in cat_value:
                # Comma-separated values
                categories = [c.strip().strip('"').strip("'") for c in cat_value.split(',') if c.strip().strip('"').strip("'")]
            else:
                categories = [cat_value.strip().strip('"').strip("'")] if cat_value.strip() else []
        elif hugo_metadata.get('category'):
            cat_val = hugo_metadata['category'].strip().strip('"').strip("'")
            if cat_val:
                categories = [cat_val]

        # Handle tags
        tags = []
        if hugo_metadata.get('tags'):
            tag_value = hugo_metadata['tags']
            if '[' in tag_value and ']' in tag_value:
                # Parse array format like ["tag1", "tag2"]
                tags = [t.strip().strip('"').strip("'") for t in tag_value.strip('[]').split(',') if t.strip().strip('"').strip("'")]
            elif ',' in tag_value:
                # Comma-separated values
                tags = [t.strip().strip('"').strip("'") for t in tag_value.split(',') if t.strip().strip('"').strip("'")]
            else:
                tag_val = tag_value.strip().strip('"').strip("'")
                if tag_val:
                    tags = [tag_val]

        # Combine original tags and original categories into tags
        all_tags = tags + categories
        if all_tags:
            pelican_metadata['Tags'] = ', '.join(all_tags)

        # Add our required fields
        pelican_metadata['Author'] = author_name
        pelican_metadata['AuthorURL'] = author_url
        pelican_metadata['Category'] = author_name  # Use author name as category
        pelican_metadata['Status'] = 'published'

        # Extract cover image from post content
        cover_image_url = extract_last_image_url(body_section, domain)
        pelican_metadata['Cover'] = cover_image_url

        # Convert relative image paths to absolute URLs
        # Look for ![alt](path), <img src="path">, and Hugo shortcodes
        img_pattern_md = re.compile(r'!\[([^\]]*)\]\((/[^)]+)\)')
        img_pattern_html = re.compile(r'<img([^>]*)\s+src="(/[^"]+)"')
        hugo_static_pattern = re.compile(r'\{\{<\s*figure\s+src="(/[^"]+)"')

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

        def replace_hugo_figure(match):
            img_path = match.group(1)
            absolute_url = f"https://{domain}{img_path}"
            return f'{{{{< figure src="{absolute_url}"'

        body_section = img_pattern_md.sub(replace_img_md, body_section)
        body_section = img_pattern_html.sub(replace_img_html, body_section)
        body_section = hugo_static_pattern.sub(replace_hugo_figure, body_section)

        # Rebuild the file content in Pelican format
        new_metadata = []
        for key, value in pelican_metadata.items():
            new_metadata.append(f"{key}: {value}")

        new_content = f"---\n{chr(10).join(new_metadata)}\n---\n\n{body_section}"

        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"Converted Hugo metadata to Pelican format in {os.path.basename(file_path)}")
        return True

    except Exception as e:
        print(f"Error processing Hugo metadata in {file_path}: {e}")
        return False


def get_hugo(member, force_refresh=False):
    """
    Process a Hugo blog member by cloning their repo and converting posts to Pelican format.
    """
    print(f"\nProcessing Hugo blog for {member['author']}")

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
    source_posts_dir = os.path.join(sources_dir, posts_path.lstrip('/') if posts_path else '')
    copied_files = copy_markdown_files(source_posts_dir, content_dir)

    if not copied_files:
        print(f"No markdown files found to copy for {member['author']}")
        # Clean up the sources directory even if no files were found
        cleanup_sources_directory(sources_dir, member['author'])
        return False

    # Process each copied file to convert Hugo metadata to Pelican format
    author_name = member.get("author", "Unknown")
    author_url = member.get("url", "")
    successful_conversions = 0

    for file_path in copied_files:
        if process_hugo_metadata(file_path, author_name, author_url, domain):
            successful_conversions += 1
        else:
            # Remove files that couldn't be processed (missing title/date)
            try:
                os.remove(file_path)
                print(f"Removed {os.path.basename(file_path)} - could not process")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")

    if successful_conversions == 0:
        print(f"No Hugo posts could be successfully converted for {member['author']}")
        # Clean up empty content directory
        try:
            if os.path.exists(content_dir):
                shutil.rmtree(content_dir)
        except Exception as e:
            print(f"Warning: Could not clean up empty content directory {content_dir}: {e}")

        cleanup_sources_directory(sources_dir, member['author'])
        return False

    print(f"Successfully converted {successful_conversions}/{len(copied_files)} Hugo posts for {member['author']}")

    # Clean up the sources directory after successful processing
    cleanup_sources_directory(sources_dir, member['author'])

    return True


def parse_rss_date(date_str):
    """
    Parse various RSS date formats and return a standardized format for Pelican.
    Common formats: RFC822, RFC3339, ISO8601
    """
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d %H:%M')

    # Common RSS date formats to try
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',      # RFC822: "Wed, 02 Oct 2024 14:30:00 +0000"
        '%a, %d %b %Y %H:%M:%S %Z',      # RFC822 with timezone name
        '%a, %d %b %Y %H:%M:%S',         # RFC822 without timezone
        '%Y-%m-%dT%H:%M:%S%z',           # ISO8601 with timezone
        '%Y-%m-%dT%H:%M:%SZ',            # ISO8601 UTC
        '%Y-%m-%dT%H:%M:%S',             # ISO8601 without timezone
        '%Y-%m-%d %H:%M:%S',             # Simple format
        '%d %b %Y %H:%M:%S',             # Alternative format
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime('%Y-%m-%d %H:%M')
        except ValueError:
            continue

    # If all parsing fails, use current time
    print(f"Warning: Could not parse date '{date_str}', using current time")
    return datetime.now().strftime('%Y-%m-%d %H:%M')


def sanitize_filename(title):
    """
    Convert a post title into a safe filename for markdown files.
    """
    # Remove HTML tags if any
    title = re.sub(r'<[^>]+>', '', title)
    # Replace problematic characters with nothing or safe alternatives
    title = re.sub(r'[<>:"/\\|?*&]', '', title)
    # Replace spaces and other whitespace with dashes
    title = re.sub(r'\s+', '-', title)
    # Remove multiple dashes
    title = re.sub(r'-+', '-', title)
    # Remove leading/trailing dashes
    title = title.strip('-')
    # Limit length
    title = title[:100]
    # Ensure it's not empty
    if not title:
        title = "untitled-post"

    return title.lower()


def fetch_and_parse_rss(rss_url):
    """
    Fetch and parse an RSS feed, returning a list of entries.
    """
    try:
        print(f"Fetching RSS feed from: {rss_url}")

        # Add headers to avoid being blocked
        req = urllib.request.Request(
            rss_url,
            headers={
                'User-Agent': 'AmateurEngineering.com RSS Aggregator 1.0',
                'Accept': 'application/rss+xml, application/xml, text/xml'
            }
        )

        with urllib.request.urlopen(req) as response:
            rss_content = response.read().decode('utf-8')

        # Parse the XML
        root = ET.fromstring(rss_content)

        # Handle both RSS and Atom feeds
        entries = []

        # Try RSS format first
        items = root.findall('.//item')
        if not items:
            # Try Atom format
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            is_atom = True
        else:
            is_atom = False

        for item in items:
            entry = {}

            if is_atom:
                # Atom format
                title_elem = item.find('.//{http://www.w3.org/2005/Atom}title')
                entry['title'] = title_elem.text if title_elem is not None else 'Untitled'

                link_elem = item.find('.//{http://www.w3.org/2005/Atom}link')
                entry['link'] = link_elem.get('href', '') if link_elem is not None else ''

                content_elem = item.find('.//{http://www.w3.org/2005/Atom}content')
                if content_elem is None:
                    content_elem = item.find('.//{http://www.w3.org/2005/Atom}summary')
                entry['content'] = content_elem.text if content_elem is not None else ''

                date_elem = item.find('.//{http://www.w3.org/2005/Atom}published')
                if date_elem is None:
                    date_elem = item.find('.//{http://www.w3.org/2005/Atom}updated')
                entry['date'] = date_elem.text if date_elem is not None else ''

            else:
                # RSS format
                title_elem = item.find('title')
                if title_elem is not None and title_elem.text:
                    entry['title'] = title_elem.text
                else:
                    # No title found, try to generate one from GUID or description
                    guid_elem = item.find('guid')
                    if guid_elem is not None and guid_elem.text:
                        # Extract a title from the GUID URL if possible
                        guid_text = guid_elem.text
                        if '/' in guid_text:
                            # Try to get the last part of the URL as an ID
                            entry['title'] = f"Post {guid_text.split('/')[-1]}"
                        else:
                            entry['title'] = f"Post {guid_text}"
                    else:
                        # Try to create title from description
                        desc_elem = item.find('description')
                        if desc_elem is not None and desc_elem.text:
                            # Get first 50 chars of description, strip HTML
                            import re
                            desc_text = re.sub(r'<[^>]+>', '', desc_elem.text)
                            desc_text = desc_text.strip()[:50]
                            if desc_text:
                                entry['title'] = desc_text + ('...' if len(desc_text) == 50 else '')
                            else:
                                entry['title'] = 'Untitled Post'
                        else:
                            entry['title'] = 'Untitled Post'

                link_elem = item.find('link')
                entry['link'] = link_elem.text if link_elem is not None else ''

                # Try description first, then content:encoded
                content_elem = item.find('description')
                if content_elem is None:
                    content_elem = item.find('.//{http://purl.org/rss/1.0/modules/content/}encoded')
                entry['content'] = content_elem.text if content_elem is not None else ''

                date_elem = item.find('pubDate')
                if date_elem is None:
                    date_elem = item.find('.//{http://purl.org/dc/elements/1.1/}date')
                entry['date'] = date_elem.text if date_elem is not None else ''

            # Clean up HTML entities and content
            entry['title'] = html.unescape(entry['title']).strip() if entry['title'] else ''
            entry['content'] = html.unescape(entry['content']).strip() if entry['content'] else ''

            # Skip entries without title (but now we should always have some kind of title)
            if entry['title'] and entry['title'].strip():
                entries.append(entry)

        print(f"Successfully parsed {len(entries)} entries from RSS feed")
        return entries

    except Exception as e:
        print(f"Error fetching or parsing RSS feed {rss_url}: {e}")
        return []


def create_rss_markdown_file(entry, output_dir, author_name, author_url):
    """
    Create a Pelican markdown file from an RSS entry.
    """
    try:
        # Generate filename from title
        filename = sanitize_filename(entry['title']) + '.md'
        filepath = os.path.join(output_dir, filename)

        # Avoid duplicate files by adding a number suffix if needed
        counter = 1
        base_filepath = filepath
        while os.path.exists(filepath):
            name, ext = os.path.splitext(base_filepath)
            filepath = f"{name}-{counter}{ext}"
            counter += 1

        # Parse and format the date
        pelican_date = parse_rss_date(entry['date'])

        # Create the content
        content_lines = [
            "---",
            f"Title: {entry['title']}",
            f"Author: {author_name}",
            f"AuthorURL: {author_url}",
            f"Date: {pelican_date}",
            f"Category: {author_name}",
            "Source: RSS",
            "Status: published"
        ]

        # Add original URL if available
        if entry['link']:
            content_lines.append(f"Original-URL: {entry['link']}")

        # Extract cover image from entry content (no domain since RSS content may have absolute URLs)
        cover_image_url = extract_last_image_url(entry['content'] or '', None)
        content_lines.append(f"Cover: {cover_image_url}")

        # Create summary from content (first 200 chars)
        if entry['content']:
            # Strip HTML tags for summary
            summary_text = re.sub(r'<[^>]+>', '', entry['content'])
            summary_text = ' '.join(summary_text.split())  # Clean whitespace
            if len(summary_text) > 200:
                summary_text = summary_text[:200] + "..."
            content_lines.append(f"Summary: {summary_text}")

        content_lines.extend([
            "---",
            "",
            "# " + entry['title'],
            ""
        ])

        # Add the main content
        if entry['content']:
            content_lines.append(entry['content'])
        else:
            content_lines.append("*Content not available in RSS feed.*")

        # Add link to original post
        if entry['link']:
            content_lines.extend([
                "",
                "---",
                f"**[Read the full post on the original site]({entry['link']})**"
            ])

        # Write the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))

        return filepath

    except Exception as e:
        print(f"Error creating markdown file for RSS entry '{entry.get('title', 'unknown')}': {e}")
        return None


def get_rss(member, force_refresh=False):
    """
    Process an RSS feed member by fetching entries and creating Pelican markdown files.
    """
    print(f"\nProcessing RSS feed for {member['author']}")

    # Get the directory of the script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Extract domain from member URL for the output directory
    domain = urlparse(member.get("url", "")).netloc
    if not domain:
        print(f"Error: Could not extract domain from {member.get('url', '')}")
        return False

    # Set up paths
    content_dir = os.path.join(script_dir, OUTPUT_BASE_DIR, domain)

    # Check if already processed (skip if content directory already exists)
    if os.path.exists(content_dir) and not force_refresh:
        print(f"Content directory already exists for {member['author']}, skipping...")
        return True

    # Get the RSS feed URL (check both 'posts' and 'rss' fields)
    rss_url = member.get("posts", "") or member.get("rss", "")
    if not rss_url:
        print(f"Error: No RSS URL provided for {member['author']}")
        return False

    # Fetch and parse RSS feed
    entries = fetch_and_parse_rss(rss_url)
    if not entries:
        print(f"No entries found in RSS feed for {member['author']}")
        return False

    # Create content directory
    os.makedirs(content_dir, exist_ok=True)

    # Process each RSS entry
    author_name = member.get("author", "Unknown")
    author_url = member.get("url", "")
    successful_conversions = 0

    for entry in entries:
        filepath = create_rss_markdown_file(entry, content_dir, author_name, author_url)
        if filepath:
            successful_conversions += 1
            print(f"Created: {os.path.basename(filepath)}")

    if successful_conversions == 0:
        print(f"No RSS entries could be successfully converted for {member['author']}")
        # Clean up empty content directory
        try:
            if os.path.exists(content_dir):
                shutil.rmtree(content_dir)
        except Exception as e:
            print(f"Warning: Could not clean up empty content directory {content_dir}: {e}")
        return False

    print(f"Successfully converted {successful_conversions}/{len(entries)} RSS entries for {member['author']}")
    return True


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
    source_posts_dir = os.path.join(sources_dir, posts_path.lstrip('/') if posts_path else '')
    copied_files = copy_markdown_files(source_posts_dir, content_dir)

    if not copied_files:
        print(f"No markdown files found to copy for {member['author']}")
        # Clean up the sources directory even if no files were found
        cleanup_sources_directory(sources_dir, member['author'])
        return False

    # Process each copied file to update metadata and image paths
    author_name = member.get("author", "Unknown")
    author_url = member.get("url", "")

    for file_path in copied_files:
        process_pelican_metadata(file_path, author_name, author_url, domain)

    print(f"Successfully processed {len(copied_files)} posts for {member['author']}")

    # Clean up the sources directory after successful processing
    cleanup_sources_directory(sources_dir, member['author'])

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
    parser.add_argument('--hugo-only', action='store_true',
                       help='Process only Hugo blogs')
    parser.add_argument('--rss-only', action='store_true',
                       help='Process only RSS feeds')
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

        if info["type"] == "rss" and (args.rss_only or (not args.pelican_only and not args.hugo_only)):
            print(f'Member {i} is "{info["author"]}" which {info["action_description"]}')
            # Process RSS feeds
            if get_rss(member, force_refresh=args.force):
                processed_count += 1
        elif info["type"] == "pelican" and not args.hugo_only and not args.rss_only:
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')
            # Process Pelican blogs
            if get_pelican(member, force_refresh=args.force):
                processed_count += 1
        elif info["type"] == "hugo" and not args.pelican_only and not args.rss_only:
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')
            # Process Hugo blogs
            if get_hugo(member, force_refresh=args.force):
                processed_count += 1
        elif not args.pelican_only and not args.hugo_only and not args.rss_only:
            print(f'Member {i} is "{info["author"]}" {info["action_description"]}')

    if args.hugo_only:
        blog_type = "Hugo"
    elif args.pelican_only:
        blog_type = "Pelican"
    elif args.rss_only:
        blog_type = "RSS"
    else:
        blog_type = "all"
    print(f"\nCompleted processing. Successfully processed {processed_count} {blog_type} sources.")


if __name__ == "__main__":
    main()
