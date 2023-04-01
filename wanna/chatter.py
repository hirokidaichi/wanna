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

gpt_model = ""


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
    if len(text) <= 100:
        return text
    else:
        head = text[:50]
        tail = text[-50:]
        return head + "..." + tail


# BaseAgentの作成
class BaseAgent():
    def __init__(self):
        self.messages = []
        self.temperature = 0.01

    def add_user_message(self, message):
        self.messages.append({"role": "user", "content": message})

    def add_system_message(self, message):
        self.messages.append({"role": "system", "content": message})

    def add_assistant_message(self, message):
        self.messages.append({"role": "assistant", "content": message})

    def chat(self):
        response = openai.ChatCompletion.create(
            model=gpt_model,
            messages=self.messages,
            temperature=self.temperature,
        )
        message = glom(response, "choices.0.message.content", default=None)
        self.add_assistant_message(message)
        return message


def remove_non_alpha(input_string):
    return re.sub(r'[^a-zA-Z]', '', input_string)


def guess_language(question):
    agent = BaseAgent()

    agent.add_system_message(
        f"""
        guess the language of following text:
        (e.g ja,en,fr,es,zh)

        <Example>
        input : こんにちは
        output: ja

        input : hello
        output : en
        </Example>

        input: {question}
        output:
        """
    )
    message = agent.chat()
    return remove_non_alpha(message)


class BashAgent(BaseAgent):

    def __init__(self, temperature=0.01):
        super().__init__()
        self.temperature = temperature
        self.language = None
        self.messages = []
        self.display_comment = ""
        self.question = []
        self.names = []
        self.code = ""

    def user_language_prompt(self):
        return f"Output in the following language:{self.language}"

    def bash_script_prompt(self):
        return f"""
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
        </Example>

        {self.user_language_prompt}
        """

    def listup_filename_prompt(self):
        return """
        If you were to name this bashscript, what file name would you give it?
        Be sure to output 4 candidates
        Please follow the example name without the ".sh" and answer with a list of four choices in json format.

        ```json
        {
            "filename_candidates": [
                "top_mem_processes",
                "high_mem_procs",
                "mem_usage_top5",
                "processes_by_mem"
            ] // should be 4 candicates
        }
        ```
        """

    def reflection_prompt(self):
        return f"""
        実行結果を見て問題があれば、コードの修正を提案せよ。問題なく動作していれば、問題なしと回答せよ。
        """

    def summary_prompt(self):
        return f"""
        Please write 1 line description of this bash script.
        Condition : Must be less than 150 characters.
        Condition : The description of the operation should be simple.
        Condition : The description should be in the form of a sentence.
        {self.user_language_prompt()}
        """

    def rethink(self, result, retry=0):
        if retry >= 3:
            print("Overlimit retry count")
            sys.exit(1)

        self.add_system_message(f"""
        The execution result of your proposed script is as follows Based on the results:

        # RESULT
        returncode : {result.returncode}
        stdout :
        {extract_head_tail(result.stdout)}
        stderr : 
        {extract_head_tail(result.stderr)}

        If there are any problems with the execution results, suggest modifications to the code. If it works fine, reply that there is no problem.
        {self.user_language_prompt()}
        """)
        message = self.chat()
        code = codedisplay.extract_code_block(message)
        if code is not None:
            self.display_comment = codedisplay.highlight_code_block(message)
            self.code = codedisplay.extract_code_block(message)
            return (True, None)
        else:
            return (False, message)

    def think(self, question):
        if self.language is None:
            self.language = guess_language(question)
            self.add_system_message(
                "The operating environment for bash is as follows:"+system.info())
            self.add_system_message(self.bash_script_prompt())

        self.question.append(question)
        self.add_user_message(question)
        message = self.chat()
        self.display_comment = codedisplay.highlight_code_block(message)
        self.code = codedisplay.extract_code_block(message)
        return message

    def propose_names(self, retry=0):
        if retry >= 3:
            print("Overlimit retry count")
            sys.exit(1)
        self.add_system_message(self.listup_filename_prompt())
        message = self.chat()
        try:
            json = parse_json(message)
            self.names = json["filename_candidates"]
            if len(self.names) != 4:
                print("json length error")
                raise Exception("json error")
        except:
            self.messages = self.messages[:-2]
            print(f"retry{retry}")
            print(f"{message}")
            return self.propose_names(retry + 1)

        return self.names

    def propose_summary(self):
        self.add_system_message(self.summary_prompt())
        message = self.chat()
        return message

    def reset(self):
        self.__init__()
