import json
import unittest

from dependabot_access.dependabot import Dependabot
from unittest.mock import patch, Mock, ANY


class TestDependabot(unittest.TestCase):

    def setUp(self):
        self._repo_name = 'repo-name'

    @patch('dependabot_access.dependabot.logger')
    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.Dependabot.get_package_managers')
    def test_add_configs_to_dependabot(
            self, get_package_managers, requests, logger
    ):
        # given
        mock_repo = Mock()
        mock_repo.name = self._repo_name
        mock_repo.id = '1234'
        dependabot_repo = Dependabot('4444', Mock())

        get_package_managers.return_value = set(['pip'])

        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.reason = 'Created'
        requests.request.return_value = mock_response

        # when
        dependabot_repo.add_configs_to_dependabot(mock_repo, Mock())

        # then
        requests.request.assert_called_with(
            'POST',
            'https://api.dependabot.com/update_configs',
            data=json.dumps(
                {
                    'repo-id': '1234',
                    'package-manager': 'pip',
                    'update-schedule': 'daily',
                    'directory': '/',
                    'account-id': '4444',
                    'account-type': 'org',
                }
            ),
            headers={
                'Authorization': "Personal abcdef",
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
        )

        logger.info.assert_called_with(
            "Config for repo repo-name. Dependabot Package manager: pip added"
        )

    @patch('dependabot_access.dependabot.logger')
    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.Dependabot.get_package_managers')
    def test_add_configs_to_dependabot_status_code_400(
            self, get_package_managers, requests, logger
    ):
        # given
        mock_repo = Mock()
        mock_repo.name = self._repo_name
        mock_repo.id = '1234'
        dependabot_repo = Dependabot(mock_repo, '4444', Mock())

        get_package_managers.return_value = set(['pip'])

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
                    'package-manager': 'pip',
                    'update-schedule': 'daily',
                    'directory': '/',
                    'account-id': '4444',
                    'account-type': 'org',
                }
            ),
            headers={
                'Authorization': "Personal abcdef",
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
        )

        logger.info.assert_called_with(
            "Config for repo repo-name. "
            "Dependabot Package Manager: pip already exists"
        )

    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    @patch('dependabot_access.dependabot.Dependabot.get_package_managers')
    def test_add_configs_to_dependabot_error(
            self, get_package_managers, requests
    ):
        # given
        mock_repo = Mock()
        mock_repo.name = self._repo_name
        mock_repo.id = '1234'
        mock_on_error = Mock()
        dependabot_repo = Dependabot(mock_repo, '4444', mock_on_error)

        get_package_managers.return_value = set(['pip'])

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
                    'package-manager': 'pip',
                    'update-schedule': 'daily',
                    'directory': '/',
                    'account-id': '4444',
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
            "Failed to add repo repo-name. "
            "Dependabot Package Manager: pip failed. "
            "(Status Code: 500: There's been an error!)"
        )

    @patch('dependabot_access.dependabot.requests')
    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_repo_contents(self, requests):
        # given
        mock_repo = Mock()
        mock_repo.name = self._repo_name
        mock_on_error = Mock()
        dependabot_repo = Dependabot(mock_repo, ANY, mock_on_error)

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
        mock_repo.name = self._repo_name
        mock_on_error = Mock()
        dependabot_repo = Dependabot(mock_repo, ANY, mock_on_error)

        mock_response = Mock()
        mock_response.status_code = 404
        requests.request.return_value = mock_response

        # when
        result = dependabot_repo.get_repo_contents()

        # then
        assert result == []

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_has_false(self):
        # given
        dependabot_repo = Dependabot(ANY, Mock())

        # when then
        self.assertFalse(dependabot_repo.has(None, []))

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_has_true(self):
        # given
        mock_content = {
            'name': 'Dockerfile'
        }

        dependabot_repo = Dependabot(ANY, Mock())

        # when then
        assert dependabot_repo.has('Dockerfile', [mock_content])

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_package_managers(self):
        # given
        mock_content = {
            'name': 'Dockerfile'
        }

        dependabot = Dependabot(ANY, ANY)

        # when
        package_managers = dependabot.get_package_managers([mock_content])

        # then
        assert package_managers == set(['docker'])

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_gradle_package_manager(self):
        # given
        mock_content = {
            'name': 'build.gradle'
        }

        dependabot = Dependabot(ANY, ANY)

        # when
        package_managers = dependabot.get_package_managers([mock_content])

        # then
        assert package_managers == set(['gradle'])

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_maven_package_manager(self):
        # given
        mock_content = {
            'name': 'pom.xml'
        }

        dependabot = Dependabot(ANY, ANY)

        # when
        package_managers = dependabot.get_package_managers([mock_content])

        # then
        assert package_managers == set(['maven'])

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_no_files_in_repo(self):
        # given
        dependabot = Dependabot(ANY, ANY)

        # when
        package_managers = dependabot.get_package_managers([])

        # then
        assert package_managers == set([])

    @patch.dict('os.environ', {'GITHUB_TOKEN': 'abcdef'})
    def test_get_multiple_package_managers(self):
        # given
        mock_dockerfile = {
            'name': 'Dockerfile'
        }
        mock_pipfile = {
            'name': 'Pipfile'
        }

        dependabot = Dependabot(ANY, ANY)

        # when
        package_managers = dependabot.get_package_managers(
            [mock_dockerfile, mock_pipfile]
        )

        # then
        assert package_managers == set(['docker', 'pip'])
