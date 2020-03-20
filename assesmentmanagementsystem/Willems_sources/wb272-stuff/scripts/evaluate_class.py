#!/usr/bin/env python3
# vim: textwidth=80 tabstop=4 shiftwidth=4 expandtab:

import argparse
import ast
import codecs
import contextlib
import datetime
import importlib
import inspect
import io
import jinja2
import os
import re
import signal
import sys
import textwrap
import time
import traceback

### report template ############################################################

REPORT_TEXT_TEMPLATE="""
{{ '=' * width }}
{{ [title, 'report'] | join(' ') | upper | center(width) }}
{{ ['Generated on ', date, ', at ', time] | join | center(width) }}
{{ '=' * width }}

{% for name in scripts %}
Test file: {{ name }}.py
{{ '=' * (name | length + 14) }}

    {% set mts = tmods[name] %}
    {% for fts in mts.function_setups %}
        {% set fqname = '.'.join([mts.modname, fts.fnname]) %}
Function under test: {{ fqname }}
{{ '-' * (fqname | length + 21) }}
        {% for tfsource in fts.test_sources %}

{{ tfsource }}
        {% endfor %}
    {% endfor %}
{% endfor %}

{{ '=' * width }}
{% for s in students %}
{{ s.student_number }}
    {%- if s.surname is defined %}: {{ s.surname }}, {{ s.names }}{% endif %}

{{ '=' * width }}
    {% for mtr in s.module_test_results %}
Filename:           {{ mtr.mtsetup.filename }}
        {% if not mtr.exists %}
--> MODULE NOT SUBMITTED
        {% elif mtr.has_import_error %}
{{ '-' * width }}
--> IMPORT ERROR
        {% elif mtr.has_syntax_error %}
{{ '-' * width }}
--> SYNTAX ERROR
        {% endif %}
        {% if mtr.has_import_error or mtr.has_syntax_error %}
            {% if mtr.exc_obj['msg'] and mtr.exc_obj['msg'] | count > 0 %}
--> {{ mtr.exc_obj['msg'] | wordwrap(width - 4) | indent(4) }}
            {% endif %}
            {% if mtr.exc_obj['message'] and mtr.exc_obj['message'] | count > 0 %}
--> {{ mtr.exc_obj['message'] | wordwrap(width - 4) | indent(4) }}
            {% endif %}
            {% if mtr.exc_obj['filename'] and mtr.exc_obj['filename'] | count > 0 %}
--> {{ mtr.exc_obj['filename'].split('/')[-2:] | join('/') }}, line {{ mtr.exc_obj['lineno'] }}
            {% endif %}
            {% if mtr.exc_obj['text'] %}
*** Error context:
{{ ' ' * 4 }}{{ mtr.exc_obj['text'] | trim }}
                {% if mtr.exc_obj['offset'] %}
{{ ' ' * 4 }}{{ ' ' * (mtr.exc_obj['offset'] | int) }}^
                {% endif %}
            {% endif %}
        {% endif %}
        {% if mtr.import_success %}
            {% for ftr in mtr.function_test_results %}
Function:           {{ ftr.ftsetup.fnname }}
                {% if ftr.function_not_defined %}
{{ 'NOT DEFINED' | indent(20, true) }}
                {% elif ftr.name_not_a_function %}
{{ 'NAME DEFINED, BUT NOT A FUNCTION' | indent(20, true) }}
                {% else %}
                    {% if not ftr.source_okay %}
*** SOURCE CODE CHECK FAILED ***
                        {% if ftr.illegal_statements %}
Illegal statements: {{ ftr.illegal_statements | join(', ') | indent(20) }}
                        {% elif ftr.illegal_calls %}
Illegal calls:      {{ ftr.illegal_calls | join(', ') | indent(20) }}
                        {% elif ftr.illegal_modules %}
Illegal modules:    {{ ftr.illegal_modules | join(', ') | indent(20) }}
                        {% endif %}
                    {% endif %}
                    {% if ftr.tests_passed | count == ftr.ftsetup.tests | count %}
Results:            PASSED each test
                    {% elif ftr.tests_failed | count == ftr.ftsetup.tests |
count %}
Results:            FAILED each test
                    {% elif ftr.tests_crashed | count == ftr.ftsetup.tests 
| count %}
Results:            CRASHED on each test
                    {% else %}
Results:            {{ [ftr.tests_passed | count, ' passed, '] | join }}
{{- [ftr.tests_failed | count, ' failed, '] | join }}
{{- [ftr.tests_crashed | count, ' crashed'] | join }}
                        {% if ftr.tests_passed | count > 0 %}
{{ ['Tests passed:      ', ftr.tests_passed | join(', ')] | join(' ') | wordwrap(80) | indent(20) }}
                        {% endif %}
                        {% if ftr.tests_failed | count > 0 %}
{{ ['Tests failed:      ', ftr.tests_failed | join(', ')] | join(' ') | wordwrap(80) | indent(20) }}
                        {% endif %}
                        {% if ftr.tests_crashed | count > 0 %}
{{ ['Tests crashed:     ', ftr.tests_crashed | join(', ')] | join(' ') | wordwrap(80) |  indent(20) }}
                        {% endif %}
                    {% endif %}
                    {% for tname in ftr.tests_failed %}
<*> {{ tname }}: {{ ftr.failed_tests_returns[tname] }}
                    {% endfor %}
                    {% for tname in ftr.tests_crashed %}
                        {% set trace = ftr.traces[tname]%}
                        {% set fname = '/' + ftr.mtresults.mtsetup.filename %}

*** Crash trace for {{ tname }}
    {{ trace[0].__name__ }}: {{ trace[1] }}
                        {% for frame in trace[2] if frame[0].endswith(fname) %}
                        {# for frame in trace[2] #}
    *** line {{ frame[1] }} in function '{{ frame[2] }}'
        {{ frame[3] }}
                        {% else %}
    --> Crash in test framework
                        {% endfor %}
                        {% if loop.last %}

                        {% endif %}
                    {% endfor %}
                {% endif %}
            {% endfor %}
        {% endif %}
        {% if mtr.source %}
{{ '-' * width }}
            {% if mtr.source | count > src_max_len %}
SOURCE TOO LONG: Suspected bogus submission
            {% else %}
SOURCE (blank lines stripped)
-----------------------------
{{ mtr.source }}
            {% endif %}
        {% elif mtr.exists %}
------------------------------------------
SOURCE CODE COULD NOT BE READ SUCCESSFULLY
        {% endif %}
{{ '=' * width }}
    {% endfor %}
    {% if not loop.last %}


{{ '=' * width }}
    {% endif %}
{% endfor %}
{{ 'FAMA IN FINEM' | indent(67, true) }}
"""

