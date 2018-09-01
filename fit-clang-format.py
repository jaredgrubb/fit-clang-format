#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

# System stuff.
import argparse
import math
import os
import random
import sys

# Third-party stuff.
try:
    import yaml
except ImportError:
    print("Missing library 'pyyaml'.")
    print()
    print('clang-format uses yaml as its configuration file formats. You should install the pyyaml module.')
    print('You can visit https://pyyaml.org to learn more about this module.')
    print()
    print('This command will install it locally just for your user:')
    print('    $ pip install --user pyyaml')
    print()
    print('After installing that, this tool should work.')
    sys.exit(-1)

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
    'SKIP':    ansi.COLORS['dk_gray'],   # verbose text

    'ARROW':   ansi.COLORS['blue'],
    'HEADER':  ansi.COLORS['white'],

    'STYLE_KEY': ansi.COLORS['white'],
    'STYLE_VALUE': ansi.COLORS['dk_yellow'],

    'RANK_BASE':  '',
    'RANK_BETTER':ansi.COLORS['green'],
    'RANK_SAME':  '',
    'RANK_WORSE': ansi.COLORS['red'],
}

RANK_BASE   = lambda: ansi.wrap(ANSI['RANK_BASE'],   '∅')
RANK_BETTER = lambda: ansi.wrap(ANSI['RANK_BETTER'], '+')
RANK_SAME   = lambda: ansi.wrap(ANSI['RANK_SAME'],   '-')
RANK_WORSE  = lambda: ansi.wrap(ANSI['RANK_WORSE'],  '-')

def print_score(score):
    if isinstance(score, (int,float)):
        return '%.02f' % score
    if isinstance(score, tuple):
        return '(%s)' % ', '.join(print_score(x) for x in score)
    return str(score)

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
            if score > self.candidate_score:
                return -1

        self.candidate_score = score
        self.candidate_label = label
        self.candidate_style = style

        if self.accepted_score:
            if score >= self.accepted_score:
                return 0
        return 1

    def get_best_style(self):
        return self.accepted_style

    def __repr__(self):
        if self.searching:
            return "CandidateTracker(best_score=%s, best_style=%r, searching_label=%r, searching_score=%s, searching_style=%r)" % (
                print_score(self.accepted_score), self.accepted_style,
                self.candidate_label, print_score(self.candidate_score), self.candidate_style
            )
        else:
            return "CandidateTracker(best_score=%s, best_style=%r)" % (print_score(self.accepted_score), self.accepted_style)

class StyleCanonicalizer(object):
    def __init__(self):
        self.cache = {}

    def get_base_style(self, base):
        style = self.cache.get(base)
        if not style:
            full_dict = yaml.load(
                util.run([context['clang-format'], '-dump-config', '-style', yaml.dump({'BasedOnStyle':base})])
            )
            style = styles.Style(base=base, style=full_dict)
            self.cache[base] = style
        return style

    def get_canonical_string(self, style):
        base_style = self.get_base_style(style.base)

        # Get the key-value pairs that are different.
        ret = {'BasedOnStyle': style.base}
        for key in base_style.style_dict.keys():
            value = style.style_dict.get(key)
            if value==base_style.style_dict.get(key):
                continue
            ret[key] = value

        return yaml.dump(ret)


class ScoreCache(object):
    def __init__(self):
        self.hasher = StyleCanonicalizer()
        self.cache = {}

    def get_hash_for_style(self, style):
        return self.hasher.get_canonical_string(style=style)

    def get_score(self, style):
        h = self.get_hash_for_style(style)
        return self.cache.get(h)

    def register_score(self, style, score):
        h = self.get_hash_for_style(style)
        self.cache[h] = score


def search(tracker, project, options, strictly_better=True, cache=ScoreCache()):
    tracker.start()
    for option in options:
        style = tracker.get_candidate_style(option)

        rank = RANK_SAME

        score = cache.get_score(style)
        if score is None:
            with project.apply_temporary_style(style):
                score = differ.calculate_diff(project, ignore_spaces=True)
            cache.register_score(style=style, score=score)

        better = tracker.push_candidate(label=option, score=score, style=style)

        if better < 0:
            better_label = RANK_WORSE()
        elif better == 0:
            better_label = RANK_SAME()
        else:
            better_label = RANK_BETTER()

        if verbosity > VERBOSITY_MEDIUM:
            print('  %s %s: %s %r' % (better_label, print_score(score), ansi.wrap(ANSI['STYLE_VALUE'], option), style))
        else:
            print('  %s %s: %s' % (better_label, print_score(score), ansi.wrap(ANSI['STYLE_VALUE'], option)))

    return tracker.finish(strictly_better=strictly_better)


