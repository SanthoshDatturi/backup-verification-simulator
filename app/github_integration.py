import os

from github import Auth, Github


def file_github_issue(title, body):
    """
    Files a GitHub issue to the repository specified in the .env file.
    """
    token = os.getenv("GITHUB_TOKEN")
    repo_name = os.getenv("GITHUB_REPO")

    if not token or not repo_name or token == "your_github_token_here":
        print(
            "GitHub token or repo not configured correctly in .env. Skipping issue creation."
        )
        return None

    try:
        auth = Auth.Token(token)
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)

        issue = repo.create_issue(
            title=title, body=body, labels=["backup-failure", "automated-alert"]
        )
        print(f"Successfully filed GitHub issue: {issue.html_url}")
        return issue.html_url
    except Exception as e:
        print(f"Failed to file GitHub issue: {e}")
        return None
