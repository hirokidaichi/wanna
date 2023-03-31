# wanna
ChatGPTを用いた自然言語によるシェルコマンドランチャー

![wanna](https://user-images.githubusercontent.com/95184/222627802-1df02ee6-e07b-47dc-8fe0-0787a1e63097.gif)

## 概要
`wanna`コマンドは、ChatGPTを用いた自然言語によるシェルコマンドランチャーです。自然言語によって、shell commandを生成して実行し、名付けし、管理できます。

コマンドライン上での操作は簡単に多くのことを行うことができるため、非常に便利です。しかし、多くのコマンドやオプションの組み合わせを覚えておくのは熟練したプログラマでもむずかしく、Google検索や`man`コマンドなどを駆使して思い出しながら実行することも多くあるでしょう。

たとえば、**「このディレクトリの配下にあるすべての.pyファイルを再帰的に発見して、それらの行数の合計を出力する」** といったタスクを行おうとするとき、`find`や`xargs`、 `wc`などのコマンドをどのように組み合わせたら良いのかを一発で思い出すのは中々難しいです。

### wanna think 

このようなときに`wanna think`コマンドを使います。

```bash
$ wanna think このディレクトリの配下にあるすべての.pyファイルを再帰的に発見して、それらの行数の合計を出力する
```
と打てば、AIアシスタントが自動的に次のようなbash scriptを生成します。

```bash
#!/usr/bin/env bash
find . -name "*.py" -exec cat {} + | wc -l
```
あなたはただ、それをみて、実行するかしないかを決めれば良いだけです。
```
? What's next? (Use arrow keys)
 » Do
   Save
   Additonal Request
   Another Question
   Exit
```
あなたの依頼に対して、AIはスクリプトを生成し、その解説をします。
`Do`を選べば、提案されたスクリプトを実際に実行してその結果を表示します。
実行後に問題なく動作することを確認したら、保存をすることができます。
```
? I thought of the following names. Which one do you like? (Use arrow keys)
 » count_py_lines
   py_line_counter
   recursive_py_counter
   py_line_sum
```
そういえば、「コンピュータサイエンスで最も難しいことは"命名"である」とフィルカールトンも言っていました。
このAIは、生成したスクリプトに丁度良い名前も提案してくれます。あなたは、コードレビューアとして良さそうな名前を選ぶだけです。

### wanna do
`wanna do`コマンドを使えば、過去に保存したコマンドを実行することができます。
ただ単に`wanna do`と入力すればインクリメンタルに保存済のコマンドを選び、実行できます。
```zsh
$ wanna do
```
![wanna-do](https://user-images.githubusercontent.com/95184/222663648-50325d6a-1e5e-451a-a90e-9aff6a914fc1.gif)


```
$ wanna do random_passwords
```
のようにコマンド名を直接打って実行することもできます。

## wanna list 
記録済のスクリプトをリストアップします。
```
$ wanna list 
count_py_lines      :このディレクトリの配下にあるすべての.pyファイルを再帰的に発見して、それらの行数の合計を出力する
top_memory_usage    :メモリ使用量の多いプロセスを上位10個出力する
random_passwords    :ランダムに10個のパスワードを生成する
```

これを用いると、たとえば、こんなことができます。
```
$ wanna list | peco | xargs wanna do
```
![wanna-list-peco](https://user-images.githubusercontent.com/95184/222663840-67983f47-b477-4168-81db-6abae9caf311.gif)


## インストール
インストールは、pipを用いて簡単にできます。python3.10以上の環境で動作します。
```bash
pip install wanna
```
また、OEPNAI_API_KEYを使うため、ご自身のアカウントでtokenを取得してください。
```bash
export OPENAI_API_KEY = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```