######## START #########

context = {
    'clang-format': 'clang-format', # assume it's in the path
    'ansi': ANSI,
    'verbosity': 0,
    'files_to_format': [],
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
basic_args.add_argument('--git', type=str, metavar='PATH', default=CWD, help='the path to the git-repo to match; paths are relative to this')
basic_args.add_argument('--include-extensions', type=str, metavar='EXTENSIONS', default='h,hpp,c,cc,cpp,m,mm', help='add all files with these extensions, comma-delimited')
basic_args.add_argument('-I', '--include-path', type=str, metavar='PATH', action='append', help='path/file to search for files; can be specified multiple times')
basic_args.add_argument('-E', '--exclude-path', type=str, metavar='PATH', action='append', help='path/file to exclude from the analysis; can be specified multiple times. Exclusions apply after include filters.')
basic_args.add_argument('--randomly-limit', type=int, metavar='NUM', help='randomly select NUM files; files will be selected according to relative frequence by extension (min 1)')
basic_args.add_argument('--diff-score', choices=sorted(git.diff_options.keys()), default=git.diff_default, help='the scoring algorithm to use')

basic_args = parser.add_argument_group('Style Options')
basic_args.add_argument('--style-base', choices=sorted(styles.BASE_STYLE_TYPES), help='force a specific base style')
basic_args.add_argument('--force-style', type=str, metavar='YAML', help='force a starting style (removes these keys from further consideration)')
basic_args.add_argument('--skip-option', type=str, action='append', metavar='PATH', help='skip a style option key with this name; can be specified multiple times')

basic_args = parser.add_argument_group('Environment options')
basic_args.add_argument('--clang-format-path', type=str, metavar='PATH', help='the path to the clang-format tool')

output_args = parser.add_argument_group('Output options')
output_args.add_argument('--verbose', '-v', action='count')
output_args_ansi_group = output_args.add_mutually_exclusive_group()
output_args_ansi_group.add_argument('--no-ansi', action='store_true', help='force disable ANSI colors')
output_args_ansi_group.add_argument('--ansi',    action='store_true', help='force enable ANSI colors')

args = parser.parse_args()


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
    base_path = os.getcwd()
else:
    base_path = os.path.realpath(args.git)
if not os.path.isdir(base_path):
    print(ansi.wrap(ANSI['E'], "ERROR: The path %r does not exist." % base_path))
    sys.exit(RC_FAIL)
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Using git repo at %r" % base_path))

project = git.GitProject(path=base_path, context=context)


# Build the list of files to test.
context['files_to_format'] = project.get_files(extensions=args.include_extensions.split(','))
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Matched %d files from --include-extensions matches." % len(context['files_to_format'])))

if args.include_path is None:
    pass
elif '.' in args.include_path:
    # Special case of '.' means "match all"
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping --include-path filtering because '.' is in the list (matches everything)."))
else:
    def matcher(f):
        result = any(f.startswith(p) for p in args.include_path)
        if not result and verbosity>VERBOSITY_MEDIUM:
            print(ansi.wrap(ANSI['V'], "[VV] The --include-path argument rejects file %r" % f))
        return result

    context['files_to_format'] = [
        f for f in context['files_to_format']
        if matcher(f)
    ]

    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Matched %d files after applying %d --include-path paths." % (len(context['files_to_format']), len(args.include_path))))

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

    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Matched %d files after applying %d --exclude-path paths." % (len(context['files_to_format']), len(args.exclude_path))))

if args.randomly_limit is None:
    pass
elif args.randomly_limit <= 0:
    print(ansi.wrap(ANSI['E'], "ERROR: --limit-random should be a positive number."))
    sys.exit(RC_FAIL)
elif args.randomly_limit >= len(context['files_to_format']):
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping random selection because limit of %d is larger than list of files." % (args.randomly_limit)))
else:
    files_by_extension = {}
    for f in context['files_to_format']:
        _, ext = os.path.splitext(f)
        files_by_extension.setdefault(ext, []).append(f)

    context['files_to_format'] = []
    for files in files_by_extension.itervalues():
        random.shuffle(files)

        # Always keep one of each file for sure.
        context['files_to_format'].append(files.pop())

    # Then take a fraction of each list, weighted by relative frequency
    full_count = sum(len(files) for files in files_by_extension.itervalues())
    keep_fraction = float(args.randomly_limit - len(files_by_extension)) / full_count
    for ext, files in files_by_extension.iteritems():
        i = int(round(keep_fraction * len(files)))
        if verbosity:
            # XX: the plus-one here is to account for the one file we selected in the first for loop above.
            print(ansi.wrap(ANSI['V'], "[V] Random Filter: keeping %d of %d files for extension %r." % (1+i, 1+len(files), ext)))
        context['files_to_format'].extend(files[:i])

    context['files_to_format'].sort()


if not context['files_to_format']:
    print(ansi.wrap(ANSI['E'], "ERROR: No files found to format."))
    sys.exit(RC_FAIL)
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Final file count after all filters is %d files" % (len(context['files_to_format']))))


# Pick the diff strategy.
differ = git.diff_options[args.diff_score]()
if verbosity:
    print(ansi.wrap(ANSI['V'], "[V] Using diff strategy %r." % args.diff_score))


# Check for starting styles
init_style = {}
if args.force_style:
    init_style = yaml.load(args.force_style)
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Applying a force-style (%d keys)." % len(init_style)))

if args.style_base:
    init_style['BasedOnStyle'] = args.style_base
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Forcing the style to be based on %r." % args.style_base))

skip_keys = set(init_style.keys())
if args.skip_option:
    skip_keys.update(args.skip_option)
if verbosity and skip_keys:
    print(ansi.wrap(ANSI['V'], "[V] Will skip consideration of a total of %d style option keys." % len(skip_keys)))


## Go!

# Sanity-check that we can proceed.
project.check()

if init_style:
    base_style = styles.Style(style=init_style)
    tracker = CandidateTracker(base_style)
else:
    tracker = CandidateTracker()


if 'BasedOnStyle' in skip_keys:
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping tests for BasedOnStyle."))
else:
    print("")
    print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Testing base styles to see which seems to fit best."))
    search(tracker, project, [
        {'BasedOnStyle': base} for base in styles.BASE_STYLE_TYPES
    ], strictly_better=False)
    print(" :: best option so far: %r" % (tracker,))

if 'IndentWidth' in skip_keys:
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping tests for IndentWidth."))
else:
    print("")
    print(ansi.wrap(ANSI['ARROW'], "=>") + ansi.wrap(ANSI['HEADER'], " Testing for indent width"))
    search(tracker, project, styles.STYLE_OPTIONS['IndentWidth'].options, strictly_better=False)
    print(" :: best option so far: %r" % (tracker,))


if 'UseTab' in skip_keys:
    if verbosity:
        print(ansi.wrap(ANSI['V'], "[V] Skipping tests for UseTab."))
else:
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
    if key in skip_keys:
        print(ansi.wrap(ANSI['SKIP'], "   (skipped)"))
        continue

    changed = search(tracker, project, options=styles.STYLE_OPTIONS[key].options)
    if changed:
        print(" :: UPDATED! Added a new option that improved the score.")
    else:
        print(ansi.wrap(ANSI['SKIP'], " :: Skipped. No option improved the fit."))


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


full_style_dict = yaml.load(
    util.run([context['clang-format'], '-dump-config', '-style', yaml.dump({'BasedOnStyle':base})])
)
full_style = styles.Style(base=style.base, style=full_style_dict)
project.apply_style(style.style_with_defaults_hidden(full_style))

print("""
The .clang-format file is now in your project and the style has been applied but not committed.

Next steps:
 - review the diff and see if you like the changes.
    - look for outlier files (eg, code you never want formatted, like external OSS projects)
      Outlier files could have different code style that is influencing the search.
    - review the style and see if there are any changes you prefer
 - if you don't like the result (eg, maybe your code has many different styles), consider alternate options:
    - pick a subdirectory or set of files that does have the style you like and re-run this tool
      using the '-I' option.
    - start from a known style base (--style-base)
    - start from a manually-select style (--force-style)
 - to re-run, reset your repo and start over.
 - if you're happy with the style:
   - add it to your repo and check it in.
   - read the clang-format docs which has lots of ways to integrate it into your workflow
      (vim intergration, git integration, BBEdit, etc)
      URL: https://clang.llvm.org/docs/ClangFormat.html
""")
print("")
print("")

sys.exit(RC_SUCCESS)