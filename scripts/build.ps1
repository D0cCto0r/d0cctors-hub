$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name launcher `
  --manifest launcher.manifest `
  --add-data "Montserrat-VariableFont_wght.ttf;." `
  --add-data "ark.png;." `
  --add-data "default.png;." `
  --add-data "icon.png;." `
  --add-data "logo.png;." `
  --add-data "minecraft.png;." `
  --add-data "news_bg.png;." `
  launcher_qt.py
