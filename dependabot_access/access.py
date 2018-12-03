import argparse
import os
import json
import logging
import requests

from . dependabot import DependabotRepo

class App():

    def configure():
        pass


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
    print(arguments)
    app = App(
        arguments.org, arguments.team, github_token,
        arguments.dependabot_id, arguments.account_id, handle_error
    )

    with open(arguments.access, 'r') as f:
        app.run(
            convert_access_config(
                json.loads(f.read()),
                arguments.team
            )
        )
