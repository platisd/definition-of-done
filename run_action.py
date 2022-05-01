#!/usr/bin/env python

import os
import sys
import requests
import argparse
import yaml

COMMENT_HEADER = os.environ["INPUT_COMMENT_HEADER"]
EMPTY_CHECKMARK = "- [ ]"


def dod_criteria_to_message(dod_criteria):
    message = COMMENT_HEADER + "\n"
    for criterion in dod_criteria:
        message += EMPTY_CHECKMARK + " " + criterion + "\n"
    return message


def has_bot_comment(pull_request_description):
    return COMMENT_HEADER in pull_request_description


def has_unsatisfied_dod(pull_request_description, dod_criteria):
    # Extract the bot message from the pull request description
    bot_message_begin = pull_request_description.find(COMMENT_HEADER)
    last_criterion = dod_criteria[-1]
    bot_message_end = pull_request_description.find(last_criterion)
    if bot_message_end == -1:
        print(
            "DoD criteria are missing. "
            + "Please fully remove any remnants of the bot's comment and try again."
        )
        return False
    bot_message = pull_request_description[bot_message_begin:bot_message_end]

    return EMPTY_CHECKMARK in bot_message


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
    authorization_header = {"authorization": "Bearer %s" % github_token}

    issue_url = "%s/repos/%s/issues/%s" % (
        github_api_url,
        repo,
        pull_request_id,
    )
    get_pull_request_description_result = requests.get(
        issue_url, headers=authorization_header
    )
    if get_pull_request_description_result.status_code != 200:
        print(
            "Getting pull request description from GitHub failed with code: "
            + str(get_pull_request_description_result.status_code)
        )
        print(get_pull_request_description_result.text)
        return 1
    pull_request_description = get_pull_request_description_result.json()["body"]
    if not pull_request_description:
        pull_request_description = ""

    if has_bot_comment(pull_request_description):
        if has_unsatisfied_dod(pull_request_description, config["dod"]):
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
        bot_message = dod_criteria_to_message(config["dod"])
        space_between_message_and_description = (
            "\n\n" if pull_request_description else ""
        )
        update_pull_request_description_result = requests.patch(
            issue_url,
            headers=authorization_header,
            json={
                "body": pull_request_description
                + space_between_message_and_description
                + bot_message,
            },
        )
        if update_pull_request_description_result.status_code != 200:
            print(
                "Updating pull request comment body failed with code: "
                + str(update_pull_request_description_result.status_code)
            )
            return 1

        print(
            "The Definition of Done for this pull request "
            + "needs to fully marked as satisfied by a repository maintainer. "
            + "Please make sure a maintainer marks off the checklist "
            + "that was appended to the pull request description."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
