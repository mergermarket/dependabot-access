import unittest
from unittest.mock import Mock, patch, ANY

from dependabot_access.access import App


class TestApp(unittest.TestCase):

    def setUp(self):
        self._app_id = '12345678'
        self._org_name = 'fake_org'

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    def test_configure_repo_archived(
        self, get_github_repo, install_app_on_repo
    ):
        #  given
        repo_name = 'mock-archived-repo-name'
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'apps': {
                    'dependabot': True
                },
                'repos': [
                    repo_name
                ]
            }
        ]

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = True
        mock_repo.permissions.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.install_app_on_repo.assert_not_called()

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    def test_configure_repo_non_admin(
        self, get_github_repo, install_app_on_repo
    ):
        #  given
        repo_name = 'mock-non-admin-repo-name'
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'apps': {
                    'dependabot': True
                },
                'repos': [
                    repo_name
                ]
            }
        ]

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.permissions.admin = False
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.install_app_on_repo.assert_not_called()

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_app_configure(
        self, dependabot_repo, get_github_repo, install_app_on_repo
    ):
        #  given
        repo_name = 'mock-repo-name'
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'apps': {
                    'dependabot': True
                },
                'repos': [
                    repo_name
                ]
            }
        ]

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.permissions.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.install_app_on_repo.assert_called_once_with(
            self._app_id, mock_repo
        )

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_app_configure_no_dependabot(
        self, dependabot_repo, get_github_repo, install_app_on_repo
    ):
        #  given
        repo_name = 'mock-repo-name'
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'apps': {
                    'dependabot': False
                },
                'repos': [
                    repo_name
                ]
            }
        ]

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.permissions.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.install_app_on_repo.assert_not_called()

    @patch('dependabot_access.access.App.enforce_app_access')
    def test_app_configure_no_dependabot_object(
        self, enforce_app_access
    ):
        #  given
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'apps': {},
                'repos': [
                    'mock_repo_name'
                ]
            }
        ]

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.enforce_app_access.assert_not_called()

    @patch('dependabot_access.access.App.enforce_app_access')
    def test_app_configure_no_app(
        self, enforce_app_access
    ):
        #  given
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'repos': [
                    'mock_repo_name'
                ]
            }
        ]

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.enforce_app_access.assert_not_called()

    @patch('dependabot_access.access.App.enforce_app_access')
    def test_app_configure_no_repos(
        self, enforce_app_access
    ):
        #  given
        config = [
            {
                'teams': {
                    'team-c': 'pull'
                },
                'apps': {
                    'dependabot': True
                }
            }
        ]

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.configure(config)

        # then
        app.enforce_app_access.assert_not_called()

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    @patch('dependabot_access.access.DependabotRepo')
    def test_enforce_app_access(
        self, dependabot_repo, get_github_repo, install_app_on_repo
    ):
        #  given
        repo_name = 'mock-repo-name'

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.permissions.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY)
        app.enforce_app_access(repo_name)

        # then
        app.install_app_on_repo.assert_called_once_with(
            self._app_id, mock_repo
        )

    @patch('dependabot_access.access.Github')
    def test_get_github_repo(self, github):
        # given
        repo_name = 'mock-repo-name'

        mock_repo = Mock()
        mock_repo.name = repo_name
        github.return_value.get_repo.return_value = mock_repo

        # when
        app = App(self._org_name, ANY, self._app_id, ANY, ANY)
        repo = app.get_github_repo(repo_name)

        # then
        assert repo == mock_repo

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
        app = App(ANY, github_token, self._app_id, ANY, ANY)
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
        app = App(ANY, github_token, self._app_id, ANY, mock_error)
        with patch(
            'dependabot_access.access.requests.request',
            return_value=mock_response
        ):
            app.install_app_on_repo(self._app_id, mock_repo)
            mock_error.assert_called_once_with(
                'Failed to add repo test-mock-repo to Dependabot'
                'app installation'
            )
