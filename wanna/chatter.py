import os
import openai
import json
import re
from glom import glom
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
Please follow the example without the .sh and answer with a list of four choices in json format. (ex.["aba", "bbb", "ccc", "ddd"])
"""


def talk_to_openai(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.1,
    )
    return glom(response, "choices.0.message.content", default=None)
    # return response["choices"][0]["message"]["content"]


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
    return json.loads(extract_json_block(text))


def think_script_name(question, context):
    json_list = talk_to_openai([
        {"role": "system", "content": BASH_SCRIPT_PROMPT},
        {"role": "user", "content": question},
        {"role": "assistant", "content": context},
        {"role": "user", "content": LIST_UP_FILENAMES_PROMPT},
    ])

    return parse_json(question, json_list)
