from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import OperationalError
import yaml
import urllib.parse
import logging
from urllib.parse import urlparse
import markdown  # https://www.digitalocean.com/community/tutorials/how-to-use-python-markdown-to-convert-markdown-text-to-html
import re

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

# TODO: Needs a route to load a single post by ID with a URL like /post/title-of-post


@app.route("/")
def index():

    # TODO: Figure out pagination at some point, but for now just show all posts

    conn = create_connection()
    if conn is not None:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT p.id, p.user_id, p.post_title, p.post_markdown, p.post_date,
                       u.username, u.website_url
                FROM posts p
                JOIN users u ON p.user_id = u.id
                ORDER BY p.post_date DESC
            """
            )
            posts = cursor.fetchall()

            formatted_posts = []

            for post in posts:
                processed_markdown = markdown.markdown(post[3])
                formatted_post = {
                    "id": post[0],
                    "title": post[2],
                    "content": processed_markdown,
                    "date": post[4],
                    "author": post[5],
                    "author_url": post[6],
                }
                formatted_posts.append(formatted_post)

                # TODO: Either strip the first H1 from the markdown text, or modify the template to not show the first H1

            return render_template("index.html", posts=formatted_posts)

        except psycopg2.Error as e:
            app.logger.error(f"Database query failed: {e}")
            return render_template(
                "error.html", error="Failed to fetch data from the database."
            )
        finally:
            cursor.close()
            close_connection(conn)
    else:
        return render_template(
            "error.html", error="Database connection could not be established."
        )


@app.route("/about/")
def about():
    try:
        with open("README.md", "r") as file:
            # Load and convert contents of README.md from Markdown to HTML
            markdown_text = file.read()
            contents = markdown.markdown(markdown_text)
    except Exception as e:
        app.logger.error(f"Could not load or parse README.md: {e}")
        return render_template(
            "error.html", error="Failed to load README.md for the /about page."
        )

    # Pass the HTML content to the template
    return render_template("about.html", contents=contents)


@app.route("/bookmarks/")
def bookmarks():
    try:
        with open("bookmarks.yaml", "r") as file:
            data = yaml.safe_load(file)
            bookmarks = data.get("bookmarks", {})
    except Exception as e:
        app.logger.error(f"Could not load or parse Bookmarks YAML: {e}")
        return render_template("error.html", error="Failed to load Bookmarks data.")

    return render_template("bookmarks.html", bookmarks=bookmarks)


@app.route("/refresh/")
def refresh():
    # Load the YAML file from the repo to get the list of post contributors
    try:
        response = requests.get(repo_url)
        data = yaml.safe_load(response.text)
        members = data.get("members", [])
    except Exception as e:
        app.logger.error(f"Could not load or parse Contributors YAML: {e}")
        return render_template("error.html", error="Failed to load Contributors data.")
    if members:

        # Connect to the database so we can store the posts
        conn = create_connection()
        if conn is not None:
            cursor = conn.cursor()

            # Reset the database for now because we don't have DIFFing logic yet and it's just easier
            reset_database(conn)

            try:
                posts_data = []
                for member in members:
                    member_data = {
                        # Data pulled from the YAML file:
                        "name": member["name"],
                        "website": member["website"],
                        "posts_url": member["posts"],
                        # Default values for other data we'll collect:
                        "posts": [],
                        "post_count": 0,
                        "error": None,
                        "source": "Unknown",
                    }

                    if detect_source(member_data["posts_url"]) == "GITHUB":
                        posts = get_github(
                            member_data["name"], member_data["posts_url"]
                        )
                        member_data["source"] = "GitHub"
                    elif detect_source(member_data["posts_url"]) == "GITLAB":
                        posts = get_gitlab(
                            member_data["name"], member_data["posts_url"]
                        )
                        member_data["source"] = "GitLab"
                    else:
                        posts = get_other(member_data["name"], member_data["posts_url"])

                    if isinstance(posts, list):
                        member_data["posts"] = posts
                        member_data["post_count"] = len(posts)
                    else:
                        member_data["error"] = posts  # Store error message

                    posts_data.append(member_data)

                    if member_data["error"] is None:
                        app.logger.info(
                            f"Adding {member_data['name']}'s post to database: {member_data['posts_url']}"
                        )
                    else:
                        app.logger.error(
                            f"Ignoring {member_data['name']}'s post because: {member_data['error']}"
                        )

                # Add the posts to the database
                add_posts_to_database(conn, posts_data)

                return render_template("refresh.html", posts_data=posts_data)

            except psycopg2.Error as e:
                app.logger.error(f"Database query failed: {e}")
                return render_template(
                    "error.html", error="Could not update the database with new posts."
                )
            finally:
                cursor.close()
                close_connection(conn)
        else:
            return render_template(
                "error.html", error="Database connection could not be established."
            )
    else:
        return render_template(
            "error.html", error="Could not parse members from the YAML file."
        )


###################
#### FUNCTIONS ####
###################


def create_connection():
    """
    Create a postgres connection using psycopg2.
    Connection details are pulled from .env file.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_DATABASE"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT", "5432"),
        )
        return conn
    except OperationalError as e:
        print(f"An error occurred while connecting to the database: {e}")
        return None


