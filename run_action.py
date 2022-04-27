#!/usr/bin/env python

import os
import sys
import requests
import argparse
import yaml

COMMENT_HEADER = "### :ballot_box_with_check: Definition of Done checker"
EMPTY_CHECKMARK = "- [ ]"


def dod_criteria_to_message(dod_criteria):
    message = COMMENT_HEADER + "\n"
    for criterion in dod_criteria:
        message += EMPTY_CHECKMARK + " " + criterion + "\n"
    return message


def get_bot_comment(comments):
    for comment in comments:
        if comment["user"]["type"] == "Bot" and COMMENT_HEADER in comment["body"]:
            return comment["body"]
    return ""


def has_unsatisfied_dod(bot_comment):
    return EMPTY_CHECKMARK in bot_comment


def main():
    parser = argparse.ArgumentParser(description="Definition of Done checker")
    parser.add_argument(
        "--pull-request-id", type=str, required=True, help="The pull request id"
    )
    args = parser.parse_args()

    github_workspace = os.environ["GITHUB_WORKSPACE"]
    dod_yaml = os.environ["INPUT_DOD_YAML"]
    dod_yaml_path = os.path.join(github_workspace, dod_yaml)

    config = {}
    with open(dod_yaml_path, "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as yaml_exception:
            print("Invalid YAML file")
            print(yaml_exception)
            return 1

    if "dod" not in config:
        print("No DoD section in config")
        return 1

    repo = os.environ.get("GITHUB_REPOSITORY")
    pull_request_id = args.pull_request_id

    github_token = os.environ.get("INPUT_GITHUB_TOKEN")
    github_api_url = os.environ.get("GITHUB_API_URL")
    comments_url = "%s/repos/%s/issues/%s/comments" % (
        github_api_url,
        repo,
        pull_request_id,
    )

    get_result = requests.get(comments_url)
    if get_result.status_code != 200:
        print(
            "Getting pull request comments to GitHub failed with code: "
            + str(get_result.status_code)
        )
        print(get_result.text)

    bot_comment = get_bot_comment(get_result.json())
    if bot_comment:
        if has_unsatisfied_dod(bot_comment):
            print(
                "The Definition of Done for this pull request "
                + "has not been yet been fully marked as satisfied "
                + "by a repository maintainer. "
                + "Please make sure all checkboxes in the relevant pull request "
                + "comment have been checked off."
            )
            return 1
        else:
            print("All DoD criteria are satisfied. 🎉")
            return 0
    else:
        print(
            "The Definition of Done for this pull request "
            + "has not been yet been fully marked as satisfied "
            + "by a repository maintainer. "
            + "Please make sure to check them off "
            + "in the pull request comment that was just posted."
        )
        message = dod_criteria_to_message(config["dod"])
        post_result = requests.post(
            comments_url,
            json={"body": message},
            headers={"Authorization": "token %s" % github_token},
        )
        if post_result.status_code != 201:
            print(
                "Posting comment to GitHub failed with code: "
                + str(post_result.status_code)
            )
            print(post_result.text)
        return 1


if __name__ == "__main__":
    sys.exit(main())
