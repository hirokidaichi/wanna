# wanna
Shell command launcher in natural language using ChatGPT

![wanna](https://user-images.githubusercontent.com/95184/222627802-1df02ee6-e07b-47dc-8fe0-0787a1e63097.gif)

## synopsis
The `wanna` command is a natural language shell command launcher using ChatGPT. It can generate, execute, name, and manage shell commands by natural language.

It is very convenient because you can easily do many things on the command line. However, remembering many commands and option combinations can be difficult even for experienced programmers, and often requires a Google search or the `man` command to remember and execute.

For example, if you want to do a task like **"recursively find all .py files under this directory and output the total number of lines in them "**, it is difficult to remember how to combine commands like `find`, `xargs`, and `wc` in a single shot. It is difficult to remember how to combine commands such as `find`, `xargs`, and `wc` in one shot.

### wanna think 

The `wanna think` command is used in such cases.

```bash
$ wanna think "Recursively finds all .py files under this directory and prints the sum of their line counts"
```
the AI assistant will automatically generate the following bash script: 

```bash
#! /usr/bin/env bash
find . -name "*.py" -exec cat {} + | wc -l
```
You just look at it and decide to run it or not.

```
$ ? What's next? (Use arrow keys)
   Do
   Save
   Another Question
   Exit
````
In response to your request, AI will generate a script and explain it.
If you choose ``Do``, it will actually run the proposed script and display the results.
Once you have run it and verified that it works, you can save it.
```
$ ? I thought of the following names. which one do you like? (Use arrow keys)
   count_py_lines
   py_line_counter
   recursive_py_counter
   py_line_sum
````
[Phil Karlton once said](https://martinfowler.com/bliki/TwoHardThings.html), "The hardest part of computer science is naming. "
This AI also suggests just the right name for the scripts it generates. All you have to do is choose a name that sounds good as a code reviewer.


### wanna do
The `wanna do` command allows you to execute a previously saved command.
Simply type `wanna do` to incrementally select and execute a previously saved command.
```zsh
$ wanna do
```
![wanna-do](https://user-images.githubusercontent.com/95184/222663648-50325d6a-1e5e-451a-a90e-9aff6a914fc1.gif)


```
$ wanna do random_passwords
```
You can also run the command by typing its name directly, as in: ## wanna list

## wanna list 
List recorded scripts.
```
$ wanna list 
count_py_lines :recursively find all .py files under this directory and print the total number of lines in them
top_memory_usage :Output the top 10 processes with the highest memory usage.
random_passwords :Generate 10 random passwords.
````

With this, you can, for example, do this.
```
$ wanna list | peco | xargs wanna do
```
![wanna-list-peco](https://user-images.githubusercontent.com/95184/222663840-67983f47-b477-4168-81db-6abae9caf311.gif)


## Installation
Installation is easy using pip, and works with python 3.10 or higher.
```bash
pip install wanna
```
Also, you will need to get a token with your own account to use OEPNAI_API_KEY.
```bash
export OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```
