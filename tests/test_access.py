import json
import os
import unittest
from unittest.mock import Mock, patch, mock_open, ANY

from dependabot_access.access import (
    configure_app, convert_access_config,
    validate_main_team_not_configured, validate_access_config
)


class TestAccess(unittest.TestCase):

    def setUp(self):
        self.account_id = '7890'
        self.dependabot_id = '123456'

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.DependabotRepo.get_repo_contents')
    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.Github')
    def test_access(self, github, install_app_on_repo, get_repo_contents):
        # given
        mock_repo = Mock()
        mock_repo.id = '1'
        mock_repo.name = 'Repo-A'
        mock_repo.archived = False
        mock_repo.permissions.admin = True

        main_team_name = 'test-team'

        mock_team = Mock()
        mock_team.name = main_team_name

        mock_team.get_repos.return_value = [mock_repo]

        mock_org = Mock()
        mock_org.get_teams.return_value = [mock_team]
        github.return_value.get_organization.return_value = mock_org

        mock_content = {
            'name': 'Dockerfile'
        }
        get_repo_contents.return_value = [mock_content]

        # when
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.reason = 'Created'
        with patch(
            'dependabot_access.dependabot.requests.request',
            return_value=mock_response
        ) as dependabot_request:
            args = [
                '--org', 'test-org',
                '--team', 'test-team',
                '--access', f'{os.getcwd()}/tests/fixtures/access.json',
                '--dependabot-id', self.dependabot_id,
                '--account-id', self.account_id
            ]
            configure_app(args, 'test-github-token')

        # then
        data = {
            'repo-id': '1',
            'package-manager': 'docker',
            'update-schedule': 'daily',
            'directory': '/',
            'account-id': self.account_id,
            'account-type': 'org',
        }
        dependabot_request.assert_called_once_with(
            'POST',
            'https://api.dependabot.com/update_configs',
            data=json.dumps(data),
            headers={
                'Authorization': f"Personal abcdef",
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
        )

    @patch('dependabot_access.access.App')
    def test_args(self, patch_app):

        # given
        access = [{'repos': ['test'], 'teams': {}}]
        with patch(
            'dependabot_access.access.open',
            mock_open(read_data=json.dumps(access)),
            create=True
        ) as mocked_open:
            with patch.dict(
                'dependabot_access.access.os.environ',
                {'GITHUB_TOKEN': 'test-github-token'}
            ):
                # when
                configure_app([
                    '--org', 'test-org',
                    '--team', 'test-team',
                    '--access', 'test-file.json',
                    '--dependabot-id', '123456',
                    '--account-id', '7890'
                ], 'test-github-token')

            # then
            patch_app.assert_called_once_with(
                'test-org', 'test-team', 'test-github-token', '123456',
                '7890', ANY
            )
            mocked_open.assert_called_once_with('test-file.json', 'r')
            patch_app.return_value.configure.assert_called_once_with({
                'test': {'teams': {}, 'apps': {}}
            })

    def test_validate_main_team_not_configured(self):
        # given
        teams = ['main-team']
        main_team = 'main-team'

        # when then
        with self.assertRaises(Exception):
            validate_main_team_not_configured(teams, main_team)

    def test_validate_access_config_no_duplicate(self):
        # given
        access_config = [
            {
                'teams': {'team-c': 'pull'},
                'apps': {'dependabot': True},
                'repos': ['repo-d', 'repo-d']
            }
        ]
        main_team = 'main-team'

        # when then
        with self.assertRaises(Exception):
            validate_access_config(access_config, main_team)


class TestFormatConversion(unittest.TestCase):

    def test_array_conversion(self):
        self.assertEqual(
            convert_access_config([
                {
                    'teams': {'team-a': 'pull', 'team-b': 'push'},
                    'repos': ['repo-a', 'repo-b']
                },
                {
                    'teams': {'team-c': 'pull'},
                    'repos': ['repo-c']
                },
                {
                    'teams': {'team-c': 'pull'},
                    'apps': {'dependabot': True},
                    'repos': ['repo-d']
                },
            ], 'test-main-team'),
            {
                'repo-a': {
                    'teams': {'team-a': 'pull', 'team-b': 'push'},
                    'apps': {}
                },
                'repo-b': {
                    'teams': {'team-a': 'pull', 'team-b': 'push'},
                    'apps': {}
                },
                'repo-c': {
                    'teams': {'team-c': 'pull'},
                    'apps': {}
                },
                'repo-d': {
                    'teams': {'team-c': 'pull'},
                    'apps': {'dependabot': True}
                }
            }
        )
