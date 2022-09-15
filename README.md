# Definition of Done - Checklist for your pull requests
A bot to make you confirm your Definition of Done (DoD) has been satisfied before a pull request can be merged.

![dod-demo](https://i.imgur.com/EVx32jz.png)

## What?

`platisd/definition-of-done` adds a checklist to your pull request's description, which needs to be ticked off.<br>
The GitHub Action returns a success code only if all of the items in the checklist have been *marked* as done
by a maintainer.
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

The GitHub Action appends the DoD checklist to the pull request description when a pull request is opened.
Then every time an item in the checklist is edited, or to be exact the pull request description is edited,
it checks whether _all_ of the checklist items have been marked.
The GitHub Action will keep *failing* until all criteria have been checked as satisfied.<br>

The checklist needs to be provided by the Action's user as a `yaml` file with the following syntax,
also found in the sample [dod.yaml](dod.yaml) utilized by this project:

```yaml
dod:
  - 'Checklist item 1'
  - 'Checklist item 2'
  - 'Checklist item 3'
```

To create indented (sub)items in the checklist, add the appropriate number of "➡️" characters,
as shown below.

```yaml
dod:
  - 'Checklist item 1'
  - '➡️Checklist item 2'
  - '➡️➡️Checklist item 3'
  - 'Checklist item 4'
```

The example above, will be published as:

> - [ ] Checklist item 1
>   - [ ] Checklist item 2
>     - [ ] Checklist item 3
>  - [ ] Checklist item 4

Finally, you need to create a workflow similar to the one below (also found in
[.github/workflows/dod-checker.yml](.github/workflows/dod-checker.yaml)):

```yaml
name: Definition of Done
on:
  pull_request:
    types: [opened, edited]

jobs:
  check-dod:
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
* `on`: You should launch this action when there is a new pull request opened or edited
(marking a checklist counts as an edit).
* `dod_yaml`: You must specify the relative path to the `yaml` with the checklist you would like to be posted
with the syntax described earlier.
* `github_token`: You must provide the GitHub token for the Action to be able to view and
most importantly edit your pull request description.
* (Optional) `message_header`: You may provide a custom message to be displayed above the checklist instead of the
default one found in [action.yml](action.yml).
