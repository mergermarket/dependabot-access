# dependabot-access

[![Build Status](https://travis-ci.com/mergermarket/dependabot-access.svg?branch=master)](https://travis-ci.com/mergermarket/dependabot-access)
[![Dependabot Status](https://api.dependabot.com/badges/status?host=github&repo=mergermarket/dependabot-access)](https://dependabot.com)

This container can be used to configure [Dependabot](https://dependabot.com/) for repositories.

Usage:

    export GITHUB_TOKEN=my-team-member-github-token
    docker run -i -w $PWD -v $PWD:$PWD -e GITHUB_TOKEN mergermark/dependabot-access \
        --org my-github-org \
        --access access.json
        --dependabot-id 12345
        --account-id 67890

access.json should be a json file containing the repositories that have
access to - for example:

    [
      {
        "repos": [ "repo1", "repo2" ],
        "apps": {
          "dependabot": true
        }
      }
    ]

Another example in `tests/fixtures/access.json`

Errors will be produced if access.json contains archived repos or repos
that you don't have admin access to.
