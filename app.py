from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import OperationalError
import logging
import yaml
import urllib.parse
from urllib.parse import urlparse
import markdown
import re


# Load .env vars
load_dotenv()
members_yaml_url = os.getenv("REPO_URL")

# Create the Flask app
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


##################
##### ROUTES #####
##################


@app.route("/")
def do_index():

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

            if len(posts) == 0:
                return render_template("error.html", error="No posts found in the database.")
            else:
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
            return render_template("error.html", error="Failed to fetch data from the database.")
        finally:
            cursor.close()
            close_connection(conn)
    else:
        return render_template("error.html", error="Database connection could not be established.")


@app.route("/refresh/")
def do_refresh():
    # TODO: This crashes because get_members() is broken.

    conn = create_connection()

    # Get the list of members from the members.yaml file
    members_data = get_members(members_yaml_url)

    if members_data is not None:
        app.logger.info(
            f"Loaded {len(members_data)} members from the members.yaml file.")

        # Wipe the database first, we'll worry about diff'ing files to do edits/updates later.
        # TODO: One day find a better way to do this than nuking the entire DB every time :P
        reset_database(conn)

        # Start processing each member
        for member in members_data:
            app.logger.info(
                f"Processing {member['name']}'s posts from {member['source_url']}")

            # Add the users to the database so we can refer to them by ID from now on.
            # TODO: Only add users if they've actually got posts to add.
            user_id = import_user(
                member["name"], member["website_url"], member["source_url"])

            # Add the posts to the database
            posts_imported = import_posts(user_id, member["markdown_list"])
            if posts_imported is not None:
                app.logger.info(
                    f"Added {posts_imported} posts for {member['name']} to the database.")
            else:
                app.logger.error(
                    f"Failed to add posts for {member['name']} to the database.")

        output = "Refreshed the database with new posts."

        # TODO: For each markdown file the user has, get the contents and insert them into the database - import_post(user_id, markdown_url)
    else:
        app.logger.error("Failed to process the member list.")
        output = "Refresh failed, something went wrong with processing the member data."

    close_connection(conn)

    return render_template("output.html", output=output)


@app.route("/about/")
def do_about():
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
def do_bookmarks():
    try:
        with open("bookmarks.yaml", "r") as file:
            data = yaml.safe_load(file)
            bookmarks = data.get("bookmarks", {})
    except Exception as e:
        app.logger.error(f"Could not load or parse Bookmarks YAML: {e}")
        return render_template("error.html", error="Failed to load Bookmarks data.")

    return render_template("bookmarks.html", bookmarks=bookmarks)


#####################
##### FUNCTIONS #####
#####################


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
        app.logger.error(
            f"An error occurred while connecting to the database: {e}")
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
    conn_opened = False

    if not conn:
        conn_opened = True
        conn = create_connection()
    try:
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
    except OperationalError as e:
        app.logger.error(
            f"An error occurred while resetting the database: {e}")
        return None

    if conn_opened:
        conn_opened = False
        close_connection(conn)


def get_members(members_yaml_url):
    """
    Get the list of members from the members.yaml file in the repo.

    Usage:
    members_data = get_members(members_yaml_url)

    Returns a list of dictionaries with member data.
    """
    
    # TODO: This function is very broken.

    members = None
    members_data = []

    try:
        response = requests.get(members_yaml_url)
        data = yaml.safe_load(response.text)
        members = data.get("members", [])
        for member in members:

            # Check if their source_url is supported
            if check_url_type(member["source_url"]) != "OTHER":

                # Build the member data dictionary
                member_data = {
                    # Data pulled from the YAML file:
                    "name": member["name"],
                    "website_url": member["website_url"],
                    "source_url": member["source_url"],
                    # Default values for other data we'll build:
                    "markdown_list": {},  # This will be a dictionary of filename: markdown_content,
                    "post_count": 0,
                    "error": None,
                    "source_type": "Unknown",
                }
                # Check the source URLs and build the member data appropriately

                # GitHub users
                if check_url_type(member["source_url"]) == "GITHUB":
                    member_data["source_type"] = "GitHub"

                    # Get the users Markdown posts
                    member_data["markdown_list"] = get_github_posts(
                        member["source_url"])

                # # GitLab users
                # elif check_url_type(member["source_url"]) == "GITLAB":
                #     member_data["source_type"] = "GitLab"

                #     # Get the users Markdown posts
                #     member_data["markdown_list"] = get_gitlab_posts(
                #         member["source_url"])

                # Add the post count to the member data
                if member_data["markdown_list"] is not None:
                    member_data["post_count"] = len(
                        member_data["markdown_list"])
                    app.logger.info(
                        f"Added {member_data['post_count']} posts for {member_data['name']}.")

            else:
                app.logger.error(
                    f"Unsupported source URL. {member['name']} submitted {member['source_url']}, ignoring this user.")

            members_data.append(member_data)

    except Exception as e:
        app.logger.error(f"Could not load or parse Members YAML: {e}")
        return render_template("error.html", error="Failed to load Members list.")


