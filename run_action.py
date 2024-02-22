#!/usr/bin/env python

import os
import sys
import requests
import argparse
import yaml
import re

from pathlib import Path

MESSAGE_HEADER = os.environ["INPUT_MESSAGE_HEADER"]
EMPTY_CHECKMARK = "- [ ]"
RIGHT_ARROW_EMOJI = "➡️"


def dod_criteria_to_message(dod_criteria):
    message = MESSAGE_HEADER + "\n"
    for criterion in dod_criteria:
        indentation_depth = criterion.count(RIGHT_ARROW_EMOJI)
        indentation = 2 * " " * indentation_depth
        criterion = criterion.replace(RIGHT_ARROW_EMOJI, "")
        message += indentation + EMPTY_CHECKMARK + " " + criterion + "\n"
    return message


def has_bot_comment(pull_request_description):
    return MESSAGE_HEADER in pull_request_description


def maybe_replace_config(config: dict, pull_request_description: str):
    """
    Replace the default DoD with an alternative one if specified
    in the pull request description with a YAML block at the end.
    """
    if has_bot_comment(pull_request_description):
        pull_request_description = pull_request_description.split(MESSAGE_HEADER)[0]
    pr_description = pull_request_description.rstrip()
    if not pr_description.endswith("```"):
        return False

    yaml_block_pattern = r"```yaml(.*?)```"
    yaml_block = re.search(yaml_block_pattern, pr_description, re.DOTALL)
    if yaml_block is None:
        return False

    if pr_description.endswith(yaml_block.group(0)):
        try:
            yaml_block_contents = yaml.safe_load(yaml_block.group(1))
            if "dod_yaml" in yaml_block_contents:
                print("Alternative DoD YAML file specified")
                alternative_dod_yaml_path = Path(os.environ["GITHUB_WORKSPACE"]) / Path(
                    yaml_block_contents["dod_yaml"]
                )
                if alternative_dod_yaml_path.exists():
                    with open(alternative_dod_yaml_path, "r") as stream:
                        try:
                            alternative_config = yaml.safe_load(stream)
                            assert_config(alternative_config)
                            # Replace the original config with the alternative one
                            print(
                                "Replacing the original config with the alternative one"
                            )
                            config.clear()
                            config.update(alternative_config)
                        except yaml.YAMLError as yaml_exception:
                            print("Invalid YAML block")
                            print(yaml_exception)
                            return False
                else:
                    print(
                        "Alternative DoD YAML file does not exist in specified path: "
                        + str(alternative_dod_yaml_path)
                    )
                    return False
            else:
                return False

        except yaml.YAMLError as yaml_exception:
            print("Invalid YAML block")
            print(yaml_exception)
            return False
    else:
        print("YAML block found but not at the end of the pull request description")
        return False

    return True


def assert_config(config: dict):
    assert "dod" in config, "No DoD section in config"
    assert isinstance(config["dod"], list), "DoD section is not a list"


def has_unsatisfied_dod(pull_request_description, dod_criteria, optional_tag):
    # Extract the bot message from the pull request description
    bot_message_begin = pull_request_description.find(MESSAGE_HEADER)
    last_criterion = dod_criteria[-1].replace(RIGHT_ARROW_EMOJI, "")
    bot_message_end = pull_request_description.find(last_criterion)
    if bot_message_end == -1:
        print(
            "DoD criteria are missing. "
            + "Please fully remove any remnants of the bot's comment and try again."
        )
        return True
    bot_message = pull_request_description[
        bot_message_begin : bot_message_end + len(last_criterion)
    ]

    # If all boxes are checked, then the DoD is satisfied
    if EMPTY_CHECKMARK not in bot_message:
        print("All DoD criteria are satisfied, no unchecked boxes")
        return False
    # If there are unchecked boxes and no optional tags, then the DoD is unsatisfied
    if not optional_tag:
        print("There are unchecked DoD criteria and no optional tags")
        return True

    print("There are unchecked DoD criteria but they might be optional")
    # If there are optional tags, then only unchecked boxes WITHOUT the optional tag
    # are unsatisfied criteria
    for line in bot_message.split("\n"):
        line = line.strip()
        if line.startswith(EMPTY_CHECKMARK):
            criterion = line[len(EMPTY_CHECKMARK) :].strip()
            if criterion.startswith(optional_tag) or criterion.endswith(optional_tag):
                continue  # Ignore the optional unchecked criterion
            print("Found unchecked DoD criteria that are not optional")
            return True  # Found an unsatisfied non-optional criterion

    print("Found unchecked DoD criteria, but all of them were optional")
    return False


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

    assert_config(config)

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

    maybe_replace_config(config, pull_request_description)
    if has_bot_comment(pull_request_description):
        optional_tag = os.environ.get("INPUT_OPTIONAL_TAG")
        if has_unsatisfied_dod(pull_request_description, config["dod"], optional_tag):
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
            + "needs to be fully marked as satisfied by a repository maintainer. "
            + "Please make sure a maintainer marks off the checklist "
            + "that was appended to the pull request description."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
