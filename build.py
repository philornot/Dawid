import PyInstaller.__main__
import os
import shutil
import sys
import time


def build():
    try:
        # Upewnij się, że folder dist jest pusty
        if os.path.exists('dist'):
            try:
                shutil.rmtree('dist')
                time.sleep(1)  # Daj systemowi czas na zwolnienie zasobów
            except Exception as e:
                print(f"Nie można usunąć folderu dist: {e}")
                return

        args = [
            'dawid.py',
            '--onefile',
            '--name=Dawid',
            '--clean',
            '--add-data=dawid_data.json;.' if os.path.exists('dawid_data.json') else None,
        ]

        args = [arg for arg in args if arg is not None]
        PyInstaller.__main__.run(args)

        # Czyszczenie
        for dir_to_remove in ['build', '__pycache__']:
            try:
                if os.path.exists(dir_to_remove):
                    shutil.rmtree(dir_to_remove)
            except Exception as e:
                print(f"Nie można usunąć {dir_to_remove}: {e}")

        try:
            if os.path.exists('Dawid.spec'):
                os.remove('Dawid.spec')
        except Exception as e:
            print(f"Nie można usunąć Dawid.spec: {e}")

        print("\nKompilacja zakończona sukcesem! Plik exe znajduje się w folderze dist/")

    except Exception as e:
        print(f"\nBłąd podczas kompilacji: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()