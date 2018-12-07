import json
import unittest
from unittest.mock import Mock, patch, mock_open, ANY

from dependabot_access.access import (
    App, configure_app, convert_access_config,
    validate_main_team_not_configured, validate_access_config
)


class TestAccess(unittest.TestCase):

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


class TestApp(unittest.TestCase):

    def setUp(self):
        self._app_id = '12345678'
        self.org_name = 'fake_org'

    @patch('dependabot_access.access.Github')
    def test_app_get_github_team(self, github):
        # given
        main_team_name = 'test-team'

        mock_team = Mock()
        mock_team.name = main_team_name

        mock_org = Mock()
        mock_org.get_teams.return_value = [mock_team]
        github.return_value.get_organization.return_value = mock_org

        # when
        app = App(ANY, ANY, ANY, self._app_id, ANY)
        team = app.get_github_team(main_team_name)

        # then
        assert team
        assert team.name == main_team_name

    @patch('dependabot_access.access.App.handle_repo')
    @patch('dependabot_access.access.App.get_github_team')
    @patch('dependabot_access.access.DependabotRepo')
    def test_configure_repo_archived(
        self, dependabot_repo, get_github_team, handle_repo
    ):
        repo_name = 'mock-archived-repo-name'
        #  given
        repo_config = {
            'teams': {'team-c': 'pull'},
            'apps': {'dependabot': True}
        }

        access_config = {
            repo_name: repo_config
        }

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = True
        mock_repo.permissions.admin = True
        mock_team = Mock()
        mock_team.get_repos.return_value = [mock_repo]
        get_github_team.return_value = mock_team

        # when
        app = App(ANY, ANY, ANY, self._app_id, ANY)
        app.configure(access_config)

        # then
        app.handle_repo.assert_not_called()

    @patch('dependabot_access.access.App.handle_repo')
    @patch('dependabot_access.access.App.get_github_team')
    @patch('dependabot_access.access.DependabotRepo')
    def test_configure_repo_non_admin(
        self, dependabot_repo, get_github_team, handle_repo
    ):
        repo_name = 'mock-non_admin-repo-name'
        #  given
        repo_config = {
            'teams': {'team-c': 'pull'},
            'apps': {'dependabot': True}
        }

        access_config = {
            repo_name: repo_config
        }

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.permissions.admin = False
        mock_team = Mock()
        mock_team.get_repos.return_value = [mock_repo]
        get_github_team.return_value = mock_team

        # when
        app = App(ANY, ANY, ANY, self._app_id, ANY)
        app.configure(access_config)

        # then
        app.handle_repo.assert_not_called()

    @patch('dependabot_access.access.App.handle_repo')
    @patch('dependabot_access.access.App.get_github_team')
    @patch('dependabot_access.access.DependabotRepo')
    def test_app_configure(
        self, dependabot_repo, get_github_team, handle_repo
    ):
        repo_name = 'mock-repo-name'
        #  given
        repo_config = {
            'teams': {'team-c': 'pull'},
            'apps': {'dependabot': True}
        }

        access_config = {
            repo_name: repo_config
        }

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.permissions.admin = True
        mock_team = Mock()
        mock_team.get_repos.return_value = [mock_repo]
        get_github_team.return_value = mock_team

        # when
        app = App(ANY, ANY, ANY, self._app_id, ANY)
        app.configure(access_config)

        # then
        app.handle_repo.assert_called_once_with(mock_repo, repo_config)

    @patch('dependabot_access.access.App.enforce_app_access')
    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_app_handle_repo(
        self, dependabot_repo, install_app_on_repo, enforce_app_access
    ):
        #  given
        app_config = {
            'dependabot': True
        }
        repo_config = {
            'teams': {'team-c': 'pull'},
            'apps': app_config
        }
        mock_repo = Mock()

        # when
        app = App(ANY, ANY, ANY, self._app_id, ANY)
        app.handle_repo(mock_repo, repo_config)

        # then
        app.enforce_app_access.assert_called_once_with(mock_repo, app_config)

    @patch('dependabot_access.access.App.enforce_app_access')
    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_app_handle_repo_no_config(
        self, dependabot_repo, install_app_on_repo, enforce_app_access
    ):
        #  given
        mock_error = Mock()
        mock_repo = Mock()
        mock_repo.name = 'mock-repo'

        # when
        app = App(ANY, ANY, ANY, self._app_id, mock_error)
        app.handle_repo(mock_repo, None)

        # then
        mock_error.assert_called_once_with(
            'repository mock-repo has no config'
        )
        app.enforce_app_access.assert_not_called()

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_enforce_app_access(
        self, dependabot_repo, install_app_on_repo
    ):
        #  given
        app_config = {
            'dependabot': True
        }
        mock_repo = Mock()

        # when
        app = App(ANY, ANY, ANY, 'app-id', ANY)
        app.enforce_app_access(mock_repo, app_config)

        # then
        app.install_app_on_repo.assert_called_once_with('app-id', mock_repo)

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_enforce_app_access_no_dependabot(
        self, dependabot_repo, install_app_on_repo
    ):
        #  given
        app_config = {
            'dependabot': False
        }
        mock_repo = Mock()

        # when
        app = App(ANY, ANY, ANY, 'app-id', ANY)
        app.enforce_app_access(mock_repo, app_config)

        # then
        app.install_app_on_repo.assert_not_called()

    @patch('dependabot_access.access.requests')
    def test_install_app_on_repo(self, requests):
        github_token = 'github-token'
        mock_repo = Mock()
        mock_repo.id = '12345'
        url = (
            f'https://api.github.com/user/installations/{self._app_id}/'
            f'repositories/{mock_repo.id}'
        )
        headers = {
            'Authorization': f"token {github_token}",
            'Accept': "application/vnd.github.machine-man-preview+json",
            'Cache-Control': "no-cache",
        }
        mock_response = Mock()
        mock_response.status_code = 204
        app = App(ANY, ANY, github_token, self._app_id, ANY)
        with patch(
            'dependabot_access.access.requests.request',
            return_value=mock_response
        ):
            app.install_app_on_repo(self._app_id, mock_repo)
            requests.request.assert_called_once_with(
                "PUT", url, headers=headers
            )

    @patch('dependabot_access.access.requests')
    def test_install_app_on_repo_error(self, requests):
        github_token = 'github-token'
        mock_repo = Mock()
        mock_repo.id = '12345'
        mock_repo.name = 'test-mock-repo'
        mock_response = Mock()
        mock_response.status_code = 500
        mock_error = Mock()
        app = App(ANY, ANY, github_token, self._app_id, mock_error)
        with patch(
            'dependabot_access.access.requests.request',
            return_value=mock_response
        ):
            app.install_app_on_repo(self._app_id, mock_repo)
            mock_error.assert_called_once_with(
                'Failed to add repo test-mock-repo to Dependabot'
                'app installation'
            )

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_dependabot_configured(
        self, dependabot_repo, install_app_on_repo
    ):
        #  given
        app_config = {
            'dependabot': True
        }
        mock_repo = Mock()
        dependabot = Mock()
        dependabot.add_configs_to_dependabot = Mock()
        dependabot_repo.return_value = dependabot

        # when
        app = App(ANY, ANY, ANY, self._app_id, ANY)
        app.enforce_app_access(mock_repo, app_config)

        # then
        dependabot.add_configs_to_dependabot.assert_called()
