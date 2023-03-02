
import toml
import json
from enum import Enum
import re
import openai
import sys
from langchain.chains import LLMBashChain
from langchain.llms import OpenAI
import questionary
from dotenv import load_dotenv
import click
import os
from . import codedisplay
# import codedisplay
openai.api_key = os.environ["OPENAI_API_KEY"]


BASH_SCRIPT_PROMPT = """
If someone asks you to perform a task, your job is to come up with a series of bash scripts that will perform that task.
Do not use anything but bash scripts.
Use the following format and try to explain your reasoning step by step:.

Q: "Copy files in a directory named "target" to a new directory at the same level as target named "myNewDirectory"."

The following actions are required
- Create a nepow directory
- Copy files from the first directory to the second
```bash
#!/usr/bin/env bash
mkdir myNewDirectory
cp -r target/* myNewDirectory
````

"""

LIST_UP_FILENAMES_PROMPT = """
If you were to name this bashscript, what file name would you give it?
Please follow the example without the .sh and answer with a list of four choices in json format. (ex.["aba", "bbb", "ccc", "ddd"])
"""

# ホームディレクトリのパスを取得する
home_dir = os.path.expanduser("~")
# `.wanna`ディレクトリのパスを作成する
wanna_dir = os.path.join(home_dir, ".wanna")

# `.wanna`ディレクトリが存在しない場合は作成する
if not os.path.exists(wanna_dir):
    os.mkdir(wanna_dir)


def read_toml_file(file_path):
    with open(file_path, 'r') as f:
        data = toml.load(f)
    return data


def write_toml_file(file_path, data):
    with open(file_path, 'w') as f:
        toml.dump(data, f)


toml_file_name = os.path.join(wanna_dir, "config.toml")
if not os.path.exists(toml_file_name):
    write_toml_file(toml_file_name, {})

config = read_toml_file(toml_file_name)


def add_to_config(name, code, question):
    config[name] = {"question": question, "code": code}
    write_toml_file(toml_file_name, config)


def talk_to_openai(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5,
    )
    return response["choices"][0]["message"]["content"]


def guess_bash_command(question):
    return talk_to_openai([
        {"role": "system", "content": BASH_SCRIPT_PROMPT},
        {"role": "user", "content": question}
    ])


def extract_json_block(text):
    code_regex = r"```json([\s\S]*?)```"
    code_matches = re.findall(code_regex, text)

    if code_matches:
        return code_matches[0]
    else:
        return text


def parse_json(question, text):
    try:
        return json.loads(extract_json_block(text))
    except:
        print(text)
        questionary.confirm(
            "Hmmm, I can't think of a good name, can I think again?").ask()
        return think_script_name(question, text)


def think_script_name(question, context):
    json_list = talk_to_openai([
        {"role": "system", "content": BASH_SCRIPT_PROMPT},
        {"role": "user", "content": question},
        {"role": "assistant", "content": context},
        {"role": "user", "content": LIST_UP_FILENAMES_PROMPT},
    ])

    return parse_json(question, json_list)


class NextAction(Enum):
    DO = "Do"
    SAVE = "Save"
    ANOTHER_QUESTION = "Another Question"
    EXIT = "Exit"


def call_whats_next():
    na = questionary.select(
        "What's next?",
        choices=[e.value for e in NextAction],
    ).ask()
    return NextAction(na)


def save_script(name, code, question):
    # configにもデータを保存する
    add_to_config(name, code, question)

    with open(os.path.join(wanna_dir, name), "w") as f:
        f.write(code)

    os.chmod(os.path.join(wanna_dir, name), 0o755)


def try_save(question, comment, code):
    name_cands = think_script_name(question, comment)
    selected_name = questionary.select(
        "I thought of the following names. Which one do you like?",
        choices=name_cands,
    ).ask()
    save_script(selected_name, code, question)


def after_comment(question, comment):
    display_comment = codedisplay.highlight_code_block(comment)
    code = codedisplay.extract_code_block(comment)
    click.echo("")
    click.echo(click.style("AI assistant's thougt:",
               bold=True, underline=True, reverse=True))
    click.echo("\n")
    click.echo(display_comment)
    click.echo("\n")

    next_action = call_whats_next()
    if next_action == NextAction.DO:
        os.system(code)
        if questionary.confirm("save this script?").ask():
            try_save(question, comment, code)
    elif next_action == NextAction.SAVE:
        try_save(question, comment, code)
    elif next_action == NextAction.ANOTHER_QUESTION:
        what_wanna_do(question)
    elif next_action == NextAction.EXIT:
        sys.exit(0)


def what_wanna_do(default_question="Recursively explore all .py files under the current directory and sum their line counts."):
    # 　やりたいことを聞く
    question = questionary.text(
        'What do you want to do ?', default=default_question).ask()
    #  bash script と解説を取得する。
    comment = guess_bash_command(question)
    after_comment(question, comment)


@click.group()
def cmd():
    pass


@cmd.command()
@click.argument('command', required=False)
def do(command=None):
    if command is not None:
        os.system(config[command]["code"])
    else:
        ideas = [
            f"{key} ~ {config[key]['question']}" for key in sorted(config)]
        command_and_question = questionary.autocomplete(
            'Choose command',
            choices=ideas).ask()
        got_command = command_and_question.split("~")[0].strip()
        os.system(config[got_command]["code"])


@cmd.command()
@click.argument('question', required=False)
def think(question=None):
    if (question is None):
        what_wanna_do()
    else:
        what_wanna_do(question)


@cmd.command()
@click.option('--command-only', '-c')
def list(command_only):
    print(command_only)


def main():
    cmd()


if __name__ == '__main__':
    main()
