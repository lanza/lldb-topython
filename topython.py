import lldb
import re
import argparse
import shlex

# `topython` translates LLDB commands to Python API. The translation happens
# using the following dictionaries.

# The `CommandAPIs` dictionary translates full commands to one or more Python
# APIs. Before this can be used, any given command must first be expanded using
# `ResolveCommand()`, which turns aliases (`po`) and abbreviations (`br s`) to
# canonical full commands.
CommandAPIs = {
    ### Thread Commands
    "thread step-over": ["lldb.SBThread.StepOver"],
    "thread step-in": ["lldb.SBThread.StepInto"],
    "thread step-inst": ["lldb.SBThread.StepInstruction(False)"],
    "thread step-inst-over": ["lldb.SBThread.StepInstruction(True)"], # TODO: Document parameter
    "thread return": ["lldb.SBThread.ReturnFromFrame(SBFrame, SBValue)"],
    "thread jump": ["lldb.SBThread.JumpToLine", "lldb.SBFrame.SetPC"], # TODO: Jump to address
    "thread until": ["lldb.SBThread.StepOverUntil"],

    ### Process Commands
    "process continue": ["lldb.SBProcess.Continue"],

    ### Expression Command
    "expression": [
        "lldb.SBFrame.EvaluateExpression",
        "lldb.SBTarget.EvaluateExpression",
        # "lldb.SBExpressionOptions",
    ],

    ### Frame Commands
    "frame variable": [
        "lldb.SBFrame.GetVariables",
        "lldb.SBFrame.FindVariable",
    ],
    # "frame info": [],

    ### Breakpoint Commands
    "breakpoint set": [
        "lldb.SBTarget.BreakpointCreateByAddress",
        "lldb.SBTarget.BreakpointCreateByLocation",
        "lldb.SBTarget.BreakpointCreateByName",
        "lldb.SBTarget.BreakpointCreateByNames",
        "lldb.SBTarget.BreakpointCreateByRegex",
        "lldb.SBTarget.BreakpointCreateBySBAddress",
        "lldb.SBTarget.BreakpointCreateBySourceRegex",
    ],
    # "breakpoint clear": ...,
    "breakpoint command": [
        "lldb.SBBreakpoint.SetCommandLineCommands",
        "lldb.SBBreakpoint.SetScriptCallbackBody",
        "lldb.SBBreakpoint.SetScriptCallbackFunction",
    ],
    "breakpoint delete": [
        "lldb.SBTarget.DeleteAllBreakpoints",
        "lldb.SBTarget.BreakpointDelete",
    ],
    "breakpoint disable": [
        "lldb.SBTarget.DisableAllBreakpoints",
        "lldb.SBBreakpoint.SetEnabled(False)",
    ],
    "breakpoint enable": [
        "lldb.SBTarget.EnableAllBreakpoints",
        "lldb.SBBreakpoint.SetEnabled(True)",
    ],
    "breakpoint list": [
        "lldb.SBTarget.breakpoint_iter",
        "lldb.SBTarget.GetNumBreakpoints",
        "lldb.SBTarget.GetBreakpointAtIndex",
        # "lldb.SBTarget.GetBreakpointNames",
    ],
    "breakpoint modify": [
        "lldb.SBBreakpoint.SetAutoContinue",
        "lldb.SBBreakpoint.SetCondition",
        "lldb.SBBreakpoint.SetIgnoreCount",
        "lldb.SBBreakpoint.SetOneShot",
        "lldb.SBBreakpoint.SetQueueName",
        "lldb.SBBreakpoint.SetThreadIndex",
        "lldb.SBBreakpoint.SetThreadName",
        # "lldb.SBBreakpoint.SetThreadID"
    ],
    "breakpoint name": [
        "lldb.SBBreakpoint.AddName",
        "lldb.SBBreakpoint.GetNames",
        "lldb.SBBreakpoint.MatchesName",
        "lldb.SBBreakpoint.RemoveName",
    ],

    ### Register Commands
    "register read": [
        "lldb.SBFrame.FindRegister",
        "lldb.SBFrame.GetRegisters",
    ],

    # Memory Commands
    "memory read": [
        "lldb.SBProcess.ReadMemory",
        "lldb.SBTarget.ReadMemory",
    ],
    "memory write": [
        "lldb.SBProcess.WriteMemory",
    ],
}

