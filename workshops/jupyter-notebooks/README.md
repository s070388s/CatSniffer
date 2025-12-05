# Fresh Install

## Install Python 3.13.3
https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe

```bash

# Optional
python -m venv venv
# Windows
 .\venv\Scripts\activate

pip install jupyterlab
pip install ipywidgets

jupyter lab
```

> Note: if a typing_extensions error occurs at the installation, use this command: pip install --upgrade typing_extensions and run `jupyter lab` again

# Run
Open the `CatSniffer-Minino.ipynb` and run all the codes.