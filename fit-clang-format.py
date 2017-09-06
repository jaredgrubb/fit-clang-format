#! /usr/bin/python

from __future__ import print_function

# System stuff.
import argparse
import os
import yaml
import sys

# Project-local stuff.
import ansi
import git
import styles
import util

RC_FAIL = -1
RC_SUCCESS = 0

PROGRAM_VERSION = "0.1"

VERBOSITY_LOW = 0
VERBOSITY_MEDIUM = 1
VERBOSITY_HIGH = 2

ANSI = {
    'RESET':   ansi.COLORS['reset'],
    'E':       ansi.COLORS['red'],       # errors
    'W':       ansi.COLORS['yellow'],    # warnings
    'V':       ansi.COLORS['dk_gray'],   # verbose text

    'ARROW':   ansi.COLORS['blue'],
    'HEADER':  ansi.COLORS['white'],
}

class CandidateTracker(object):
    def __init__(self, base_style=None):
        self.accepted_style = base_style
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

def search(tracker, project, options, strictly_better=True):
    tracker.start()
    for option in options:
        style = tracker.get_candidate_style(option)

        with project.apply_temporary_style(style):
            diff = differ.calculate_diff(project, ignore_spaces=True)
            better = tracker.push_candidate(label=option, score=diff, style=style)

            print('  %s %r: %r %r' % ('!!' if better else '  ', diff, option, style))

    return tracker.finish(strictly_better=strictly_better)


######## START #########

context = {
    'clang-format': 'clang-format', # assume it's in the path
    'ansi': ANSI,
    'verbosity': 0,
    'files_to_format': None,
}

verbosity = 0

# Sentinels to help with argparse arguments.
CWD = util.SentinelWithHelpText('CWD')

