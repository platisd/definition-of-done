# Definition of Done - Checklist for your pull requests
A bot to make you confirm your Definition of Done (DoD) has been satisfied before a pull request can be merged.

## What?

`platisd/definition-of-done` is a GitHub Action that adds a checklist that needs to be ticked off
to your pull requests.<br>
The GitHub Action returns a success code only if all of the items in the checklist have been marked by a maintainer.
This allows projects to remind maintainers and contributors to _manually_ confirm they abide by several criteria,
i.e. the "Definition of Done", for the pull request to be considered good to merge.

## Why?

In an ideal world the usefulness, correctness and quality of pull requests would be automatically verified.
In practice this does not or cannot happen and we need to manually ensure whether a pull request is in a merge-able
state.

The Definition of Done (DoD) is a set of criteria, determined by a project, which need to be satisfied so to consider
a task/user story as completed ("done"). In GitHub-based projects, this often boils down to the combination of
different conditions that must be true for a pull request to be merged.<br>
While the verification some of these conditions can be automated, e.g. a code review should have taken place,
tests should pass, several quality metrics kept above a particular threshold, others cannot.
Conditions that are not easily automated can be technical, e.g.:
- Change tested on scarcely available hardware
- Programming best practices followed

Or criteria related to the process, e.g.:
- Feature approved by stakeholders
- New API is adequately documented

Keep in mind that the Definition of Done is not the same as the acceptance criteria which are functional
and non functional requirements for a *specific* task. In other words, the Definition of Done is set at a project
level and remains same, while the acceptance criteria are specified on a feature level and are different every time.

If you do not care about the DoD semantics, you can use the action to *force* maintainers to manually go through a checklist before the pull request can be merged.

## How?
