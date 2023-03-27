import os
import openai
import json
import re
import sys
from subprocess_tee import run
from glom import glom
from . import system
from . import codedisplay


if "OPENAI_API_KEY" not in os.environ:
    print("ERROR: OPENAI_API_KEY environment variable not found.")
    sys.exit(1)

openai.api_key = os.environ["OPENAI_API_KEY"]

GPT_MODEL = os.environ["WANNA_GPT_MODEL"] if "WANNA_GPT_MODEL" in os.environ else "gpt-3.5-turbo"

BASH_SCRIPT_PROMPT = """
If someone asks you to perform a task, 
your job is to come up with a series of bash scripts that will perform that task.
Do not use anything but bash scripts.Take up to two arguments if necessary.
Make the script as compatible as possible.
Use the following format and try to explain your reasoning step by step:


<Example>
Q: "Copy files in a directory named "target" to a new directory at the same level as target named "myNewDirectory"."

The following actions are required
- Create a new directory
- Copy files from the first directory to the second
```bash
#!/usr/bin/env bash
mkdir myNewDirectory
cp -r target/* myNewDirectory
````

"""

LIST_UP_FILENAMES_PROMPT = """
If you were to name this bashscript, what file name would you give it?
Be sure to output 4 candidates
Please follow the example name without the ".sh" and answer with a list of four choices in json format. (ex.["good_one", "something_special", "count_records", "delete_files"])
"""

SUMMARY_PROMPT = """
Please write 1 line description of this bash script.
Condition 1: Output should be in the same language as the USER'S INPUT LANGUAGE.
Condition 2: Must be less than 150 characters.
Condition 3: The description of the operation should be simple.
Condition 4: The description should be in the form of a sentence.
"""


def extract_json_block(text):
    code_regex = r"```json([\s\S]*?)```"
    code_matches = re.findall(code_regex, text)

    if code_matches:
        return code_matches[0]
    else:
        return text


def parse_json(text):
    return json.loads(extract_json_block(text))


def extract_head_tail(text):
    if len(text) <= 200:
        return text
    else:
        head = text[:100]
        tail = text[-100:]
        return head + "..." + tail


# BaseAgentの作成
class BaseAgent():
    def __init__(self):
        self.messages = []
        self.temperature = 0.1

    def add_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

    def add_system_message(self, message):
        self.messages.append({"role": "system", "content": message})

    def add_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def chat(self):
        response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            messages=self.messages,
            temperature=self.temperature,
        )
        message = glom(response, "choices.0.message.content", default=None)
        self.add_assistant_message(message)
        return message


class BashAgent(BaseAgent):
    PRESET_MESSAGES = [
        {"role": "system", "content": BASH_SCRIPT_PROMPT},
        {"role": "system", "content": "The operating environment for bash is as follows:"+system.info()},
    ]

    def __init__(self, temperature=0.1):
        super().__init__()
        self.temperature = temperature
        self.messages = self.PRESET_MESSAGES
        self.display_comment = ""
        self.question = []
        self.names = []
        self.code = ""

    def report_result(self, result):
        self.add_system_message(f"""
        returncode : {result.returncode}
        stdout :
        {extract_head_tail(result.stdout)}
        stderr : 
        {extract_head_tail(result.stderr)}
        """)

    def think_script(self, question):
        self.question.append(question)
        self.add_user_message(question)
        message = self.chat()
        self.display_comment = codedisplay.highlight_code_block(message)
        self.code = codedisplay.extract_code_block(message)
        return message

    def think_script_names(self):
        self.add_system_message(LIST_UP_FILENAMES_PROMPT)
        message = self.chat()
        self.names = parse_json(message)
        return self.names

    def question_summary(self):
        self.add_system_message(SUMMARY_PROMPT)
        message = self.chat()
        return message

    def reset(self):
        self.messages = self.PRESET_MESSAGES