## Set up context from args
parser = argparse.ArgumentParser(
    description='Generate a clang-format style file to match existing source conventions.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument('--version', action='version', version='%(prog)s version ' + PROGRAM_VERSION)

basic_args = parser.add_argument_group('Project Options')
basic_args.add_argument('--git', type=str, metavar='PATH', default=CWD, help='the path to the git-repo to match')
basic_args.add_argument('--include-extensions', type=str, metavar='EXTENSIONS', default='h,hpp,c,cc,cpp,m,mm', help='add all files with these extensions')
basic_args.add_argument('--exclude-path', type=str, metavar='PATH', action='append', help='a path/file to exclude from the analysis; can be specified multiple times')
basic_args.add_argument('--git-diff-score', choices=sorted(git.diff_options.keys()), default=git.diff_default, help='the scoring algorithm to use')


basic_args = parser.add_argument_group('Environment options')
basic_args.add_argument('--clang-format-path', type=str, metavar='PATH', help='the path to the clang-format tool')
basic_args.add_argument('--style-base', choices=sorted(styles.BASE_STYLE_TYPES), help='force a specific base style')

output_args = parser.add_argument_group('Output options')
output_args.add_argument('--verbose', '-v', action='count')
output_args_ansi_group = output_args.add_mutually_exclusive_group()
output_args_ansi_group.add_argument('--no-ansi', action='store_true', help='force disable ANSI colors')
output_args_ansi_group.add_argument('--ansi',    action='store_true', help='force enable ANSI colors')

args = parser.parse_args()

print(args)

# Set up things that affect our logging.
verbosity = args.verbose
context['verbosity'] = verbosity

if args.no_ansi:
    use_ansi = False
elif args.ansi:
    use_ansi = True
else:
    use_ansi = sys.stdout.isatty()
if not use_ansi:
    # Zap all the color strings in the dict so we don't print them.
    for k in ANSI:
        ANSI[k] = ''


# Find clang-format binary.
if args.clang_format_path is None:
    # Look for clang-format in the path.
    try:
        context['clang-format'] = util.run(['which', 'clang-format']).strip()
    except:
        print(ansi.wrap(ANSI['E'], "ERROR: Unable to find clang-format tool in the path; maybe specify --clang-format-path with an explicit path?"))
        sys.exit(RC_FAIL)
else:
    # They may pass in either the executable itself, or the path that contains the executable.
    if util.check([args.clang_format_path, '-version']):
        context['clang-format'] = args.clang_format_path
    elif util.check([os.path.join(args.clang_format_path, 'clang-format'), '-version']):
        context['clang-format'] = os.path.join(args.clang_format_path, 'clang-format')
    else:
        print(ansi.wrap(ANSI['E'], "ERROR: Unable to find clang-format binary at path %r" % args.clang_format_path))
        sys.exit(RC_FAIL)
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Using clang-format at location %r" % context['clang-format']))


# For now, we only support git repos.
if args.git is CWD:
    source_path = os.getcwd()
else:
    source_path = os.path.realpath(args.git)
if not os.path.isdir(source_path):
    print(ansi.wrap(ANSI['E'], "ERROR: The source path %r does not exist." % source_path))
    sys.exit(RC_FAIL)
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Using source git repo at %r" % source_path))

project = git.GitProject(path=source_path, context=context)


# Build the list of files to test.
if context['files_to_format'] is None:
    context['files_to_format'] = project.get_files(extensions=args.include_extensions.split(','))
if not context['files_to_format']:
    print(ansi.wrap(ANSI['E'], "ERROR: No files found to format."))
    sys.exit(RC_FAIL)

if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Matched %d files from --include-extensions matches." % len(context['files_to_format'])))

if args.exclude_path:
    def matcher(f):
        result = any(f.startswith(p) for p in args.exclude_path)
        if result and verbosity>VERBOSITY_MEDIUM:
            print(ansi.wrap(ANSI['V'], "[VV] The --exclude-path argument excludes file %r due to ." % f))
        return result

    context['files_to_format'] = [
        f for f in context['files_to_format']
        if not matcher(f)
    ]

    print(ansi.wrap(ANSI['V'], "[V] Matched %d files after applying --exclude-path matches." % len(context['files_to_format'])))


# Pick the diff strategy.
differ = git.diff_options[args.git_diff_score]()
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Using diff strategy %r." % args.git_diff_score))


## Go!

# Sanity-check that we can proceed.
project.check()

if args.style_base:
    skip_keys = ['BasedOnStyle']
    base_style = styles.Style(style={'BasedOnStyle': args.style_base})
    tracker = CandidateTracker(base_style)
else:
    skip_keys = []
    tracker = CandidateTracker()


if 'BasedOnStyle' in skip_keys:
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping tests for base style due to --style-base argument."))
else:
    print("")
    print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Testing base styles to see which seems to fit best."))
    search(tracker, project, [
        {'BasedOnStyle': base} for base in styles.BASE_STYLE_TYPES
    ], strictly_better=False)
    print(" :: best option so far: %r" % (tracker,))


print("")
print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Testing for indent width"))
search(tracker, project, styles.STYLE_OPTIONS['IndentWidth'].options, strictly_better=False)
print(" :: best option so far: %r" % (tracker,))


print("")
print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Testing for tabs vs spaces"))
search(tracker, project, styles.STYLE_OPTIONS['UseTab'].options, strictly_better=False)
print(" :: best option so far: %r" % (tracker,))


if 'BasedOnStyle' in skip_keys:
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping re-test of base style."))
else:
    print("")
    print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Retesting the bases using indent and tabs"))
    search(tracker, project, [
        {'BasedOnStyle': base} for base in styles.BASE_STYLE_TYPES
    ])
    print(" :: best option so far: %r" % (tracker,))


print("")
print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Final stage: tweak each key"))

for index, key in enumerate(styles.STYLE_OPTIONS.keys()):
    print(ansi.wrap(ANSI['HEADER'], " == Round %d of %d: %r" % (index, len(styles.STYLE_OPTIONS), key)))
    changed = search(tracker, project, options=styles.STYLE_OPTIONS[key].options)


print("")
print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " DONE!"))

style = tracker.get_best_style()

print("")
print("Final style:")
print("============")
style.dump(sys.stdout)
print("============")
print("")

print("Applying style to the project..")
project.apply_style(style)

print("")
print("The .clang-format file is now in your project and the style has been applied but not committed.")

sys.exit(RC_SUCCESS)