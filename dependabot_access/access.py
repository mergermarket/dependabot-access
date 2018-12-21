import argparse
import json
import logging
import os
import requests

from collections import namedtuple
from .dependabot import Dependabot

logger = logging.getLogger()


class App():

    def __init__(
        self, org_name, github_token, app_id, account_id, on_error, dependabot
    ):
        self.org_name = org_name
        self.github_token = github_token
        self.app_id = app_id
        self.account_id = account_id
        self.on_error = on_error

        self.headers = {
            'Authorization': f"token {self.github_token}",
            'Accept': "application/vnd.github.machine-man-preview+json",
            'Cache-Control': "no-cache"
        }

        self.github_request_session = requests.Session()
        self.github_request_session.headers.update(self.headers)

        self.dependabot = dependabot

    def configure(self, config_list):
        for config in config_list:
            if config.get('apps', {}).get('dependabot', False):
                for repo_name in config.get('repos', []):
                    self.enforce_app_access(repo_name)

    def get_repo_contents(self, repo_name):
        no_repo_contents_status_code = 404
        response = self.github_request_session.request(
            'GET',
            f'https://api.github.com/repos/{self.org_name}/'
            f'{repo_name}/contents'
        )
        if response.status_code == no_repo_contents_status_code:
            logger.info(f'Repo {repo_name} has no content')
            return []
        return response.json()

    def enforce_app_access(self, repo_name):
        repo = self.get_github_repo(repo_name)
        if repo.archived or not repo.admin:
            return
        self.install_app_on_repo(self.app_id, repo)
        repo_files = self.get_repo_contents(repo_name)

        self.dependabot.add_configs_to_dependabot(repo, repo_files)

    def get_github_repo(self, repo_name):
        logger.info(f'Getting repo: {repo_name}')
        response = self.github_request_session.request(
            'GET',
            f'https://api.github.com/repos/{self.org_name}/'
            f'{repo_name}'
        )
        repo_content = response.json()
        repo = namedtuple('Repository', 'id, name, archived, admin')(
            repo_content.get('id'),
            repo_content.get('name'),
            repo_content.get('archived'),
            repo_content.get('permissions').get('admin')
        )
        return repo

    def install_app_on_repo(self, app_id, repo):
        url = (
            f'https://api.github.com/user/installations/{app_id}/'
            f'repositories/{repo.id}'
        )
        logger.info(f'Installing app on {repo.name} in Github')
        response = self.github_request_session.request("PUT", url)
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
    dependabot = Dependabot(arguments.account_id, handle_error)
    app = App(
        arguments.org, github_token, arguments.dependabot_id,
        arguments.account_id, handle_error, dependabot
    )

    with open(arguments.access, 'r') as f:
        app.configure(json.loads(f.read()))
