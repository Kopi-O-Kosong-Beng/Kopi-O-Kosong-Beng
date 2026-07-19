# Profile Easter Egg Clarity Design

## Purpose

Remove the impression that visitors must run a command to view the GitHub profile.

## Change

Replace the `brew --profile` summary with the plain text label `a little more about me`. Remove code styling from both expandable section labels.

The animated signal lab, introduction, portfolio link, LinkedIn link, and email link remain visible immediately. The expandable sections remain optional Easter eggs and do not contain information required to understand the profile.

## Validation

The profile tests must confirm that the old command text is absent, the new label is present, and both native expandable sections remain available. The rendered README must remain valid on GitHub.
