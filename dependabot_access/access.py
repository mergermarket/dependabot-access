import argparse
import json
import os
import requests

from github import Github
from . dependabot import DependabotRepo


class App():

    def __init__(
        self, org_name, main_team_name, github_token, app_id, on_error
    ):
        self.org_name = org_name
        self.main_team_name = main_team_name
        self.github_token = github_token
        self.app_id = app_id
        self.on_error = on_error

    def get_github_team(self, main_team_name):
        github = Github(self.github_token)
        org = github.get_organization(self.org_name)
        teams = {
            team.name: team
            for team in org.get_teams()
        }
        return teams.get(main_team_name)

    def configure(self, access_config):
        main_team = self.get_github_team(self.main_team_name)
        for repo in main_team.get_repos():
            if repo.archived or not repo.permissions.admin:
                continue
            self.handle_repo(repo, access_config.get(repo.name))

    def handle_repo(self, repo, repo_access_config):
        if repo_access_config is None:
            self.on_error(
                f'repository {repo.name} has no config'
            )
            return
        self.enforce_app_access(repo, repo_access_config['apps'])

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
        print(response.status_code)
        if response.status_code != 204:
            self.on_error(
                f'Failed to add repo {repo.name} to Dependabot'
                'app installation'
            )

    def enforce_app_access(self, repo, app_config):
        if app_config.get('dependabot'):
            self.install_app_on_repo(self.app_id, repo)
            dependabot = DependabotRepo(repo, self.on_error)
            dependabot.add_configs_to_dependabot()


def validate_main_team_not_configured(teams, main_team):
    for team in teams:
        if team == main_team:
            raise Exception(
                f'team {team} should not be listed - this is implied'
            )


def validate_access_config(access_config, main_team):
    seen = set()
    for level in access_config:
        validate_main_team_not_configured(level['teams'], main_team)
        for repo in level['repos']:
            if repo in seen:
                raise Exception(f'repo {repo} listed twice')
            seen.add(repo)


def convert_access_config(access_config, main_team):
    validate_access_config(access_config, main_team)
    return {
        repo: {'teams': level['teams'], 'apps': level.get('apps', {})}
        for level in access_config
        for repo in level['repos']
    }


def configure_app(args, handle_error):
    argument_parser = argparse.ArgumentParser('github_access')
    argument_parser.add_argument('--org', required=True)
    argument_parser.add_argument('--team', required=True)
    argument_parser.add_argument('--access', required=True)
    argument_parser.add_argument('--dependabot-id', required=True)
    argument_parser.add_argument('--account-id', required=True)

    arguments = argument_parser.parse_args(args)

    github_token = os.environ['GITHUB_TOKEN']
    app = App(
        arguments.org, arguments.team, github_token,
        arguments.dependabot_id, arguments.account_id, handle_error
    )

    with open(arguments.access, 'r') as f:
        app.configure(
            convert_access_config(
                json.loads(f.read()),
                arguments.team
            )
        )
