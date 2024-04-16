from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
from dotenv import load_dotenv
import os
import yaml
import urllib.parse
import logging


# Load .env vars
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
repo_url = os.getenv("REPO_URL")

# Create the Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


##################
##### ROUTES #####
##################


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/bookmarks")
def bookmarks():
    # TODO: - Pull the list of bookmarks from a YAML file in the AE repo so others can contribute
    return render_template("bookmarks.html")


@app.route("/refresh")
def refresh():
    try:
        response = requests.get(repo_url)
        data = yaml.safe_load(response.text)
        members = data.get("members", [])
    except Exception as e:
        app.logger.error(f"Could not load or parse YAML: {e}")
        return render_template("error.html", error="Failed to load contributors data.")

    posts_data = []
    for member in members:
        for username, details in member.items():
            member_data = {
                "name": details.get("name"),
                "website": details.get("website"),
                "posts": [],
                "post_count": 0,
                "error": None,
                "source": "Unknown",
            }

            posts_url = details.get("posts")
            if "github.com" in posts_url.lower():
                posts = get_github(username, posts_url)
                member_data["source"] = "GitHub"
            elif "gitlab.com" in posts_url.lower():
                posts = get_gitlab(username, posts_url)
                member_data["source"] = "GitLab"
            else:
                posts = get_other(username, posts_url)

            if isinstance(posts, list):
                member_data["posts"] = posts
                member_data["post_count"] = len(posts)
            else:
                member_data["error"] = posts  # Store error message

            posts_data.append(member_data)

    return render_template("refresh.html", posts_data=posts_data)


###################
#### FUNCTIONS ####
###################


def get_github(username, posts_url):
    app.logger.info(f"Getting {username}'s posts from GitHub")
    if "github.com" in posts_url and "/tree/" in posts_url:
        try:
            base_url = "https://api.github.com/repos"
            parts = posts_url.split("/")
            user = parts[3]
            repo = parts[4]
            branch = parts[6]
            path = "/".join(parts[7:])  # Path within the repository
            api_url = f"{base_url}/{user}/{repo}/contents/{path}?ref={branch}"
            app.logger.info(f"Converted WWW URL to API URL: {api_url}")
        except IndexError:
            app.logger.error("URL parsing error.")
            return f"Error parsing GitHub URL: {posts_url}"

        response = requests.get(api_url)
        if response.status_code == 200:
            files = response.json()
            return [
                file["html_url"]
                for file in files
                if file["type"] == "file" and file["name"].endswith(".md")
            ]
        else:
            return f"Failed to retrieve data from GitHub API, status code {response.status_code}"
    else:
        return "Invalid GitHub URL format"


def get_gitlab(username, posts_url):
    app.logger.info(f"Getting {username}'s posts from GitLab")
    api_base, branch, path = parse_gitlab_url(posts_url)

    if not api_base:
        return "Invalid GitLab URL or unable to parse necessary details"

    params = {"ref": branch, "path": path}
    response = requests.get(api_base, params=params)
    if response.status_code == 200:
        items = response.json()
        return [
            f"https://gitlab.com/{urllib.parse.quote_plus('/'.join(api_base.split('/')[4:6]))}/-/blob/{branch}/{item['path']}"
            for item in items
            if item["type"] == "blob" and item["name"].endswith(".md")
        ]
    else:
        return f"Failed to retrieve data from GitLab API with status {response.status_code}"


def get_other(username, posts_url):
    app.logger.info(
        f"Currently, non-GitHub or non-GitLab sources like {posts_url} are not supported for {username}"
    )
    return f"Currently, non-GitHub or non-GitLab sources like {posts_url} are not supported for {username}"


def parse_gitlab_url(posts_url):
    """Parse a GitLab URL to extract the API endpoint components."""
    app.logger.info("[i] Parsing URL: %s", posts_url)
    if "gitlab.com" not in posts_url:
        return None, None, None

    # Normalize and split the URL to parts
    parts = posts_url.replace("-/tree/", "/tree/").split("/")
    try:
        # Extract base parts
        base_index = parts.index("gitlab.com") + 1
        namespace = "/".join(parts[base_index : base_index + 2])
        # URL encode the namespace for API usage
        encoded_namespace = urllib.parse.quote_plus(namespace)
        project_api_base = (
            f"https://gitlab.com/api/v4/projects/{encoded_namespace}/repository/tree"
        )

        # Find the tree index and extract branch and path
        if "tree" in parts:
            tree_index = parts.index("tree") + 1
            branch = parts[tree_index]
            path = "/".join(parts[tree_index + 1 :])
        else:
            branch = "main"
            path = ""

        app.logger.info(
            "[i] Namespace: %s, Encoded Namespace: %s, Branch: %s, Path: %s",
            namespace,
            encoded_namespace,
            branch,
            path,
        )
        app.logger.info(
            "[i] API URL: %s, Branch: %s, Path: %s", project_api_base, branch, path
        )
        return project_api_base, branch, path
    except (ValueError, IndexError):
        return None, None, None


if __name__ == "__main__":
    app.run(debug=True)
