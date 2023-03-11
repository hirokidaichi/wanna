

import subprocess
import tempfile
from enum import Enum
import re
import sys
import questionary
import click
import subprocess_tee
import click_spinner
from . import chatter
from . import config


def extract_arguments(code):
    matches = re.findall(r"\$[0-9]+", code)
    return matches


def require_args_if_need(code):
    args = extract_arguments(code)
    if len(args) > 0:
        args_string = questionary.text(f"Please input arguments:").ask()
        return split_by_whitespace(args_string)
    return []


def think_with_spinner(agent, message):
    with click_spinner.spinner():
        agent.think_script(message)


def retry_if_fail(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return func(*args, **kwargs)
            except:
                if questionary.confirm("Oops, something went wrong. Retry?").ask():
                    pass
                else:
                    sys.exit(0)
    return wrapper


def execute_bash_tee(filename, args=[]):
    return subprocess_tee.run(["bash", filename] + args)


def execute_bash(filename, args=[]):
    return subprocess.run(["bash", filename] + args)


def create_tmp_file(code):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(code.encode("utf-8"))
        return tmp_file.name


class NextAction(Enum):
    DO = "Do"
    SAVE = "Save"
    ADDITONAL_REQUEST = "Additonal Request"
    ANOTHER_QUESTION = "Another Question"
    EXIT = "Exit"


def split_by_whitespace(string):
    regex = re.compile(r'\s+')
    return regex.split(string)


def call_whats_next():
    na = questionary.select(
        "What's next?",
        choices=[e.value for e in NextAction],
    ).ask()
    return NextAction(na)


def try_save(agent):
    retry_think_script_name = retry_if_fail(lambda: agent.think_script_names())

    names = retry_think_script_name()
    selected_name = questionary.select(
        "I thought of the following names. Which one do you like?",
        choices=names,
    ).ask()
    summary = agent.question_summary()
    click.echo(f"Saved as {selected_name}: Description:{summary}")
    config.save_script(selected_name, agent.code, summary)


def conversation_cycle(agent, is_display_comment=True):
    display_comment = agent.display_comment
    code = agent.code

    if is_display_comment:
        if code is None:
            click.echo(click.style("AI Answer:",
                                   bold=True, underline=True, reverse=True))
            click.echo(display_comment)
            click.echo(click.style("Sorry, I could not generate the proper code from your comment.",
                                   fg="red", bold=True))
            sys.exit(0)

        click.echo(click.style("AI Answer:", bold=True, reverse=True))
        click.echo(display_comment)

    next_action = call_whats_next()

    if next_action == NextAction.DO:
        tmp = create_tmp_file(code)
        args = require_args_if_need(code)
        result = execute_bash_tee(tmp, args)
        agent.report_result(result)
        if result.returncode != 0 or len(result.stderr) > 0:
            think_again = questionary.confirm(
                "Something doesn't seem to be going right. \nCan I try to fix the code?", default=False).ask()
            if think_again:
                think_with_spinner(agent, "")

                return conversation_cycle(agent, is_display_comment=True)

        return conversation_cycle(agent, is_display_comment=False)

    elif next_action == NextAction.SAVE:
        return try_save(agent)

    elif next_action == NextAction.ADDITONAL_REQUEST:
        text = questionary.text("What additional requests do you have?").ask()
        think_with_spinner(agent, text)
        return conversation_cycle(agent)

    elif next_action == NextAction.ANOTHER_QUESTION:
        return what_wanna_do(agent.question_summary())

    elif next_action == NextAction.EXIT:
        sys.exit(0)


def what_wanna_do(default_question=""):
    question = questionary.text(
        'What do you want to do ?', default=default_question).ask()

    if len(question.strip()) == 0:
        click.echo("please tell me what you wanna do", err=True)
        sys.exit(0)
    agent = chatter.BashAgent()

    think_with_spinner(agent, question)

    conversation_cycle(agent)


@click.group()
def cmd():
    """Shell command launcher with natural language"""
    pass


def fill_command(command):
    if config.exists(command):
        return command
    ideas = config.ideas()
    command_and_question = questionary.autocomplete(
        'Choose command',
        choices=ideas).ask()
    got_command = command_and_question.split(":")[0].strip()
    if config.exists(got_command):
        return got_command
    else:
        sys.exit(0)


def fill_args(cmd):
    return require_args_if_need(config.get_code(cmd))


@cmd.command()
@click.argument('command', required=False)
@click.argument("args", nargs=-1)
def do(command=None, args=None):
    """Execute a command"""
    cmd = fill_command(command)
    args = [a for a in args] if args is not None else []
    filled_args = args if command else fill_args(cmd)

    execute_bash(config.get_command_path(cmd), filled_args)


@cmd.command()
@click.argument('question', required=False)
def think(question=None):
    """Generate a bash script that answers the incoming request"""
    if (question is None):
        what_wanna_do()
    else:
        what_wanna_do(question)


@cmd.command()
@click.option('--command', is_flag=True)
def list(command):
    """List up all commands"""

    target_list = config.commands() if command else config.ideas()

    for value in target_list:
        click.echo(value)


@cmd.command()
@click.argument('command', required=False)
@click.argument("args", nargs=-1)
def remove(command, args):
    """Remove selected command"""
    click.echo("Removed:" + command)
    cmd = fill_command(command)
    config.remove(cmd)


def main():
    cmd()


if __name__ == '__main__':
    main()