### helpers ####################################################################

EPSILON = 1e-7


def are_close(m, n):
    """Test "equality" (closeness) of floating-point numbers."""
    return abs(m - n) < EPSILON


def is_valid_student_number(numstr):
    pattern = re.compile(r'^\d\d\d\d\d\d\d\d\Z', re.UNICODE)
    match = pattern.match(numstr)
    if match:
        return sum(i * int(numstr[8-i]) for i in range(1, 9)) % 11 == 0
    else:
        return False


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), *named)
    reverse = dict((value, key) for key, value in enums.iteritems())
    enums['reverse_mapping'] = reverse
    return type('Enum', (), enums)


class File13(object):
    """Eat writes, acting as /dev/null."""

    def write(self, x):
        pass

    def flush(self):
        pass


class UnknownPromptError(Exception):
    """Exception class for an unknown prompt found during raw input capture."""

    def __init__(self, prompt):
        self._prompt = prompt

    def __str__(self):
        return 'Unknown raw_input prompt \'{}\''.format(self._prompt)


class TestError(Exception):
    """Exception class for test case errors."""
    pass


class TimeoutException(Exception):
    """Exception class for a timeout."""
    pass


class SourceVisitor(ast.NodeVisitor):
    """Explore the abstract syntax tree (AST) of a node."""

    def __init__(self, module=None, funcdefs=None):
        self._callables = set()
        self._funcdefs = funcdefs if funcdefs else set()
        self._imports = set()
        self._module = module
        self._module_dir = set(dir(module)) if module else []
        self._visited = set()

    def get_node_types(self):
        return self._visited

    def get_callables(self):
        return self._callables

    def get_illegal_statements(self):
        return self._illegals

    def get_imports(self):
        return self._imports

    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, None)
        if visitor:
            return visitor(node)
        else:
            self._visited.add(node.__class__.__name__)
            return self.generic_visit(node)

    def visit_Call(self, node):
        self._visited.add(node.__class__.__name__)

        # record callables
        callable_name = None
        if isinstance(node.func, ast.Attribute):
            # function
            callable_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            # method
            callable_name = node.func.id
        if callable_name:
            self._callables.add(callable_name)

        # follow the name definition if defined in this module
        if callable_name in self._module_dir:
            call = getattr(self._module, callable_name)
            try:
                source = inspect.getsource(call)
                root = ast.parse(source)
                checker = SourceVisitor(self._module, funcdefs=self._funcdefs)
                checker.visit(root)
                self._visited |= checker.get_node_types()
                self._callables |= checker.get_callables()
            except:
                pass

        # visit recursively
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        if node.name in self._funcdefs:
            return
        self._funcdefs.add(node.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        names = set([name.name for name in node.names])
        self._imports |= names
        self._visited.add('Import')

    def visit_ImportFrom(self, node):
        self._imports.add(node.module)
        self._visited.add('ImportFrom')


class FunctionTestSetup(object):
    """Setup for functions to be tested."""

    def __init__(self, mts, fnname, test_fnname_start):
        self.blacklist = set()
        self.module_test_setup = mts
        mts.add_function_setup(self)
        self.fnname = fnname
        self.function = None
        self.illegal_calls = set()
        self.illegal_statements = set()
        self.legal_calls = set()
        self.test_fnname_start = test_fnname_start
        self.whitelist = set()

        # collect tests
        test_names = [x for x in dir(mts.mod)
                      if x.startswith(test_fnname_start)]
        self.tests = [(x, t) for x, t in [(y, getattr(mts.mod, y))
                      for y in test_names] if callable(t)]
        self.test_sources = [inspect.getsource(t) for _, t in self.tests]

    def set_illegal_calls(self, illegal_calls):
        self.illegal_calls = set(illegal_calls)

    def set_illegal_statements(self, illegal_statements):
        self.illegal_statements = set(illegal_statements)

    def set_legal_calls(self, legal_calls):
        self.legal_calls = set(legal_calls)

    def set_module_blacklist(self, blacklist):
        self.blacklist = set(blacklist)

    def set_module_whitelist(self, whitelist):
        self.whitelist = set(whitelist)

    def set_function(self, function):
        self.function = function


class ModuleTestSetup(object):
    """Setup for the module to be tested."""

    def __init__(self, filename):
        self.filename = filename
        self.function_setups = []
        self.modname = filename.split('.')[0]
        self.mod = sys.modules[__name__]

    def add_function_setup(self, function_setup):
        self.function_setups.append(function_setup)


class RawInputCapture(object):
    """Redirect raw_input to a challenge/response callable object."""

    def __init__(self, prompt_to_response):
        self._prompt_to_response = prompt_to_response

    def __call__(self, prompt=''):
        if prompt in self._prompt_to_response:
            return self._prompt_to_response[prompt]
        else:
            for p in self._prompt_to_response:
                if prompt.startswith(p) or p.startswith(prompt):
                    return self._prompt_to_response[p]
        raise UnknownPromptError(prompt)


# TODO: Refactor properly to strip out code duplication.
# TODO: Consider doing the source visit once, and then to perform a lookup into
#       def nodes; i.e., try to prevent what appears to be the inefficient
#       traversal of the AST more than once.
class FunctionTestResults(object):

    def __init__(self, mtresults, ftsetup):
        self.failed_tests_returns  = {}
        self.ftsetup               = ftsetup
        self.function              = None
        self.function_not_defined  = False
        self.illegal_statements    = None
        self.illegal_calls         = None
        self.illegal_modules       = None
        self.legal_calls           = None
        self.mtresults             = mtresults
        self.name_not_a_function   = False
        self.source_okay           = True
        self.tests_ran             = False
        self.tests_passed          = []
        self.tests_failed          = []
        self.tests_crashed         = []
        self.traces                = {}
        mtresults.add_function_test_results(self)

        # collect the target function(s)
        try:
            self.function = getattr(mtresults.mod, ftsetup.fnname)
            if not callable(self.function):
                self.name_not_a_function = True
                self.function = None
        except AttributeError:
            self.function_not_defined = True
            self.function = None

    def check_source(self):
        # XXX: Consider caching?
        if not self.function:
            # FIXME: Clean up this logic ... maybe add extra variable to
            #        distinguish between function import failure and illegal
            #        source code?
            self.source_okay = False
            return self.source_okay
        fts = self.ftsetup
        function = self.function
        module = sys.modules[function.__module__]

        # visit function source
        source = inspect.getsource(function)
        root = ast.parse(source)
        checker = SourceVisitor(module)
        checker.visit(root)

        # collect illegal (toxic) statements and calls
        toxic_statements = checker.get_node_types() & fts.illegal_statements
        toxic_calls = checker.get_callables() & fts.illegal_calls
        if len(fts.legal_calls) > 0:
            toxic_calls |= checker.get_callables() - fts.legal_calls
        toxic_modules = None

        # check module for imports
        imports = set(['Import', 'ImportFrom']) & fts.illegal_statements
        if len(imports) > 0 or len(fts.blacklist) > 0 or len(fts.whitelist) > 0:
            msource = inspect.getsource(module)
            mroot = ast.parse(msource)
            mchecker = SourceVisitor()
            mchecker.visit(mroot)
            if len(fts.blacklist) == 0 and len(fts.whitelist) == 0:
                toxic_statements |= mchecker.get_node_types() & imports
            else:
                toxic_modules = [m for m in mchecker.get_imports() if m not in
                        fts.whitelist or m in fts.blacklist]

        # collate results
        self.illegal_statements = toxic_statements
        self.illegal_calls = toxic_calls
        self.illegal_modules = toxic_modules
        self.source_okay = not (toxic_modules or len(toxic_statements) > 0 or
                                len(toxic_calls) > 0)

        return self.source_okay

    def run_tests(self):
        self.tests_ran = True
        for name, test in self.ftsetup.tests:
            try:
                rval = test(self.function)
                try:
                    rvalue, expected = rval
                except TypeError:
                    if isinstance(rval, bool):
                        if rval:
                            self.tests_passed.append(name)
                        else:
                            self.tests_failed.append(name)
                            self.failed_tests_returns[name] = 'test case failed'
                    else:
                        msg = 'single-valued return is non-boolean'
                        self.tests_failed.append(name)
                        self.failed_tests_returns[name] = msg
                else:
                    if rvalue == expected:
                        self.tests_passed.append(name)
                    else:
                        self.tests_failed.append(name)
                        self.failed_tests_returns[name] = 'returned {} instead of {}'.format(rvalue, expected)
            except:
                etype, eobj, etb = sys.exc_info()
                if hasattr(eobj, 'text') and eobj.text and eobj.offset:
                    i = 0
                    for ch in eobj.text:
                        if ch == ' ' or ch == '\t':
                            i += 1
                        else:
                            break
                    eobj.offset -= i + 1

                # FIXME: Remove when debugged
                # print('-> etype: {}'.format(etype), file=sys.stderr)
                # print('-> eobj: {}'.format(eobj), file=sys.stderr)

                # FIXME: The following test is extreme fragile
                if etype.__name__ == 'TestError':
                    self.tests_failed.append(name)
                    self.failed_tests_returns[name] = 'failed on "{}"'.format(eobj)
                else:
                    frames = traceback.extract_tb(etb)
                    self.tests_crashed.append(name)
                    if (etype.__name__ == 'RuntimeError' and str(eobj) ==
                            'maximum recursion depth exceeded'):
                        self.traces[name] = (etype, eobj, [])
                    else:
                        self.traces[name] = (etype, eobj, frames)


class ModuleTestResults(object):

    def __init__(self, mtsetup, student_number):
        self.function_test_results = []
        self.exc_obj                = None
        self.exc_tb_frames          = None
        self.exc_type               = None
        self.exists                 = True
        self.has_import_error       = False
        self.has_syntax_error       = False
        self.mtsetup                = mtsetup
        self.mod                    = None
        self.source                 = None
        self.student_number         = student_number

        # import module to be tested
        relmodname = '..' + mtsetup.modname
        package = student_number + '.' + mtsetup.modname
        try:
            with nostdout(), time_limit(2):
                self.mod = importlib.import_module(relmodname, package)
            self.source = inspect.getsource(self.mod)
        except:
            # print('Module not found for {}'.format(student_number),
            #         file=sys.stderr)
            self.exc_type, self.exc_obj, etb = sys.exc_info()
            self.exc_tb_frames = traceback.extract_tb(etb)
            if (hasattr(self.exc_obj, 'text') and self.exc_obj.text and
                    self.exc_obj.offset):
                i = 0
                for ch in self.exc_obj.text:
                    if ch == ' ' or ch == '\t':
                        i += 1
                    else:
                        break
                self.exc_obj.offset -= i + 1

            # FIXME: remove the following when you are done
            # print(student_number, self.exc_type, self.exc_obj, file=sys.stderr)
            # pubattr = [attr for attr in dir(self.exc_obj) if not
            #            attr.startswith('__')]
            # pubattr = {attr: value for attr, value in [(attr,
            #            self.exc_obj.__getattribute__(attr))
            #            for attr in pubattr]}
            # for attr in sorted(pubattr):
            #     print('{}: {}'.format(attr, pubattr[attr]), file=sys.stderr)

            if (isinstance(self.exc_obj, ModuleNotFoundError)
                    and self.exc_obj.msg.startswith('No module named')):
                self.exists = False
            elif isinstance(self.exc_obj, SyntaxError):
                self.has_syntax_error = True
            else:
                self.has_import_error = True

            if (not self.source and hasattr(self.exc_obj, 'filename') and
                    self.exc_obj.filename):
                with codecs.open(self.exc_obj.filename, 'r',
                        encoding='UTF-8') as f:
                    try:
                        self.source = '\n'.join(line for line in f.readlines())
                    except:
                        self.source = None

        self.import_success = (self.exists and not self.has_import_error
                               and not self.has_syntax_error)

        # strip blank lines from the source
        if self.source:
            self.source = '\n'.join(line for line in self.source.split('\n')
                                    if line.strip() != '')

    def add_function_test_results(self, ftresults):
        self.function_test_results.append(ftresults)


class StudentResults(object):

    def __init__(self, student_number):
        self.student_number = student_number
        #self.surname = None
        #self.names = None
        self.module_test_results = []

    def __str__(self):
        return 'student number = {}, surname = {}\nresults = {}'.format(
                self.student_number,
                self.surname,
                self.module_test_results)

    def add_module_test_results(self, mtresults):
        self.module_test_results.append(mtresults)

    def set_names(self, surname, names):
        self.surname = surname
        self.names = names


@contextlib.contextmanager
def raw_input_capture(ric):
    """Capture raw_input."""
    saved_raw_input = __builtins__.raw_input
    __builtins__.raw_input = ric
    try:
        yield
    finally:
        __builtins__.raw_input = saved_raw_input


@contextlib.contextmanager
def output_capture():
    """Capture stdout and stderr."""
    saved_stdout = sys.stdout
    saved_stderr = sys.stderr
    captured_outs = [io.StringIO(), io.StringIO()]
    sys.stdout, sys.stderr = captured_outs
    try:
        yield captured_outs
    finally:
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
        captured_outs[0] = captured_outs[0].getvalue()
        captured_outs[1] = captured_outs[1].getvalue()


@contextlib.contextmanager
def nostdout():
    """Context that prevents writing to the console via stdout.  Any exception
    reattaches stdout to the console."""
    saved_stdout = sys.stdout
    sys.stdout = File13()
    try:
        yield
    except Exception as e:
        sys.stdout = saved_stdout
        raise e
    sys.stdout = saved_stdout


@contextlib.contextmanager
def time_limit(seconds):
    """Apply a time limit to a context (e.g., a function) to prevent infinite
    loops."""
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

### reporting in technicolour ##################################################

ANSI_COLOR_LIST = [('black', 30), ('red', 31), ('green', 32), ('yellow', 33),
        ('blue', 34), ('magenta', 35), ('cyan', 36), ('white', 37)]


def ansi_color(ascii_code):
    def _cfunction(s):
        return '\033[{}m{}\033[m'.format(ascii_code, s)
    return _cfunction


ANSI_COLOR = {n:ansi_color(c) for n, c in ANSI_COLOR_LIST}


def oops():
    return ANSI_COLOR['yellow']('failed')


def facepalm():
    return ANSI_COLOR['red']('crashed')


def yay():
    return ANSI_COLOR['green']('passed')


def doh():
    return ANSI_COLOR['red']('Do\'h!')


def doc(function):
    return ANSI_COLOR['cyan'](function.__doc__)

### test runner ################################################################

def run_tests(student_number, test_mod_setups, test_script_names,
              must_check_source, source_warning_only):
    results = StudentResults(student_number)
    print('Running tests for {}'.format(student_number))
    for test_script_name in test_script_names:
        mtsetup = test_mod_setups[test_script_name]
        mtresults = ModuleTestResults(mtsetup, student_number)
        results.add_module_test_results(mtresults)

        for ftsetup in mtsetup.function_setups:
            ftresults = FunctionTestResults(mtresults, ftsetup)
            if (must_check_source and not ftresults.check_source() and not
                    source_warning_only):
                continue
            ftresults.run_tests()

    print('DONE with {}'.format(student_number))
    return results

### main #######################################################################

def load_test_mods(test_mod_names):
    return {name: mts for name, mts in
            [(nm, importlib.import_module(nm).set_up_tests())
                for nm in test_mod_names]}


def set_up_argparser():
    ap = argparse.ArgumentParser(
        description='Marking script.'
    )
    ap.add_argument(
        '-c', '--classlist',
        default=None,
        help='''the name of the class list file'''
    )
    ap.add_argument(
        '-d', '--disable-source-checking',
        action='store_true',
        help='''disable the checking of source code for disallowed programming
                constructs'''
    )
    ap.add_argument(
        '-s', '--submission-dir',
        default='.',
        help='''the directory from which to read the student directories;
                defaults to the current directory'''
    )
    ap.add_argument(
        '-t', '--title',
        default='Assignment',
        help='''the assignment title, to be used in the generated report; any
                spaces must be escaped in some way'''
    )
    ap.add_argument(
        '-v', '--verbose',
        action='store_false',
        help='''print student numbers to show progress as tests are run'''
    )
    ap.add_argument(
        '-w', '--source-warning-only',
        action='store_true',
        help='''only warn when source does not check out; has no effect when
                source checking is disabled'''
    )
    ap.add_argument(
        'test_scripts',
        metavar='test_script',
        nargs='+',
        help='''the name of the test file to run'''
    )
    return ap


def mark(args):
    # setup
    test_script_names = [n.split('.')[0] for n in args.test_scripts]
    test_mods = load_test_mods(test_script_names)
    sdirs = [d for d in sorted(os.listdir(args.submission_dir))
             if os.path.isdir(d) and is_valid_student_number(d)]
    if args.classlist:
        with open(args.classlist) as f:
            names = {n: (sn, fn) for n, sn, fn in [line.strip().split(',')
                                                   for line in f.readlines()]}
    else:
        names = None

    # run the tests
    results = []
    must_check_source = not args.disable_source_checking
    context = nostdout if args.verbose else contextlib.nullcontext
    with context():
        for student_number in sdirs:
            results.append(run_tests(student_number, test_mods,
                                     test_script_names, must_check_source,
                                     args.source_warning_only))

    # load class list if specified
    if args.classlist:
        with codecs.open(args.classlist, 'r', encoding='UTF-8') as f:
            names = {n: (sn, fn) for n, sn, fn in [line.strip().split(',')
                                                   for line in f.readlines()]}
        for student in results:
            student.set_names(*names[student.student_number])
        results.sort(key=lambda s: s.names)
        results.sort(key=lambda s: s.surname)

    # print the report
    timestamp = datetime.datetime.now()
    today = timestamp.strftime('%A, %-d %B %Y')
    now = timestamp.strftime('%H:%M')
    env = jinja2.Environment(
        loader=jinja2.FunctionLoader(lambda x: REPORT_TEXT_TEMPLATE),
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template(None)
    report = template.render(
        date=today,
        src_max_len=2048,
        students=results,
        tmods=test_mods,
        scripts=test_script_names,
        time=now,
        title=args.title,
        width=80
    )
    print(report)

    return 0


def main():
    sys.path.insert(0, '.')
    ap = set_up_argparser()
    return mark(ap.parse_args())


# run if invoked from the command line
if __name__ == '__main__':
    sys.exit(main())
