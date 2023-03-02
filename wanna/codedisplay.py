import re
from pygments import highlight
from pygments.lexers import BashLexer
from pygments.formatters import TerminalFormatter


# BashLexerを使用してトークン化
lexer = BashLexer()
# TerminalFormatterを使用してターミナル用にフォーマット
formatter = TerminalFormatter(bg='dark')


def highlight_bash(code):
    lexer = BashLexer()
    formatter = TerminalFormatter(bg='dark')
    highlighted_code = highlight(code, lexer, formatter)
    return highlighted_code


def highlight_code_block(text):
    target = text
    code_regex = r"```bash([\s\S]*?)```"

    def replace_code(match):
        code = match.group(1)
        return "\n```bash\n" + highlight_bash(code) + "```"

    return re.sub(code_regex, replace_code, target)


def extract_code_block(text):
    code_regex = r"```bash([\s\S]*?)```"
    code_matches = re.findall(code_regex, text)

    if code_matches:
        return code_matches[0]
    else:
        return None
