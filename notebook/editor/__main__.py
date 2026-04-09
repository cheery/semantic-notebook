import sys

from notebook.editor.app import EditorApp


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m notebook.editor <file>")
        sys.exit(1)
    app = EditorApp(sys.argv[1])
    app.run()


if __name__ == "__main__":
    main()