def close_connection(conn):
    """
    Close the database connection.
    This is only here so functions can have a clean create_connection/close_connection pattern.
    """
    if conn:
        conn.close()


def reset_database(conn):
    """
    Reset the database by dropping all tables and recreating them.
    """
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS posts;")
    cursor.execute("DROP TABLE IF EXISTS users;")
    cursor.execute(
        """
        CREATE TABLE users (
            id serial PRIMARY KEY,
            username varchar (127) NOT NULL,
            posts_url varchar (255) NOT NULL,
            website_url varchar (255) NOT NULL,
            date_added date DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE posts (
            id serial PRIMARY KEY,
            user_id integer NOT NULL,
            post_title varchar (255) NOT NULL,
            post_markdown text NOT NULL,
            post_date date DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()


# TODO: Finish these functions and refactor the other code to suit.


def convert_github_url(github_url):
    return github_url


def convert_gitlab_url(gitlab_url):
    return gitlab_url


def get_github_markdown_contents(github_markdown_url):
    return github_markdown_url


def get_gitlab_markdown_contents(gitlab_markdown_url):
    return gitlab_markdown_url


def add_posts_to_database(conn, posts_data):
    """
    Add posts to the database.
    """
    cursor = conn.cursor()

    # Add the users
    for member_data in posts_data:
        if member_data["error"] is None:
            # Check if the user already exists in the database, if not, insert them
            cursor.execute(
                "SELECT id FROM users WHERE username = %s", (member_data["name"],)
            )
            user_id = cursor.fetchone()
            if user_id is None:
                cursor.execute(
                    "INSERT INTO users (username, posts_url, website_url) VALUES (%s, %s, %s) RETURNING id",
                    (
                        member_data["name"],
                        member_data["posts_url"],
                        member_data["website"],
                    ),
                )
                user_id = cursor.fetchone()[0]
            else:
                user_id = user_id[0]

            # Insert the posts
            print("-------- member_data[posts] --------")
            print(member_data["name"])
            print(user_id)
            print(member_data["posts"])

            for post in member_data["posts"]:
                # Get the markdown contents from the source URL and store it in the database
                # TODO: This breaks because we're trying to get the WWW url and need to convert it to the API one again
                # TODO: ... so need to break out the get_github and get_gitlab functions to have convert_github_url and convert_gitlab_url functions then fix all the associated crap
                markdown_response = requests.get(post)

                if markdown_response.status_code == 200:
                    markdown_text = markdown_response.text

                    # Try and get the title from inside the markdown content, looking for the first main heading
                    markdown_heading = re.search(
                        r"^#\s+(.*)", markdown_text, re.MULTILINE
                    )
                    if markdown_heading:
                        # Return the matching group which is the text after `# `
                        markdown_title = markdown_heading.group(1).strip()
                    else:
                        # Couldn't get a heading from inside the markdown, so use the filename
                        markdown_title = post.split("/")[-1].replace(".md", "")

                    cursor.execute(
                        "INSERT INTO posts (user_id, post_title, post_markdown) VALUES (%s, %s, %s)",
                        (user_id, markdown_title, markdown_text),
                    )
                else:
                    app.logger.error(
                        f"Failed to retrieve markdown content from {post} with status code {markdown_response.status_code}"
                    )
    conn.commit()


def detect_source(posts_url):
    """
    Detect the source platform of the given URL.
    """
    # Parse the URL to extract components
    parsed_url = urlparse(posts_url)
    domain = parsed_url.netloc.lower()

    # Check the domain for known sources that we currently support
    if "github.com" in domain:
        return "GITHUB"
    elif "gitlab.com" in domain:
        return "GITLAB"
    else:
        return "OTHER"


def get_github(username, posts_url):
    """
    Retrieve posts from a GitHub repository.
    """
    app.logger.info(f"Getting {username}'s posts from GitHub")
    if "/tree/" in posts_url:
        try:
            base_url = "https://api.github.com/repos"
            parts = posts_url.split("/")
            user = parts[3]
            repo = parts[4]
            branch = parts[6]
            path = "/".join(parts[7:])  # Path within the repository
            api_url = f"{base_url}/{user}/{repo}/contents/{path}?ref={branch}"
            app.logger.info(f"Converted GitHub WWW URL to API URL: {api_url}")
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
        return f"Invalid GitHub URL format: {posts_url}"


def get_gitlab(username, posts_url):
    """
    Retrieve posts from a GitLab repository.
    """
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
    """
    Handle unsupported sources.
    """
    app.logger.info(
        f"{username} submitted {posts_url} which is not currently supported."
    )
    return f"Currently, non-GitHub or non-GitLab sources like {posts_url} are not supported for {username}"


def parse_gitlab_url(posts_url):
    """
    Parse a GitLab URL to extract the API endpoint components.
    """
    app.logger.info("Parsing GitLab URL: %s", posts_url)
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

        return project_api_base, branch, path
    except (ValueError, IndexError):
        return None, None, None


if __name__ == "__main__":
    app.run(debug=True)
