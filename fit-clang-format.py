#! /usr/bin/python

from __future__ import print_function

import os
import yaml
import sys

import git
import styles
import util

SRC_DIR = os.getcwd()

RC_FAIL = -1
RC_SUCCESS = 0

# TEMPORARY SAFETY MEASURE :)
if os.path.abspath(SRC_DIR) != os.path.abspath('/private/tmp/test'):
    raise ValueError("This test program only works in one location! I don't want to accidentally clobber a real dir until we're ready.")


class CandidateTracker(object):
    def __init__(self):
        self.accepted_style = None
        self.accepted_score = None
        self.searching = False

    def get_candidate_style(self, overrides):
        if self.accepted_style is None:
            return styles.Style(style=overrides)
        else:
            return self.accepted_style.style_with_overrides(overrides)

    def start(self):
        if self.searching:
            raise RuntimeError("Cannot start; it was already searching")

        self.searching = True
        self.candidate_label = None
        self.candidate_style = None
        self.candidate_score = None

    def finish(self, strictly_better=True):
        if not self.searching:
            raise RuntimeError("Cannot finish; it was not searching")

        self.searching = False

        # Did we consider anything?
        if self.candidate_score is None:
            return False

        # Was it better?
        if self.accepted_score:
            delta = cmp(self.candidate_score, self.accepted_score)
            if strictly_better:
                if delta >= 0:
                    return False
            else:
                if delta > 0:
                    return False

        self.accepted_style = self.candidate_style
        self.accepted_score = self.candidate_score
        return True

    def push_candidate(self, label, style, score):
        if not self.searching:
            raise RuntimeError("Pushed a candidate, but we aren't searching")

        if self.candidate_score is not None:
            if score >= self.candidate_score:
                return False

        self.candidate_score = score
        self.candidate_label = label
        self.candidate_style = style
        return True

    def get_best_style(self):
        return self.accepted_style

    def __repr__(self):
        if self.searching:
            return "CandidateTracker(best_score=%r, best_style=%r, searching_label=%r, searching_score=%r, searching_style=%r)" % (
                self.accepted_score, self.accepted_style,
                self.candidate_label, self.candidate_score, self.candidate_style
            )
        else:
            return "CandidateTracker(best_score=%r, best_style=%r)" % (self.accepted_score, self.accepted_style)

def search(tracker, options, strictly_better=True):
    tracker.start()
    for option in options:
        style = tracker.get_candidate_style(option)

        with repo.apply_temporary_style(style):
            diff = differ.calculate_diff(ignore_spaces=True)
            better = tracker.push_candidate(label=option, score=diff, style=style)

            print('  %s %r: %r %r' % ('!!' if better else '  ', diff, option, style))

    return tracker.finish(strictly_better=strictly_better)


######## START #########

context = {
    'clang-format': 'clang-format', # assume it's in the path

    'files_to_format': None,
}

## Set up context from args
#   TODO

source = SRC_DIR
repo = git.GitRepo(path=SRC_DIR, context=context)
differ = git.GitRepoDiffer()

## Sanity checks.

if not util.check([context['clang-format'], '-version']):
    print("ERROR: Unable to find clang-format binary at path %r" % context['clang-format'])
    sys.exit(RC_FAIL)

if context['files_to_format'] is None:
    context['files_to_format'] = util.get_files_with_extensions('.', ['h','c','cc','cpp','m','mm'])

repo.check()

## Go!

tracker = CandidateTracker()

print("")
print("=> Testing base styles to see which seems to fit best.")
search(tracker, [
    {'BasedOnStyle': base} for base in styles.BASE_STYLE_TYPES
], strictly_better=False)
print(" :: best option so far: %r" % (tracker,))


print("")
print("=> Testing for indent width")
search(tracker, styles.STYLE_OPTIONS['IndentWidth'].options, strictly_better=False)
print(" :: best option so far: %r" % (tracker,))


print("")
print("=> Testing for tabs vs spaces")
search(tracker, styles.STYLE_OPTIONS['UseTab'].options, strictly_better=False)
print(" :: best option so far: %r" % (tracker,))


print("")
print("=> Retesting the bases using indent and tabs")
search(tracker, [
    {'BasedOnStyle': base} for base in styles.BASE_STYLE_TYPES
])
print(" :: best option so far: %r" % (tracker,))


print("")
print("=> Final stage: tweak each key")

for index, key in enumerate(styles.STYLE_OPTIONS.keys()):
    print(" == Round %d of %d: %r" % (index, len(styles.STYLE_OPTIONS), key))
    changed = search(tracker, options=styles.STYLE_OPTIONS[key].options)


print("")
print("=> DONE!")

style = tracker.get_best_style()

print("")
print("Final style:")
print("============")
style.dump(sys.stdout)
print("============")
print("")

print("Applying style to the repo...")
repo.apply_style(style)

print("")
print("The .clang-format file is now in your repo and the style has been applied but not committed.")

sys.exit(RC_SUCCESS)