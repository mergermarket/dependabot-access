import os
import json
import logging
import requests


logger = logging.getLogger()


class DependabotRepo:
    def __init__(self, github_repo, account_id, on_error):
        self.repo_name = github_repo.name
        self.repo_id = github_repo.id
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

        self.github_headers = {
            'Authorization': f"token {os.environ['GITHUB_TOKEN']}",
            'Accept': 'application/vnd.github.machine-man-preview+json',
            'Cache-Control': 'no-cache',
        }

        self.dependabot_headers = {
            'Authorization': f"Personal {os.environ['GITHUB_TOKEN']}",
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
        }

        self.repo_files = self.get_repo_contents()

    def get_repo_contents(self):
        no_repo_contents_status_code = 404
        response = requests.request(
            'GET',
            f'https://api.github.com/repos/mergermarket/'
            f'{self.repo_name}/contents',
            headers=self.github_headers)
        if response.status_code == no_repo_contents_status_code:
            logger.info(f'Repo {self.repo_name} has no content')
            return []
        return response.json()

    def has(self, filename):
        file_list = [repo_file.get('name') for repo_file in self.repo_files]
        return filename in file_list

    def get_package_managers(self):
        package_managers = []
        for (
            package_manager_file, package_manager
        ) in self.package_managers_files.items():
            if self.has(package_manager_file):
                package_managers.append(package_manager)
        return set(package_managers)

    def add_configs_to_dependabot(self):
        for package_manager in self.get_package_managers():
            data = {
                'repo-id': self.repo_id,
                'package-manager': package_manager,
                'update-schedule': 'daily',
                'directory': '/',
                'account-id': self.account_id,
                'account-type': 'org',
            }
            logger.info(f'Dependabot: Updating config for {self.repo_name}')
            response = requests.request(
                'POST',
                'https://api.dependabot.com/update_configs',
                data=json.dumps(data),
                headers=self.dependabot_headers
            )
            if response.status_code == 201 and response.reason == 'Created':
                logger.info(
                    f"Config for repo {self.repo_name}. "
                    f"Dependabot Package manager: {package_manager} added"
                )
            elif (
                response.status_code == 400 and
                "already exists" in response.text
            ):
                logger.info(
                    f"Config for repo {self.repo_name}. "
                    f"Dependabot Package Manager: {package_manager} "
                    "already exists"
                )
            else:
                self.on_error(
                    f"Failed to add repo {self.repo_name}. "
                    f"Dependabot Package Manager: {package_manager} failed. "
                    f"(Status Code: {response.status_code}: {response.text})"
                )
