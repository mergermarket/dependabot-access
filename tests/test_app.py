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
        mock_repo.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
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
        mock_repo.admin = False
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
        app.configure(config)

        # then
        app.install_app_on_repo.assert_not_called()

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    @patch('dependabot_access.access.Dependabot')
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
        mock_repo.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
        app.configure(config)

        # then
        app.install_app_on_repo.assert_called_once_with(
            self._app_id, mock_repo
        )

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    @patch('dependabot_access.access.Dependabot')
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
        mock_repo.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
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
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
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
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
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
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
        app.configure(config)

        # then
        app.enforce_app_access.assert_not_called()

    @patch('dependabot_access.access.App.install_app_on_repo')
    @patch('dependabot_access.access.App.get_github_repo')
    def test_enforce_app_access(
        self, get_github_repo, install_app_on_repo
    ):
        #  given
        repo_name = 'mock-repo-name'

        mock_repo = Mock()
        mock_repo.name = repo_name
        mock_repo.archived = False
        mock_repo.admin = True
        get_github_repo.return_value = mock_repo

        # when
        app = App(ANY, ANY, self._app_id, ANY, ANY, Mock())
        app.enforce_app_access(repo_name)

        # then
        app.install_app_on_repo.assert_called_once_with(
            self._app_id, mock_repo
        )

    @patch('dependabot_access.access.requests.Session')
    def test_get_github_repo(self, session):
        # given
        session.return_value.request.return_value.json.return_value = {
            'id': 1,
            'name': 'mock-repo-name',
            'archived': False,
            'permissions': {
                'admin': True
            }
        }

        # when
        app = App(self._org_name, ANY, self._app_id, ANY, ANY, Mock())
        repo = app.get_github_repo('mock-repo-name')

        # then
        assert repo.id == 1
        assert repo.name == 'mock-repo-name'
        assert not repo.archived
        assert repo.admin

    def test_install_app_on_repo(self):
        github_token = 'github-token'
        mock_repo = Mock()
        mock_repo.id = '12345'

        url = (
            f'https://api.github.com/user/installations/{self._app_id}/'
            f'repositories/{mock_repo.id}'
        )
        mock_response = Mock()
        mock_response.status_code = 204

        app = App(ANY, github_token, self._app_id, ANY, Mock(), Mock())
        with patch(
            'dependabot_access.access.requests.Session.request',
            return_value=mock_response
        ) as request:
            app.install_app_on_repo(self._app_id, mock_repo)
            request.assert_called_once_with("PUT", url)

    def test_install_app_on_repo_error(self):
        github_token = 'github-token'
        mock_repo = Mock()
        mock_repo.id = '12345'
        mock_repo.name = 'test-mock-repo'

        mock_response = Mock()
        mock_response.status_code = 500

        mock_error = Mock()

        app = App(ANY, github_token, self._app_id, ANY, mock_error, Mock())
        with patch(
            'dependabot_access.access.requests.Session.request',
            return_value=mock_response
        ):
            app.install_app_on_repo(self._app_id, mock_repo)
            mock_error.assert_called_once_with(
                'Failed to add repo test-mock-repo to Dependabot'
                'app installation'
            )

    @patch('dependabot_access.access.requests.Session.request')
    def test_get_repo_contents(self, request):
        # given
        repo_name = 'repo-name'
        app = App(self._org_name, ANY, self._app_id, ANY, Mock(), Mock())

        # when
        app.get_repo_contents(repo_name)

        # then
        request.assert_called_with(
            'GET',
            f'https://api.github.com/repos/{self._org_name}/{repo_name}'
            '/contents'
        )

    @patch('dependabot_access.dependabot.requests.Session.request')
    def test_get_repo_contents_no_content(self, request):
        # given
        repo_name = 'repo-name'
        app = App(self._org_name, ANY, self._app_id, ANY, Mock(), Mock())

        mock_response = Mock()
        mock_response.status_code = 404
        request.return_value = mock_response

        # when
        result = app.get_repo_contents(repo_name)

        # then
        assert result == []
