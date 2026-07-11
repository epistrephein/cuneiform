# Cuneiform

Turns a Markdown file into a single, self-contained HTML page with GitHub
Markdown styling, a retractable sidebar Table of Contents, light/dark toggle
and zero external dependencies.

## Requirements

Only [pandoc](https://pandoc.org/) v3+ is required. It must be installed and
available on the system's PATH.

On macOS, simply install it with Homebrew:

```sh
brew install pandoc
```

## Usage

```sh
python3 generate.py INPUT.md [-o OUTPUT.html] [-t "Title"]
```

If output is omitted, the HTML will be written to `<INPUT>.html` in the same
folder as the input file.  
If the title is omitted, the first heading in the Markdown file will be used.

To see an example, run:

```sh
python3 generate.py example.md && open example.html
```

## License

This project is released as open source under the terms of the [MIT License](LICENSE.md).
