# Definition of Done - Checklist for your pull requests
A bot to make you confirm your Definition of Done (DoD) has been satisfied before a pull request can be merged.

## What?

`platisd/definition-of-done` is a GitHub Action that adds a checklist that needs to be ticked off
to your pull requests.<br>
The GitHub Action returns a success code only if all of the items in the checklist have been marked by a maintainer.
This allows projects to remind maintainers and contributors to _manually_ confirm they abide by several criteria,
i.e. the "Definition of Done", for the pull request to be considered good to merge.

## Why?

In an ideal world, the usefulness, correctness and quality of pull requests would be automatically verified.
In practice this does not or cannot happen and we need to manually ensure whether a pull request is in a merge-able
state.

The Definition of Done (DoD) is a set of criteria, determined by a project, which needs to be satisfied to consider
a task/user story as completed ("done"). In GitHub-based projects, this often boils down to the combination of
different conditions that must be true for a pull request to be merged.<br>
While the verification some of these conditions can be automated, e.g. a code review should have taken place,
tests should pass, several quality metrics kept above a particular threshold, others cannot.<br>
Conditions that are not easily automated may be technical, e.g.:
- Change tested on scarcely available hardware
- Programming best practices followed

Or criteria related to the process, e.g.:
- Feature approved by stakeholders
- New API is adequately documented

Keep in mind that the Definition of Done is not the same as the acceptance criteria which are functional
and non-functional requirements for a *specific* task. In other words, the Definition of Done is set at a project
level and remains stable, while the acceptance criteria are specified on a feature level and are different every time.

If you do not care about the DoD semantics, you can use the action to *force* maintainers to manually go through a checklist before the pull request can be merged.

## How?

The GitHub Action posts a comment with the DoD checklist when a pull request is opened and then every time
a comment in the pull request is edited, it checks if _all_ of the checklist items have been marked.
The GitHub Action will keep *failing* until all criteria have been checked as satisfied.<br>

The checklist needs to be provided by the Action's user as a `yaml` file with the following syntax,
also found in the sample [dod.yaml](dod.yaml) utilized by this project:

```yaml
dod:
  - 'Checklist item 1'
  - 'Checklist item 2'
  - 'Checklist item 3'
```

Then you need to create a workflow similar to the one below (also found in
[.github/workflows/dod-checker.yml](.github/workflows/dod-checker.yaml)):

```yaml
name: Definition of Done
on:
  pull_request:
    types: [opened]
  issue_comment:
    types: [edited]

jobs:
  check-dod:
    # Enable this check only when creating a new pull request
    # or when a comment of an open pull request gets edited
    if: |
      github.event_name == 'pull_request' ||
      (github.event_name == 'issue_comment' &&
      github.event.issue.pull_request &&
      github.event.issue.state == 'open')
    runs-on: ubuntu-20.04
    steps:
      - name: Clone Repo
        uses: actions/checkout@v3
      - name: Check DoD
        uses: platisd/definition-of-done@master
        with:
          dod_yaml: 'dod.yaml'
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

Important fields:
* `on`: You should launch this action when there is a new pull request opened and when there's a comment edit
(marking a checklist counts as an edit).
* `if`: You should disable the execution of the job unless the appropriate conditions are present. This will
 skip running the Action needlessly and posting comments on issues instead of pull requests.
* `dod_yaml`: You must specify the relative path to the `yaml` with the checklist you would like to be posted
with the syntax described earlier.
* `github_token`: You must provide the GitHub token for the Action to be able to post comments in your pull request.
* (Optional) `comment_header`: You may provide a custom message to be displayed above the checklist instead of the
default one found in [action.yml]().