# Translate regexp commands to their analagous full command.
RegexCommands = {
    "_regexp-break": "breakpoint set",
    "_regexp-jump": "thread jump",
}

def _breakpoint_modify_parser():
    parser = argparse.ArgumentParser(prog="breakpoint modify")
    parser.add_argument('--auto-continue', '-C')
    parser.add_argument('--condition', '-c')
    parser.add_argument('--disable', '-d', action='store_const', const=True, default=None)
    parser.add_argument('--enable', '-e', action='store_const', const=True, default=None)
    parser.add_argument('--ignore-count', '-i')
    parser.add_argument('--one-shot', '-o')
    parser.add_argument('--queue-name', '-q')
    parser.add_argument('--thread-index', '-x')
    parser.add_argument('--thread-name', '-T')
    return parser

CommandParsers = {
    "breakpoint modify": _breakpoint_modify_parser(),
}

CommandFlagAPIs = {
    "breakpoint modify": {
        "auto_continue": "lldb.SBBreakpoint.SetAutoContinue",
        "condition": "lldb.SBBreakpoint.SetCondition",
        "disable": "lldb.SBBreakpoint.SetEnabled(False)",
        "enable": "lldb.SBBreakpoint.SetEnabled(True)",
        "ignore_count": "lldb.SBBreakpoint.SetIgnoreCount",
        "one_shot": "lldb.SBBreakpoint.SetOneShot",
        "queue_name": "lldb.SBBreakpoint.SetQueueName",
        "thread_index": "lldb.SBBreakpoint.SetThreadIndex",
        "thread_name": "lldb.SBBreakpoint.SetThreadName",
    }
}

# [one, two, three] -> "(one|two|three)\b"
KnownCommands = re.compile(r"({})\b".format(
    "|".join(CommandAPIs.keys() + RegexCommands.keys())))

@lldb.command("topython")
def topython(debugger, command, context, result, _internal):
    """Translate LLDB commands to Python API"""

    if not command:
        result.SetError("Usage: topython <lldb-command>")
        return

    # Expand aliases and abbreviations into their base command.
    resolve_result = lldb.SBCommandReturnObject()
    debugger.GetCommandInterpreter().ResolveCommand(command, resolve_result)
    if not resolve_result.Succeeded():
        result.SetError("Nonexistent command: " + command)
        return
    expanded_command = resolve_result.GetOutput()

    # Match the fully resolved command against supported commands. In addition
    # to checking for a known command, this also strips flags and arguments.
    match = KnownCommands.match(expanded_command)
    if not match:
        result.SetError("Unsupported command: " + command)
        return
    known_command = match.group(0)

    # Convert regex commands into core commands.
    if known_command in RegexCommands:
        known_command = RegexCommands[known_command]

    parser = CommandParsers.get(known_command)
    if parser:
        command_args = expanded_command[len(known_command):]
        parsed_args, _ = parser.parse_known_args(shlex.split(command_args))

        # Exrtract just the flag names given in the command.
        command_flags = [
            name
            for name, value in vars(parsed_args).iteritems()
            if value is not None
        ]

        if command_flags:
            flagAPIs = CommandFlagAPIs[known_command]
            for flag in command_flags:
                _print_help(flagAPIs[flag])
            return

    APIs = CommandAPIs.get(known_command)
    if APIs is None:
        result.SetError("Incomplete support, missing API info for `{}`".format(command))
        return

    if len(APIs) > 2:
        # Print just the APIs by name, but not their help() documentation, to
        # avoid printing too much detail.
        for API in APIs:
            print API
        return

    for API in APIs:
        _print_help(API)

def _print_help(API):
    match = re.match(r"[^(]+", API)
    assert match
    help(match.group(0))
    # Also print full API when it contains parameter info.
    if "(" in API:
        print API
