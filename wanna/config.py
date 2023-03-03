import os
import toml

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


def save_script(name, code, question):
    # configにもデータを保存する
    add_to_config(name, code, question)

    with open(os.path.join(wanna_dir, name), "w") as f:
        f.write(code)

    os.chmod(os.path.join(wanna_dir, name), 0o755)


def ideas():
    return [
        f"{key} ~ {config[key]['question']}" for key in sorted(config)
    ]


def commands():
    return [
        key for key in sorted(config)
    ]


def exists(command):
    return command in config


def get_code(command):
    return config[command]["code"]


def get_command_path(command):
    return os.path.join(wanna_dir, command)
