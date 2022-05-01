#!/usr/bin/env python

import os
import sys
import requests
import argparse
import yaml
import json
import time

COMMENT_HEADER = os.environ["INPUT_COMMENT_HEADER"]
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


def is_pull_request_comment_edit_event(github_event):
    return (
        github_event["action"] == "edited"
        and "issue" in github_event
        and "pull_request" in github_event["issue"]
    )


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

    github_token = os.environ.get("INPUT_PAT_TOKEN")
    github_api_url = os.environ.get("GITHUB_API_URL")
    comments_url = "%s/repos/%s/issues/%s/comments" % (
        github_api_url,
        repo,
        pull_request_id,
    )

    comments_get_result = requests.get(
        comments_url, headers={"authorization": "Bearer %s" % github_token}
    )
    if comments_get_result.status_code != 200:
        print(
            "Getting pull request comments to GitHub failed with code: "
            + str(comments_get_result.status_code)
        )
        print(comments_get_result.text)

    bot_comment = get_bot_comment(comments_get_result.json())
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
            # If this action was triggered by a comment edit, we need to trigger the workflow
            # via a pull request edit event, so that its status can be used for approving the pull request
            github_event = {}
            with open(os.environ["GITHUB_EVENT_PATH"]) as f:
                github_event = json.load(f)

            if not github_event:
                print("No GitHub event found")
                return 1

            if is_pull_request_comment_edit_event(github_event):
                # Update the pull request body and then set it back to the original state
                issue_url = "%s/repos/%s/issues/%s" % (
                    github_api_url,
                    repo,
                    pull_request_id,
                )
                get_comment_body_result = requests.get(
                    issue_url, headers={"authorization": "Bearer %s" % github_token}
                )
                if get_comment_body_result.status_code != 200:
                    print(
                        "Getting pull request comment body from GitHub failed with code: "
                        + str(get_comment_body_result.status_code)
                    )
                    print(get_comment_body_result.text)
                    return 1
                pull_request_original_body = get_comment_body_result.json()["body"]
                pull_request_original_title = get_comment_body_result.json()["title"]

                # Update the pull request body and title
                update_comment_body_result = requests.patch(
                    issue_url,
                    headers={"authorization": "Bearer %s" % github_token},
                    # Add a space to the original message which will be trimmed away by GitHub
                    json={
                        "title": pull_request_original_title + " wtf",
                        "body": pull_request_original_body + " ignore this",
                    },
                )
                if update_comment_body_result.status_code != 200:
                    print(
                        "Updating pull request comment body failed with code: "
                        + str(update_comment_body_result.status_code)
                    )
                    print(update_comment_body_result.text)
                    return 1

                print("Updated pull request comment body")
                return 0
            else:
                # If this is a pull request event we can succeed directly
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
            headers={"authorization": "Bearer %s" % github_token},
            json={"body": message},
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
