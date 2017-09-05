class StyleOption(object):
	def __init__(self, name, options):
		self.name = name
		self.options = options

class Style(object):
    def __init__(self, base=None, style=None):
        if style is None:
            if base is not None:
                style = {'BasedOnStyle': base}
            elif style is None:
                style = {}
        elif base is None:
            base = style['BasedOnStyle']

        self.base = base
        self.style = style

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
        'AccessModifierOffset': [-4, -2, -1],
        'AlignAfterOpenBracket': ['Align', 'DontAlign', 'AlwaysBreak'],
        'AllowShortFunctionsOnASingleLine': ['All', 'Inline', 'None', 'Empty'],
        'AlwaysBreakAfterDefinitionReturnType': ['TopLevel', 'None'],
        'AlwaysBreakAfterReturnType': ['None', 'TopLevelDefinitions'],
        'BasedOnStyle': ['WebKit', 'Mozilla', 'Chromium', 'LLVM', 'Google'],
        'BreakBeforeBinaryOperators': ['None', 'NonAssignment', 'All'],
        'BreakBeforeBraces': ['GNU', 'Allman', 'Mozilla', 'Attach', 'Stroustrup', 'Linux', 'WebKit'],
        'ColumnLimit': [0, 80, 90, 100, 110, 120],
        'ConstructorInitializerIndentWidth': [2, 4],
        'ContinuationIndentWidth': [2, 4],
        'IncludeCategories': [[{'Regex': '^"(llvm|llvm-c|clang|clang-c)/', 'Priority': 2}, {'Regex': '^(<|"(gtest|isl|json)/)', 'Priority': 3}, {'Regex': '.*', 'Priority': 1}], [{'Regex': '^<.*\\.h>', 'Priority': 1}, {'Regex': '^<.*', 'Priority': 2}, {'Regex': '.*', 'Priority': 3}]],
        'IncludeIsMainRegex': ['$', '([-_](test|unittest))?$'],
        'IndentWidth': [2, 3, 4, 8],
        "MaxEmptyLinesToKeep": [0, 1, 2, 3, 4],
        'NamespaceIndentation': ['All', 'None', 'Inner'],
        'ObjCBlockIndentWidth': [2, 4],
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

