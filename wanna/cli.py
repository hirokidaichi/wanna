

import subprocess
import tempfile
from enum import Enum
import re
import sys
import questionary
import click
from subprocess_tee import run
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


def execute_bash_tee(filename, args=[]):
    return run(["bash", filename] + args)


def execute_bash(filename, args=[]):
    return subprocess.run(["bash", filename] + args)


def create_tmp_file(code):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(code.encode("utf-8"))
        return tmp_file.name


def split_by_whitespace(string):
    regex = re.compile(r'\s+')
    return regex.split(string)


class InteractiveAgent():
    """Spinnerなどのインタラクションや再実行などを中継するクラス"""

    def __init__(self, agent):
        self.agent = agent

    # ユーザーの質問に対する回答を取得するメソッド
    def think(self, question):
        click.secho("...WANNA is thinking bash script:",  fg="blue")
        with click_spinner.spinner():
            return self.agent.think(question)

    # 回答が不正解だった場合に再度回答を求めるメソッド
    def rethink(self, result):
        click.secho("...WANNA is thinking about executed result",  fg="blue")
        with click_spinner.spinner():
            return self.agent.rethink(result)

    # 変数名の候補を提案するメソッド
    def propose_names(self):
        click.secho("...WANNA is thinking about script names",  fg="blue")
        with click_spinner.spinner():
            return self.agent.propose_names()

    # コードの概要文を提案するメソッド
    def propose_summary(self):
        click.secho("...WANNA is thinking about script description",  fg="blue")
        with click_spinner.spinner():
            return self.agent.propose_summary()

    # 生成されたコードを取得するメソッド
    def get_code(self):
        return self.agent.code

    # コメントを取得するメソッド
    def get_comment(self):
        return self.agent.display_comment


class NextAction(Enum):
    DO = "Do"
    SAVE = "Save"
    ADDITONAL_REQUEST = "Additonal Request"
    ANOTHER_QUESTION = "Another Question"
    EXIT = "Exit"


def call_whats_next():
    na = questionary.select(
        "What's next?",
        choices=[e.value for e in NextAction],
    ).ask()
    return NextAction(na)


def try_save(agent):
    names = agent.propose_names()

    selected_name = questionary.select(
        "I thought of the following names. Which one do you like?",
        choices=names,
    ).ask()
    summary = agent.propose_summary()
    click.echo(f"Saved as {selected_name}: Description:{summary}")
    config.save_script(selected_name, agent.get_code(), summary)


def conversation_cycle(agent, is_display_comment=True):
    display_comment = agent.get_comment()
    code = agent.get_code()

    WANNA_STYLE = {"bold": True, "fg": "blue", "reverse": False}

    if is_display_comment:
        if code is None:
            click.secho("AI Answer:", bold=True, underline=True, reverse=True)
            click.echo(display_comment)
            click.secho(
                "Sorry, I could not generate the proper code from your comment.", fg="red", bold=True)
            sys.exit(0)

        click.secho("WANNA:", **WANNA_STYLE)
        click.echo(display_comment)

    next_action = call_whats_next()

    if next_action == NextAction.DO:
        """実行する場合：実行結果を元に内省して間違いがあれば新しいコードを提案する"""
        tmp = create_tmp_file(code)
        args = require_args_if_need(code)
        result = execute_bash_tee(tmp, args)
        (has_fix, message) = agent.rethink(result)
        if has_fix:
            click.secho("WANNA Reflection (RETHINK):", **WANNA_STYLE)
            return conversation_cycle(agent, is_display_comment=True)
        else:
            click.secho("WANNA Reflection (SUCCESS):", **WANNA_STYLE)
            click.echo(message)
        return conversation_cycle(agent, is_display_comment=False)

    elif next_action == NextAction.SAVE:
        """保存する場合:script名を提案して、概要文を生成して保存する"""
        return try_save(agent)

    elif next_action == NextAction.ADDITONAL_REQUEST:
        """新しい指示を追加する場合:指示を元にコードを提案する"""
        text = questionary.text("What additional requests do you have?").ask()
        agent.think(text)
        return conversation_cycle(agent)

    elif next_action == NextAction.ANOTHER_QUESTION:
        """新しい指示に切り替える場合：これまでのサマリーをデフォルトに再度指示を仰ぐ"""
        return what_wanna_do(agent.propose_summary())

    elif next_action == NextAction.EXIT:
        """辞める場合:exitする"""
        sys.exit(0)


def what_wanna_do(default_question=""):
    question = questionary.text(
        'What do you want to do ?', default=default_question).ask()

    if len(question.strip()) == 0:
        click.secho("Please tell me what you wanna do", fg="red")
        sys.exit(0)
    agent = InteractiveAgent(chatter.BashAgent())
    agent.think(question)
    conversation_cycle(agent)


@ click.group()
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


@ cmd.command()
@ click.argument('command', required=False)
@ click.argument("args", nargs=-1)
def do(command=None, args=None):
    """Execute a command"""
    cmd = fill_command(command)
    args = [a for a in args] if args is not None else []
    filled_args = args if command else fill_args(cmd)

    execute_bash(config.get_command_path(cmd), filled_args)


@ cmd.command()
@ click.argument('question', required=False)
@ click.option("--model", required=False, default="gpt-3.5-turbo")
def think(model, question=None):
    chatter.gpt_model = model
    """Generate a bash script that answers the incoming request"""
    if (question is None):
        what_wanna_do()
    else:
        what_wanna_do(question)


@ cmd.command()
@ click.option('--command', is_flag=True)
def list(command):
    """List up all commands"""

    target_list = config.commands() if command else config.ideas()

    for value in target_list:
        click.echo(value)


@ cmd.command()
@ click.argument('command', required=False)
@ click.argument("args", nargs=-1)
def remove(command, args):
    """Remove selected command"""
    click.echo("Removed:" + command)
    cmd = fill_command(command)
    config.remove(cmd)


def chat_loop(agent):
    command = questionary.text("You").ask()
    if command == "exit":
        sys.exit(0)
    agent.add_user_message(command)
    with click_spinner.spinner():
        message = agent.chat()
        click.echo("Bashbot: " + message)
    chat_loop(agent)


@ cmd.command()
@ click.option("--model", required=False, default="gpt-3.5-turbo")
def chat(model):
    """Chat with bashbot"""
    chatter.gpt_model = model
    agent = chatter.BaseAgent()
    chat_loop(agent)


def main():
    cmd()


if __name__ == '__main__':
    main()