def check_url_type(source_url):
    """
    Check the domain for the URL that has been given. Tag it appropriately.

    Usage:
    source_type = check_url_type(source_url)
    """
    # Parse the URL to extract components
    parsed_url = urlparse(source_url)
    domain = parsed_url.netloc.lower()

    # Check the domain for known sources that we currently support
    if "github.com" in domain:
        return "GITHUB"
    # GitLab removed until fixed:
    # elif "gitlab.com" in domain:
    #     return "GITLAB"
    else:
        return "OTHER"


def import_user(name, website_url, source_url):
    """
    Insert a user into the database.
    """
    user_id = None

    # Add the user to the database
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, posts_url, website_url) VALUES (%s, %s, %s) RETURNING id;",
        (name, source_url, website_url),
    )
    conn.commit()
    user_id = cursor.fetchone()[0]

    app.logger.info(f"Added user {name} to the database with ID {user_id}")

    close_connection(conn)

    return user_id


def get_github_posts(github_user_url):
    """
    Get the list of Markdown files from GitHub, including their contents.

    Args:
        github_user_url (str): URL to the GitHub repository folder.

    Returns:
        dict: A dictionary with filenames as keys and their Markdown contents as values.
    """
    markdown_contents = {}

    # Convert the user-given WWW URL into an API URL
    if "/tree/" in github_user_url:
        try:
            base_url = "https://api.github.com/repos"
            parts = github_user_url.split("/")
            user = parts[3]
            repo = parts[4]
            branch = parts[6]
            path = "/".join(parts[7:])  # Path within the repository
            api_url = f"{base_url}/{user}/{repo}/contents/{path}?ref={branch}"

            # Now use the API URL to get the Markdown file list and contents
            response = requests.get(api_url)
            if response.status_code == 200:
                files = response.json()
                for file in files:
                    if file["type"] == "file" and file["name"].endswith(".md"):
                        # GitHub provides a direct link to the raw content
                        download_url = file['download_url']
                        file_response = requests.get(download_url)
                        if file_response.status_code == 200:
                            markdown_contents[file["name"]
                                              ] = file_response.text
            else:
                print(
                    f"Failed to retrieve data from GitHub API, status code {response.status_code}")
        except Exception as e:
            print(f"Could not get list of Markdown files from GitHub: {e}")

    else:
        print(f"Did  not recognize GitHub URL: {github_user_url}")

    return markdown_contents


def get_gitlab_posts(gitlab_user_url):  # TODO: This function is broken yo
    """
    Get the list of Markdown files from GitLab, including their contents.

    Args:
        gitlab_user_url (str): URL to the GitLab repository folder.

    Returns:
        dict: A dictionary with filenames as keys and their Markdown contents as values.
    """

    # Parse the given URL to extract the necessary components
    parsed_url = urlparse(gitlab_user_url)
    path_parts = parsed_url.path.split('/')

    # Extract the namespace and project, and the path to the directory
    # Assuming the path always starts with a user or org and project name
    namespace = '/'.join(path_parts[1:3])
    # Adjust index based on URL structure
    directory_path = '/'.join(path_parts[5:])
    project_id = urllib.parse.quote_plus(namespace)  # URL encode the namespace
    branch = 'master'  # Default branch, adjust as necessary

    # Prepare API request to list files in the directory
    api_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/tree"
    params = {
        'ref': branch,
        'path': directory_path,
        'per_page': 100  # Adjust as needed to cover all files in directory
    }

    response = requests.get(api_url, params=params)
    if response.status_code != 200:
        print(
            f"Failed to retrieve data from GitLab API, status code {response.status_code} for {api_url}")
        return {}  # Return an empty dict if the request fails

    items = response.json()
    markdown_posts = {}

    # Fetch each Markdown file's content
    for item in items:
        if item['type'] == 'blob' and item['name'].endswith('.md'):
            file_name = item['name']
            file_path = item['path']
            raw_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/files/{urllib.parse.quote_plus(file_path)}/raw?ref={branch}"

            # Fetch the raw content of the Markdown file
            file_response = requests.get(raw_url)
            if file_response.status_code == 200:
                markdown_posts[file_name] = file_response.text

    return markdown_posts


def import_posts(user_id, member_posts):
    """
    Goes through the member_data dictionary and imports each post into the database.

    Args:
        member_data (dict): A dictionary of member data built in get_members().

    Returns:
        dict: A dictionary with username as keys and how many posts were imported as values.
    """
    # TODO: Get the title from the first H1 in the markdown, or the filename if no H1
    # TODO: Convert the markdown into HTML using markdown.markdown()

    posts_imported = None

    for post in member_posts:
        print(f"Adding {post} for user ID {user_id} to the database.")
        # # Check the title of the post
        # post_title = post["name"]
        # post_markdown = post["content"]

        # # Insert the post into the database
        # conn = create_connection()
        # cursor = conn.cursor()
        # cursor.execute(
        #     "INSERT INTO posts (user_id, post_title, post_markdown) VALUES (%s, %s, %s);",
        #     (user_id, post_title, post_markdown),
        # )
        # conn.commit()
        # close_connection(conn)

        # app.logger.info(
        #     f"Added post '{post_title}' for user ID {user_id} to the database.")
        # posts_imported += 1

    return posts_imported




if __name__ == '__main__':
 app.run(debug=True)

