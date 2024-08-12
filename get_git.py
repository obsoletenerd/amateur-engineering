import git
import subprocess
import os

# Clone the repository
repo_url = 'https://gitlab.com/senwerks/senwerks.gitlab.io.git'
repo_dir = 'repos/'


def get_markdown_files():
    repo = git.Repo.clone_from(repo_url, repo_dir)

    # Set up sparse-checkout
    repo.git.config('core.sparseCheckout', 'true')

    # Write the sparse-checkout file
    sparse_checkout_file = os.path.join(
        repo_dir, '.git', 'info', 'sparse-checkout')
    with open(sparse_checkout_file, 'w') as sc_file:
        sc_file.write('_posts/')

    # Read the new sparse-checkout settings
    repo.git.read_tree('-mu', 'HEAD')

    # Get the markdown files
    markdown_files = []
    for root, dirs, files in os.walk(os.path.join(repo_dir, '_posts')):
        for file in files:
            if file.endswith('.md'):
                markdown_files.append(os.path.join(root, file))
