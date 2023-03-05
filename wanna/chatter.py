import os
import openai
import json
import re
import sys
from glom import glom
from . import system
from . import codedisplay
if "OPENAI_API_KEY" not in os.environ:
    print("ERROR: OPENAI_API_KEY environment variable not found.")
    sys.exit(1)

openai.api_key = os.environ["OPENAI_API_KEY"]


BASH_SCRIPT_PROMPT = """
If someone asks you to perform a task, your job is to come up with a series of bash scripts that will perform that task.
Do not use anything but bash scripts.Take up to two arguments if necessary.
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
Be sure to output 4 candidates
Please follow the example name without the ".sh" and answer with a list of four choices in json format. (ex.["good_one", "something_special", "count_records", "delete_files"])
"""

SUMMARY_PROMPT = """
Please write a description of this bash script.
Condition 1: Must be less than 100 characters
Condition 2: Output should be in the same language as the user's input language.
Condition 3: The description of the operation should be simple.
Condition 4: It is obvious that it is a bash script, so it is not mentioned.
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


class BashAgent():
    PRESET_MESSAGES = [
        {"role": "system", "content": BASH_SCRIPT_PROMPT},
        {"role": "system", "content": "The operating environment for bash is as follows:"+system.info()},
    ]

    def __init__(self, temperature=0.1):
        self.temperature = temperature
        self.messages = self.PRESET_MESSAGES
        self.display_comment = ""
        self.question = []
        self.names = []
        self.code = ""

    def add_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

    def add_system_message(self, message):
        self.messages.append({"role": "system", "content": message})

    def add_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def chat(self):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.messages,
            temperature=self.temperature,
        )
        message = glom(response, "choices.0.message.content", default=None)
        self.add_assistant_message(message)
        return message

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
        if len(self.question) == 0:
            return ""
        if len(self.question) == 1:
            return self.question[0]

        self.add_system_message(SUMMARY_PROMPT)
        self.add_system_message("/".join(self.question))
        message = self.chat()
        return message

    def reset(self):
        self.messages = self.PRESET_MESSAGES
