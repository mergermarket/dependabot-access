import argparse
import json
import os
import requests

from github import Github
from . dependabot import DependabotRepo


class App():

    def __init__(
        self, org_name, github_token, app_id, account_id, on_error
    ):
        self.org_name = org_name
        self.github_token = github_token
        self.app_id = app_id
        self.account_id = account_id
        self.on_error = on_error

    def configure(self, config_list):
        for config in config_list:
            if config.get('apps', {}).get('dependabot', False):
                for repo_name in config.get('repos', []):
                    self.enforce_app_access(repo_name)

    def enforce_app_access(self, repo_name):
        repo = self.get_github_repo(repo_name)
        if repo.archived or not repo.permissions.admin:
            return
        self.install_app_on_repo(self.app_id, repo)
        dependabot = DependabotRepo(repo, self.account_id, self.on_error)
        dependabot.add_configs_to_dependabot()

    def get_github_repo(self, repo_name):
        github = Github(self.github_token)
        return github.get_repo(f'{self.org_name}/{repo_name}')

    def install_app_on_repo(self, app_id, repo):
        url = (
            f'https://api.github.com/user/installations/{app_id}/'
            f'repositories/{repo.id}'
        )
        headers = {
            'Authorization': f"token {self.github_token}",
            'Accept': "application/vnd.github.machine-man-preview+json",
            'Cache-Control': "no-cache",
        }
        response = requests.request("PUT", url, headers=headers)
        if response.status_code != 204:
            self.on_error(
                f'Failed to add repo {repo.name} to Dependabot'
                'app installation'
            )


def configure_app(args, handle_error):
    argument_parser = argparse.ArgumentParser('dependabot_access')
    argument_parser.add_argument('--org', required=True)
    argument_parser.add_argument('--access', required=True)
    argument_parser.add_argument('--dependabot-id', required=True)
    argument_parser.add_argument('--account-id', required=True)

    arguments = argument_parser.parse_args(args)

    github_token = os.environ['GITHUB_TOKEN']
    app = App(
        arguments.org, github_token, arguments.dependabot_id,
        arguments.account_id, handle_error
    )

    with open(arguments.access, 'r') as f:
        app.configure(json.loads(f.read()))
