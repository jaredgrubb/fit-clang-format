import copy
import yaml

class StyleOption(object):
	def __init__(self, name, options):
		self.name = name
		self.options = options

class Style(object):
    def __init__(self, base=None, style=None, hidden_base_style=None):
        if style is None:
            if base is not None:
                style = {'BasedOnStyle': base}
            elif style is None:
                style = {}
        elif base is None:
            base = style['BasedOnStyle']

        self.base = base
        self.style_dict = style
        self.hidden_base_style = hidden_base_style

    def __repr__(self):
        return 'Style(base=%r, style=%r)' % (self.base, self.style_dict)

    def dump(self, output_stream):
        yaml.safe_dump(self.style_dict, stream=output_stream, default_flow_style=False)
        if self.hidden_base_style:
            hidden_keys = [key for key in self.hidden_base_style.style_dict if key not in self.style_dict]
            if hidden_keys:
                hidden_yaml = yaml.safe_dump({k:self.hidden_base_style.style_dict[k] for k in hidden_keys}, default_flow_style=False)
                hidden_yaml = hidden_yaml.splitlines()
                output_stream.write('## Other available options and their default values:\n' % line)
                for line in hidden_yaml:
                    output_stream.write('# %s\n' % line)

    def style_with_overrides(self, overrides):
        # Find the base config to override.
        new_base = overrides.get('BasedOnStyle', self.base)
        new_style_dict = copy.deepcopy(self.style_dict)
        new_style_dict.update(overrides)

        return Style(base=new_base, style=new_style_dict)

    def style_with_defaults_hidden(self, base_style):
        return Style(base=self.base, style=copy.deepcopy(self.style_dict), hidden_base_style=base_style)


# The top-level styles that clang-format supports.
BASE_STYLE_TYPES = [
    'LLVM',
    'Google',
    'Chromium',
    'Mozilla',
    'WebKit',
]

# Keys that we explicitly ignore, either because they don't really apply to what
# we're doing or they are very obscure.
SKIP_STYLE_OPTIONS = [
    'Language',
    'CommentPragmas',
    'DisableFormat',
    'ForEachMacros',
    'JavaScriptQuotes',
    'JavaScriptWrapImports',
    'MacroBlockEnd',
    'MacroBlockBegin',
    'BreakAfterJavaFieldAnnotations',
]

# Set of all styling options.
# The keys of this dictionary represent each setting that can be tweaked.
# The values are arrays of the options for each setting. Each "option" is a dictionary of key-value pairs
# where the key usually repeats the style's top-level name. This is so that some styles (like the UseTab ones)
# can be coupled and handled together.
STYLE_OPTIONS = {}

# Set up the stylings that are just on or off.
STYLE_OPTIONS.update({
    key: StyleOption(key, [
    	{key:True},
    	{key:False},
    ])
    for key in [
        "AlignConsecutiveAssignments",
        "AlignConsecutiveDeclarations",
        "AlignEscapedNewlinesLeft",
        "AlignOperands",
        "AlignTrailingComments",
        "AllowAllParametersOfDeclarationOnNextLine",
        "AllowShortBlocksOnASingleLine",
        "AllowShortCaseLabelsOnASingleLine",
        "AllowShortIfStatementsOnASingleLine",
        "AllowShortLoopsOnASingleLine",
        "AlwaysBreakBeforeMultilineStrings",
        "AlwaysBreakTemplateDeclarations",
        "BinPackArguments",
        "BinPackParameters",
        "BreakBeforeTernaryOperators",
        "BreakConstructorInitializersBeforeComma",
        "BreakStringLiterals",
        "ConstructorInitializerAllOnOneLineOrOnePerLine",
        "Cpp11BracedListStyle",
        "DerivePointerAlignment",
        "ExperimentalAutoDetectBinPacking",
        "IndentCaseLabels",
        "IndentWrappedFunctionNames",
        "KeepEmptyLinesAtTheStartOfBlocks",
        "ObjCSpaceAfterProperty",
        "ObjCSpaceBeforeProtocolList",
        "ReflowComments",
        "SortIncludes",
        "SpaceAfterCStyleCast",
        "SpaceAfterTemplateKeyword",
        "SpaceBeforeAssignmentOperators",
        "SpaceInEmptyParentheses",
        "SpacesInAngles",
        "SpacesInContainerLiterals",
        "SpacesInCStyleCastParentheses",
        "SpacesInParentheses",
        "SpacesInSquareBrackets",
    ]
})

# Set up the stylings that have specific options.
STYLE_OPTIONS.update({
    key: StyleOption(key, [
    	{key:option} for option in options
    ])
    for key,options in {
        'AccessModifierOffset': [-4, -2, -1, 0, 1, 2, 4],
        'AlignAfterOpenBracket': ['Align', 'DontAlign', 'AlwaysBreak'],
        'AllowShortFunctionsOnASingleLine': ['All', 'Inline', 'None', 'Empty'],
        'AlwaysBreakAfterDefinitionReturnType': ['TopLevel', 'None'],
        'AlwaysBreakAfterReturnType': ['None', 'TopLevelDefinitions'],
        'BasedOnStyle': ['WebKit', 'Mozilla', 'Chromium', 'LLVM', 'Google'],
        'BreakBeforeBinaryOperators': ['None', 'NonAssignment', 'All'],
        'BreakBeforeBraces': ['GNU', 'Allman', 'Mozilla', 'Attach', 'Stroustrup', 'Linux', 'WebKit'],
        'ColumnLimit': [0, 80, 90, 100, 110, 120],
        'ConstructorInitializerIndentWidth': [0, 2, 4],
        'ContinuationIndentWidth': [0, 2, 4],
        'IncludeCategories': [[{'Regex': '^"(llvm|llvm-c|clang|clang-c)/', 'Priority': 2}, {'Regex': '^(<|"(gtest|isl|json)/)', 'Priority': 3}, {'Regex': '.*', 'Priority': 1}], [{'Regex': '^<.*\\.h>', 'Priority': 1}, {'Regex': '^<.*', 'Priority': 2}, {'Regex': '.*', 'Priority': 3}]],
        'IncludeIsMainRegex': ['$', '([-_](test|unittest))?$'],
        'IndentWidth': [2, 3, 4, 8],
        "MaxEmptyLinesToKeep": [0, 1, 2, 3, 4],
        'NamespaceIndentation': ['All', 'None', 'Inner'],
        'ObjCBlockIndentWidth': [0, 2, 4],
        'PenaltyBreakBeforeFirstCallParameter': [1, 19],
        'PenaltyBreakComment': [300, 150],
        'PenaltyBreakFirstLessLess': [120, 60],
        'PenaltyBreakString': [1000, 500],
        'PenaltyExcessCharacter': [1000000, 500000],
        'PenaltyReturnTypeOnItsOwnLine': [200, 60],
        'PointerAlignment': ['Middle', 'Right', 'Left'],
        'SpaceBeforeParens': ['Always', 'Never', 'ControlStatements'],
        'SpacesBeforeTrailingComments': [1, 2],
        'Standard': ['Auto','Cpp03','Cpp11'],
        'Standard': ['Cpp11', 'Cpp03', 'Auto'],
    }.iteritems()
})

# The UseTab & TabWidth are coupled.
STYLE_OPTIONS['UseTab'] = StyleOption('UseTab', [
    {'UseTab': 'Never', 'TabWidth': 8},
    {'UseTab': 'ForIndentation', 'TabWidth': 4},
    {'UseTab': 'ForIndentation', 'TabWidth': 8},
    {'UseTab': 'Always', 'TabWidth': 4},
    {'UseTab': 'Always', 'TabWidth': 8},
])
