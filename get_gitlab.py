import requests
from flask import Flask, request, jsonify
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)


@app.route('/', methods=['GET'])
def get_markdown_files():
    gitlab_url = "https://gitlab.com/firnsy/firnsy.com/-/tree/master/data/posts"
    if not gitlab_url:
        return jsonify({"error": "URL parameter is missing"}), 400

    project_path, directory_path = parse_gitlab_url(gitlab_url)
    if not project_path or not directory_path:
        return jsonify({"error": "Invalid GitLab URL"}), 400

    # Use your GitLab token here
    headers = {'Private-Token': 'glpat-fZr5LDyF99AexGz2nCK5'}
    project_id = get_project_id(project_path, headers)
    if not project_id:
        return jsonify({"error": "Project not found"}), 404

    files = list_markdown_files(project_id, directory_path, headers)
    markdown_contents = {}

    for file in files:
        file_content = get_file_content(project_id, file, headers)
        markdown_contents[file] = file_content

    return jsonify(markdown_contents)


def parse_gitlab_url(url):
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    if len(path_parts) > 5:
        # This might need adjustment based on URL structure
        project_path = '/'.join(path_parts[1:3])
        directory_path = '/'.join(path_parts[5:])
        return project_path, directory_path
    return None, None


def get_project_id(project_path, headers):
    api_url = f"https://gitlab.com/api/v4/projects/{requests.utils.quote(project_path, safe='')}"
    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        return response.json()['id']
    return None


def list_markdown_files(project_id, directory_path, headers):
    api_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/tree?path={directory_path}"
    response = requests.get(api_url, headers=headers)
    markdown_files = []
    if response.status_code == 200:
        files = response.json()
        markdown_files = [file['path']
                          for file in files if file['name'].endswith('.md')]
    return markdown_files


def get_file_content(project_id, file_path, headers):
    api_url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/files/{requests.utils.quote(file_path, safe='')}/raw"
    response = requests.get(api_url, headers=headers)
    return response.text if response.status_code == 200 else None


if __name__ == '__main__':
    app.run(debug=True)
