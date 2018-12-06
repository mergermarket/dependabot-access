import json
import unittest

from dependabot_access.dependabot import DependabotRepo
from unittest.mock import patch, Mock


class TestDependabot(unittest.TestCase):

    @patch('dependabot_access.dependabot.logger')
    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.DependabotRepo.get_package_managers')
    def test_add_configs_to_dependabot(
            self, get_package_managers, requests, logger
    ):
        # given
        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_repo.id = '1234'
        dependabot_repo = DependabotRepo(mock_repo, Mock())

        get_package_managers.return_value = set({'Python': 'pip'})

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.reason = 'Created'
        requests.request.return_value = mock_response

        # when
        dependabot_repo.add_configs_to_dependabot()

        # then
        requests.request.assert_called_with(
            'POST',
            'https://api.dependabot.com/update_configs',
            data=json.dumps(
                {
                    'repo-id': '1234',
                    'package-manager': 'Python',
                    'update-schedule': 'daily',
                    'directory': '/',
                    'account-id': '2012700',
                    'account-type': 'org',
                }
            ),
            headers={
                'Authorization': "Personal abcdef",
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
        )

        logger.info.assert_called_once_with(
            "Config for repo repo-name:Python added to Dependabot"
        )

    @patch('dependabot_access.dependabot.logger')
    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.DependabotRepo.get_package_managers')
    def test_add_configs_to_dependabot_status_code_400(
            self, get_package_managers, requests, logger
    ):
        # given
        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_repo.id = '1234'
        dependabot_repo = DependabotRepo(mock_repo, Mock())

        get_package_managers.return_value = set({'Python': 'pip'})

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = 'bla bla bla already exists'
        requests.request.return_value = mock_response

        # when
        dependabot_repo.add_configs_to_dependabot()

        # then
        requests.request.assert_called_with(
            'POST',
            'https://api.dependabot.com/update_configs',
            data=json.dumps(
                {
                    'repo-id': '1234',
                    'package-manager': 'Python',
                    'update-schedule': 'daily',
                    'directory': '/',
                    'account-id': '2012700',
                    'account-type': 'org',
                }
            ),
            headers={
                'Authorization': "Personal abcdef",
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
        )

        logger.info.assert_called_once_with(
            "Config for repo repo-name:Python already exists in Dependabot"
        )

    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.DependabotRepo.get_package_managers')
    def test_add_configs_to_dependabot_error(
            self, get_package_managers, requests
    ):
        # given
        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_repo.id = '1234'
        mock_on_error = Mock()
        dependabot_repo = DependabotRepo(mock_repo, mock_on_error)

        get_package_managers.return_value = set({'Python': 'pip'})

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'There\'s been an error!'
        requests.request.return_value = mock_response

        # when
        dependabot_repo.add_configs_to_dependabot()

        # then
        requests.request.assert_called_with(
            'POST',
            'https://api.dependabot.com/update_configs',
            data=json.dumps(
                {
                    'repo-id': '1234',
                    'package-manager': 'Python',
                    'update-schedule': 'daily',
                    'directory': '/',
                    'account-id': '2012700',
                    'account-type': 'org',
                }
            ),
            headers={
                'Authorization': "Personal abcdef",
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
        )

        mock_on_error.assert_called_once_with(
            "Failed to add repo repo-name:Python to "
            "Dependabot app installation "
            "(Staus Code: 500:There's been an error!)"
        )

    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_repo_contents(self, requests):
        # given
        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_on_error = Mock()
        dependabot_repo = DependabotRepo(mock_repo, mock_on_error)

        # when
        dependabot_repo.get_repo_contents()

        # then
        requests.request.assert_called_with(
            'GET',
            'https://api.github.com/repos/mergermarket/repo-name/contents',
            headers={
                'Authorization': "token abcdef",
                'Accept': 'application/vnd.github.machine-man-preview+json',
                'Cache-Control': 'no-cache',
            }
        )

    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_repo_contents_no_content(self, requests):
        # given
        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_on_error = Mock()
        dependabot_repo = DependabotRepo(mock_repo, mock_on_error)

        mock_response = Mock()
        mock_response.status_code = 404
        requests.request.return_value = mock_response

        # when
        result = dependabot_repo.get_repo_contents()

        # then
        assert result == []

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.DependabotRepo.get_repo_contents')
    def test_has_false(self, get_repo_contents):
        # given
        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_on_error = Mock()
        dependabot_repo = DependabotRepo(mock_repo, mock_on_error)

        get_repo_contents.return_value = []

        # when then
        self.assertFalse(dependabot_repo.has(None))

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.DependabotRepo.get_repo_contents')
    def test_has_true(self, get_repo_contents):
        # given
        mock_content = {
            'name': 'Dockerfile'
        }
        get_repo_contents.return_value = [mock_content]

        mock_repo = Mock()
        mock_repo.name = 'repo-name'
        mock_on_error = Mock()
        dependabot_repo = DependabotRepo(mock_repo, mock_on_error)

        # when then
        assert dependabot_repo.has('Dockerfile')
