import os
import json
import logging
import requests


logger = logging.getLogger()


class Dependabot:
    def __init__(self, account_id, on_error):
        self.account_id = account_id
        self.on_error = on_error

        self.package_managers_files = {
            "Dockerfile": "docker",
            "Gemfile": "bundler",
            "gemspec": "bundler",
            "package.json": "npm_and_yarn",
            "composer.json": "composer",
            "requirements.txt": "pip",
            "setup.py": "pip",
            "Pipfile": "pip",
            "Pipfile.lock": "pip",
            "build.gradle": "gradle",
            "pom.xml": "maven",
            "Cargo.toml": "cargo",
            "mix.exs": "hex",
            "mix.lock": "hex"
        }

        self.headers = {
            'Authorization': f"Personal {os.environ['GITHUB_TOKEN']}",
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }

        self.dependabot_request_session = requests.Session()
        self.dependabot_request_session.headers.update(self.headers)

    def has(self, filename, repo_files):
        file_list = [repo_file.get('name') for repo_file in repo_files]
        return filename in file_list

    def get_package_managers(self, repo_files):
        package_managers = []
        for (
            package_manager_file, package_manager
        ) in self.package_managers_files.items():
            if self.has(package_manager_file, repo_files):
                package_managers.append(package_manager)
        return set(package_managers)

    def add_configs_to_dependabot(self, repo, repo_files):
        for package_manager in self.get_package_managers(repo_files):
            data = {
                'repo-id': repo.id,
                'package-manager': package_manager,
                'update-schedule': 'daily',
                'directory': '/',
                'account-id': self.account_id,
                'account-type': 'org'
            }
            logger.info(
                f'Dependabot: Updating config for repo: {repo.name} '
                f'with Package manager: {package_manager}'
            )
            response = self.dependabot_request_session.request(
                'POST',
                'https://api.dependabot.com/update_configs',
                data=json.dumps(data)
            )
            if response.status_code == 201 and response.reason == 'Created':
                logger.info(
                    f"Config for repo {repo.name}. "
                    f"Dependabot Package manager: {package_manager} added"
                )
            elif (
                response.status_code == 400 and
                "already exists" in response.text
            ):
                logger.info(
                    f"Config for repo {repo.name}. "
                    f"Dependabot Package Manager: {package_manager} "
                    "already exists"
                )
            else:
                self.on_error(
                    f"Failed to add repo {repo.name}. "
                    f"Dependabot Package Manager: {package_manager} failed. "
                    f"(Status Code: {response.status_code}: {response.text})"
                )
