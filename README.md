<!-- i18n: language-switcher -->
[English](README.en.md) | [日本語](README.md)

# jbacon

Maven プロジェクト用の bacon 風バックグラウンドコードチェッカー。
エディタの隣（ターミナル / VSCode の統合ターミナル）で常駐させておくと、
ファイルを保存するたびに自動でビルドチェックを走らせ、
エラーと警告をソート済みでリアルタイム表示する。

```
 jbacon 0.2.0  job:check  mvn  fail  2 errors, 0 warnings
E src/main/java/com/example/Calc.java:9:21
   ';' expected
E Failed to execute goal
  org.apache.maven.plugins:maven-compiler-plugin:3.13.0:compile (default-compile) on
  project jbacon-demo: Compilation failure

 BUILD FAILURE in 3.5s
 c:check  t:test  v:verify  p:package  r:rerun o:offline s:summary w:raw h:help q:quit
```

（↑ 実際のレンダリング出力。`tests/screenshot.txt` 参照）

## 特徴（bacon から持ってきた設計）

- **常駐・保存で自動再ビルド**: src/ と pom.xml を監視。マルチモジュールは3階層まで自動検出
- **エラーが警告より先**: ロケーション付きエラー → 一般エラー → 警告の順にソート。
  先頭に一番重要な情報が来るのでスクロール不要
- **1キーでジョブ切替**: `c` compile / `t` test / `v` verify / `p` package。
  bacon の `t` / `c` / `d` と同じ操作感
- **前回結果を保持したまま再計算**: ビルド中も直前のエラー一覧が消えない
- **重複除去**: Maven がコンパイルエラーを2回出す問題（本文+末尾サマリ）を吸収
- **ビルドの即時キャンセル**: ビルド中に再保存したら古いビルドを kill して最新だけ走らせる
  （watchexec -r 相当）
- **軽量**: Python 標準ライブラリのみ・依存ゼロ・1ファイル。
  監視は mtime ポーリング（target/ .git/ は除外）
- **mvnd 自動検出**: `mvnd` > `./mvnw` > `mvn` の順で自動選択。mvnd があればJVM常駐で高速
- **`--once` モード**: CI やコミット前チェック用。TUIなしで1回実行して exit code を返す

## 必要なもの

- `mvn` / `mvnd` / `./mvnw` のどれか
- Linux / macOS のターミナル（Windows は WSL で）
- native release binary を使う場合、Python は不要
- ソースを直接コピーして使う場合、Python 3.11+（tomllib 使用。設定ファイルを使わなければ 3.8+ でも動く）

## インストール

```bash
# いちばん簡単: native 単体バイナリを ~/.local/bin/jbacon に入れる
curl -fsSL https://raw.githubusercontent.com/hjosugi/jacon/main/install.sh | sh

# ソース checkout から入れる場合: fish (CachyOS など)
fish install.fish

# または手動で
cp jbacon ~/.local/bin/ && chmod +x ~/.local/bin/jbacon
```

native release は Linux x86_64 / Linux aarch64 / macOS x86_64 / macOS arm64 を用意する。
特定バージョンを入れる場合は `JBACON_VERSION=v0.2.0`、インストール先を変える場合は
`JBACON_INSTALL_DIR=/path/to/bin` を指定する。

高速化したい場合は mvnd を推奨:

```bash
sdk install mvnd          # SDKMAN
# Arch系: paru -Ss mvnd で AUR を確認
```

## 使い方

```bash
cd your-maven-project
jbacon                    # デフォルトジョブ (check = test-compile) で常駐開始
jbacon --job test         # テスト監視で開始
jbacon --once             # 1回だけ実行してレポート出力・終了 (CI用)
jbacon --mvn mvnd         # maven 実行体を明示指定
jbacon --offline          # -o (オフライン) 付きで実行
```

### キー操作

| キー | 動作 |
|---|---|
| `c` | check ジョブ (test-compile) |
| `t` | test ジョブ |
| `v` | verify ジョブ |
| `p` | package ジョブ (-DskipTests) |
| `r` | 手動で再実行 |
| `o` | オフラインモード切替 (-o) |
| `s` | サマリ表示切替（1診断=1行） |
| `w` | Maven 生ログ表示切替 |
| `h` | ヘルプ / ジョブ一覧 |
| `j` `k` / 矢印 | スクロール |
| `g` `G` | 先頭 / 末尾へ |
| `q` | 終了 |

## 設定 (jbacon.toml)

プロジェクトルートに `jbacon.toml` を置くとジョブの追加・上書きができる。
同梱の `jbacon.toml` にコメント付きサンプルがある。よく使う例:

```toml
extra_args = ["-T1C"]        # 全ビルドに追加する引数

[jobs.focus]                 # 1テストクラスだけ監視
key = "f"
goals = ["test", "-Dtest=CalcTest"]

[jobs.errorprone]            # Error Prone プロファイルで静的解析
key = "e"
goals = ["clean", "test-compile", "-Perrorprone"]
```

## VSCode 統合

`vscode/tasks.json` をプロジェクトの `.vscode/tasks.json` にコピー。
`Ctrl+Shift+P` → Tasks: Run Task → `jbacon: watch` で専用パネルに常駐する
（`runOn: folderOpen` を有効にしているのでフォルダを開くと自動起動）。

推奨構成（3層）:

1. **エディタ内リアルタイム**: Extension Pack for Java + SonarQube for IDE。
   1ファイル単位の即時エラーはこちらが担当（IntelliJ 相当）
2. **jbacon 常駐**: モジュール全体が本当にコンパイル/テストを通るかを担保。
   エディタの増分解析では拾えない全体整合性はこちら
3. **Error Prone / SpotBugs**: jbacon のジョブに乗せて必要な時だけ回す

## 軽さの設計メモ

- 保存ごとのコストは「Maven の実行時間」だけ。jbacon 自身の監視は
  mtime ポーリング（デフォルト 0.7 秒間隔、target/ 除外）で CPU ほぼゼロ
- mvnd を入れると JVM・プラグインクラスローダ・JIT コードがビルド間で
  キャッシュされるので、`test-compile` なら体感が大きく変わる
- デフォルトジョブが `test-compile`（package や install を回さない）なのも軽さのため。
  「コンパイルが通るか」の確認にはこれで十分

## 動作確認

同梱のデモプロジェクトで試せる（初回は依存ダウンロードあり）:

```bash
cd demo
../jbacon
# 別の窓で src/main/java/com/example/Calc.java のセミコロンを消して保存
# → 即座にエラーが先頭に表示される
```

テスト:

```bash
python3 tests/parser_test.py   # パーサ単体テスト
python3 tests/tui_test.py      # pty経由のTUI結合テスト (要 mvn + JDK)
```

parser test は CI で実行する。TUI 結合テストは `mvn` + JDK が入ったローカル環境で実行する。

## リリース

tag を push すると GitHub Actions が PyInstaller で native release asset を作成する。

```bash
git tag v0.2.0
git push origin main v0.2.0
```

## 制限

- 診断のパースは Maven の `[ERROR]` / `[WARNING]` 形式（-B, color=never）に依存。
  ロケーション付きで拾えるのは `.java` / `.kt` / `.kts` / `.groovy`。
  Gradle は非対応（Gradle は `--continuous` が組み込みであるのでそちらを）
- ファイル監視は inotify ではなくポーリング。巨大 monorepo（数万ファイル）では
  `poll_interval` を上げるか `watch` で範囲を絞ると良い

## License

0BSD. You can use, copy, modify, and distribute this project for almost any purpose.
