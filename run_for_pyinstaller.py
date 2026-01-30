"""
PyInstaller entry point script.
PyInstaller cannot easily handle package entry points with src layout,
so we use this simple wrapper script.
"""

if __name__ == "__main__":
    from bank_template_processing.main import main

    main()
