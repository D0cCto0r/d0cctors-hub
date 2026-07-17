APP_VERSION = "0.3"
APP_STAGE = "Beta"
APP_BUILD = "2026.5"
APP_FULL_VERSION = f"{APP_VERSION}-{APP_BUILD}"

import sys
import os
import webbrowser
import winreg

import ctypes

if not ctypes.windll.shell32.IsUserAnAdmin():
    script_path = os.path.abspath(sys.argv[0])
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        f'"{script_path}"',
        os.path.dirname(script_path),
        1
    )
    sys.exit()

from PySide6.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QLabel
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFrame, QComboBox, QFileDialog, QScrollArea,
    QStackedLayout, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont
from config_manager import ConfigManager
import requests
import minecraft_launcher_lib
import psutil
import subprocess
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
    
from PySide6.QtGui import QColor


class ServerCard(QFrame):
    def __init__(self, title, description, font_family, pixmap, installed=False, click_callback=None, large=False):
        super().__init__()

        self.title = title
        self.click_callback = click_callback

        if large:
            self.setFixedSize(660, 140)
        else:
            self.setFixedSize(200, 180)

        self.setStyleSheet("""
            QFrame {
                background-color: #1a1a22;
                border-radius: 12px;
            }
        """)

        # ===== LAYOUT =====
        if large:
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)

        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # ===== IMAGEN =====
        image_label = QLabel()

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                120,
                120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            image_label.setPixmap(scaled)
        else:
            fallback = self.parent().get_remote_asset("default.png").scaled(
                120,
                120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            image_label.setPixmap(fallback)

        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)

        # ===== TITULO =====
        title_label = QLabel(title)
        title_font = QFont(font_family, 16)
        title_font.setWeight(QFont.Weight.DemiBold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        if large:
            title_label.setAlignment(Qt.AlignLeft)
        else:
            title_label.setAlignment(Qt.AlignCenter)

        # ===== DESCRIPCIÓN (solo en cards grandes) =====
        if large:

            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #aaaaaa;")
            desc_label.setWordWrap(True)
            desc_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
            desc_label.setContentsMargins(0, 0, 0, 0)


            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            text_layout.setContentsMargins(0, 0, 0, 0)

            text_layout.addWidget(title_label, alignment=Qt.AlignTop)
            text_layout.addWidget(desc_label, alignment=Qt.AlignTop)
            text_layout.addStretch()

            layout.addLayout(text_layout)
            layout.addStretch()

        else:

            layout.addWidget(title_label)
            layout.addStretch()

        # ===== BOTÓN =====
        self.button = QPushButton()
        self.button.setFixedSize(150, 30)
        self.button.setCursor(Qt.PointingHandCursor)
        
        # ===== BOTÓN REINSTALAR MODS (solo Ark) =====
        self.reset_btn = QPushButton("Reinstalar Mods")
        self.reset_btn.setFixedSize(150, 25)
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a35;
                color: white;
                border-radius: 10px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #3a3a45;
            }
        """)

        self.reset_btn.hide()  # oculto por defecto

        if installed:
            self.button.setText("Jugar")
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: #ff2d55;
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #ff4d6d;
                }
            """)
        else:
            self.button.setText("Instalar")
            self.button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: black;
                    border-radius: 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #dddddd;
                }
            """)

        # ===== GLOW =====
        self.glow = QGraphicsDropShadowEffect()
        self.glow.setBlurRadius(25)
        self.glow.setOffset(0)
        self.glow.setColor(QColor(255, 255, 255, 120))
        self.button.setGraphicsEffect(self.glow)

        # ===== HOVER =====
        self.button.enterEvent = self.enter_glow
        self.button.leaveEvent = self.leave_glow

        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.addWidget(self.reset_btn, alignment=Qt.AlignCenter)
        self.reset_btn.clicked.connect(self.reset_mods)

        # ===== CLICK CALLBACK =====
        if self.click_callback:
            self.button.clicked.connect(lambda: self.click_callback(self.title))
            
        # Mostrar botón solo si es Ark
        if self.title.lower() == "ark survival":
            self.reset_btn.show()

    def enter_glow(self, event):
        self.glow.setColor(QColor(255, 255, 255, 255))
        self.glow.setBlurRadius(40)

    def leave_glow(self, event):
        self.glow.setColor(QColor(255, 255, 255, 120))
        self.glow.setBlurRadius(25)
        
    def reset_mods(self):
        if self.click_callback:
            self.click_callback("__RESET_MODS__")


from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer

from PySide6.QtGui import QPainter, QRadialGradient, QBrush

class GlowLogo(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.setPixmap(pixmap)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(pixmap.size())
        self.glow_radius = 65  # tamaño del aura
        self.glow_strength = 10  # intensidad

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Centro del widget
        center = self.rect().center()

        # Gradiente radial
        gradient = QRadialGradient(center, self.glow_radius)
        gradient.setColorAt(0.0, QColor(255, 255, 255, self.glow_strength))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 80))
        gradient.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, self.glow_radius, self.glow_radius)

        # Dibuja el logo encima
        super().paintEvent(event)

from PySide6.QtGui import QFontDatabase
from PySide6.QtGui import QPainter, QPainterPath

class RoundedImage(QLabel):
    def __init__(self, pixmap, radius=12):
        super().__init__()
        self.pixmap_original = pixmap
        self.radius = radius

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(self.rect(), self.radius, self.radius)
        painter.setClipPath(path)

        if not self.pixmap_original.isNull():
            scaled = self.pixmap_original.scaled(
                self.width(),
                self.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
            
            
from PySide6.QtCore import QThread, Signal
import zipfile
import os
import requests

class InstallWorker(QThread):
    progress = Signal(int)
    finished = Signal()
    error = Signal(str)

    def __init__(self, url, instance_folder, version):
        super().__init__()
        self.url = url
        self.instance_folder = instance_folder
        self.version = version

    def run(self):
        try:
            os.makedirs(self.instance_folder, exist_ok=True)
            zip_path = os.path.join(self.instance_folder, "modpack.zip")

            response = requests.get(self.url, stream=True)
            print("Status code:", response.status_code)
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(zip_path, "wb") as f:
                print("Comenzando descarga...")
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = int(downloaded * 100 / total_size)
                        self.progress.emit(percent)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.instance_folder)

            os.remove(zip_path)

            with open(os.path.join(self.instance_folder, "version.txt"), "w") as v:
                v.write(self.version)
                
            import time
            time.sleep(2)

            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))          
            
from PySide6.QtCore import QThread, Signal

class GameWatcher(QThread):
    finished_signal = Signal(str)

    def __init__(self, process_name, server_name):
        super().__init__()
        self.process_name = process_name
        self.server_name = server_name

    def run(self):
        import time

        # Esperar a que el proceso aparezca
        while True:
            found = False
            for p in psutil.process_iter():
                try:
                    if p.name() == self.process_name:
                        found = True
                        break
                except:
                    continue

            if found:
                break

            time.sleep(1)

        # Esperar a que se cierre
        while True:
            running = False
            for p in psutil.process_iter():
                try:
                    if p.name() == self.process_name:
                        running = True
                        break
                except:
                    continue

            if not running:
                break

            time.sleep(2)

        self.finished_signal.emit(self.server_name)      
            
class Launcher(QMainWindow):
    
    def check_for_updates(self):
        try:
            version_url = "https://raw.githubusercontent.com/D0cCto0r/d0cctors-hub/main/remote/version.txt"
            response = requests.get(version_url, timeout=5)

            if response.status_code != 200:
                print("No se pudo acceder a version.txt")
                return

            lines = response.text.strip().splitlines()

            if len(lines) < 2:
                print("version.txt mal formado")
                return

            remote_version = lines[0].strip()
            download_url = lines[1].strip()

            print("Versión remota:", remote_version)
            print("Versión local:", APP_FULL_VERSION)

            def parse_version(version):
                app_version, build = version.split("-", 1)
                app_parts = tuple(int(part) for part in app_version.split("."))
                build_parts = tuple(int(part) for part in build.split("."))
                return app_parts + build_parts

            if parse_version(remote_version) > parse_version(APP_FULL_VERSION):
                self.ask_update(remote_version, download_url)

        except Exception as e:
            print("No se pudo verificar actualización:", e)
        

    def ask_update(self, new_version, download_url):
        dialog = QDialog(self)
        dialog.setWindowTitle("Actualización disponible")
        dialog.setFixedSize(420, 180)

        layout = QVBoxLayout(dialog)

        label = QLabel(
            f"Nueva versión disponible\n\n"
            f"Actual: {APP_FULL_VERSION}\n"
            f"Nueva: {new_version}\n\n"
            f"¿Actualizar ahora?"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)

        layout.addWidget(label)

        buttons_layout = QHBoxLayout()

        yes_btn = QPushButton("Actualizar")
        no_btn = QPushButton("Más tarde")

        buttons_layout.addWidget(yes_btn)
        buttons_layout.addWidget(no_btn)

        layout.addLayout(buttons_layout)

        def start_update():
            yes_btn.setEnabled(False)
            yes_btn.setText("Descargando...")
            self.download_update(dialog, download_url)

        yes_btn.clicked.connect(start_update)
        no_btn.clicked.connect(dialog.close)

        dialog.exec()
        
    def download_update(self, dialog, exe_url):
        print("🔥 download_update llamado")
        print("URL:", exe_url)

        try:
            dialog.setWindowTitle("Actualizando...")
            layout = dialog.layout()
            layout.itemAt(0).widget().setText(
                "Descargando actualización...\nPor favor esperá."
            )
            QApplication.processEvents()

            response = requests.get(exe_url, stream=True, allow_redirects=True)

            if response.status_code != 200:
                print("No se pudo descargar el exe.")
                return

            current_exe = sys.executable
            base_dir = os.path.dirname(current_exe)

            new_exe_path = os.path.join(base_dir, "launcher_new.exe")

            exe_name = os.path.basename(current_exe)

            # ===============================
            # GUARDAR NUEVO EXE
            # ===============================
            with open(new_exe_path, "wb") as f:
                for chunk in response.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)

            dialog.close()

            # ===============================
            # MENSAJE AL USUARIO
            # ===============================
            finished_dialog = QDialog(self)
            finished_dialog.setWindowTitle("Actualización lista")
            finished_dialog.setFixedSize(420, 150)

            layout = QVBoxLayout(finished_dialog)

            label = QLabel(
                "La actualización fue descargada.\n\n"
                "El launcher se cerrará para completar la instalación.\n"
                "Cierra esta ventana y espera."
            )

            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)

            layout.addWidget(label)

            finished_dialog.exec()

            # ===============================
            # EJECUTAR UPDATER
            # ===============================
            print("Ejecutando updater...")

            updater = os.path.join(base_dir, "updater.exe")

            subprocess.Popen([
                updater,
                current_exe,
                new_exe_path
            ])

            os._exit(0)

        except Exception as e:
            print("Error descargando actualización:", e)

    def detect_steam_path(self):
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Valve\Steam"
            )
            steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
            return steam_path
        except:
            return None

    def is_steam_game_installed(self, appid):
        steam_path = self.detect_steam_path()
        if not steam_path:
            return False

        common_path = os.path.join(steam_path, "steamapps", "common")

        ark_path = os.path.join(common_path, "ARK")

        return os.path.exists(ark_path)

    def get_remote_asset(self, filename):
        BASE_ASSET_URL = "https://raw.githubusercontent.com/D0cCto0r/d0cctors-hub/main/remote/assets/"

        try:
            url = BASE_ASSET_URL + filename
            response = requests.get(url)

            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap

        except Exception as e:
            print("Error cargando asset remoto:", e)

        return QPixmap()

    def check_java_installed(self):
        import subprocess
        try:
            result = subprocess.run(
                ["java", "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
            
    def is_forge_installed(self, mc_version, forge_version):
        versions_path = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            ".minecraft",
            "versions"
        )

        folder_name = f"{mc_version}-forge-{forge_version}"
        forge_path = os.path.join(versions_path, folder_name)

        return os.path.exists(forge_path)

    def set_playing_state(self, server_name, playing=True):
        for card in self.findChildren(ServerCard):
            if card.title == server_name:
                if playing:
                    card.button.setText("Jugando...")
                    card.button.setEnabled(False)
                else:
                    card.button.setText("Jugar")
                    card.button.setEnabled(True)

    def install_forge(self, mc_version, forge_version):
        import subprocess

        print("Instalando Forge automáticamente...")

        installer_url = (
            f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
            f"{mc_version}-{forge_version}/"
            f"forge-{mc_version}-{forge_version}-installer.jar"
        )

        installer_path = os.path.join(self.base_path, "forge_installer.jar")

        response = requests.get(installer_url)
        if response.status_code != 200:
            print("Error descargando Forge installer")
            return False

        with open(installer_path, "wb") as f:
            f.write(response.content)

        minecraft_path = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            ".minecraft"
        )

        try:
            subprocess.run(
                [
                    "java",
                    "-jar",
                    installer_path,
                    "--installClient"
                ],
                cwd=minecraft_path,   # 🔥 ESTA ES LA CLAVE
                check=True
            )

            print("Forge instalado correctamente")
            os.remove(installer_path)
            return True

        except Exception as e:
            print("Error instalando Forge:", e)
            return False  

    def install_fabric(self, mc_version, loader_version):
        import subprocess

        print("Instalando Fabric automáticamente...")

        installer_url = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.1/fabric-installer-1.0.1.jar"
        installer_path = os.path.join(self.base_path, "fabric_installer.jar")

        response = requests.get(installer_url)
        if response.status_code != 200:
            print("Error descargando Fabric installer")
            return False

        with open(installer_path, "wb") as f:
            f.write(response.content)

        minecraft_path = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            ".minecraft"
        )

        try:
            subprocess.run(
                [
                    "java",
                    "-jar",
                    installer_path,
                    "client",
                    "-mcversion",
                    mc_version,
                    "-loader",
                    loader_version
                ],
                cwd=minecraft_path,
                check=True
            )

            print("Fabric instalado correctamente")
            os.remove(installer_path)
            return True

        except Exception as e:
            print("Error instalando Fabric:", e)
            return False

            
    def launch_steam_game(self, server, server_name):
        steam_appid = server.get("steam_appid")

        if not steam_appid:
            return

        try:
            os.startfile(f"steam://run/{steam_appid}")

            # Cambiar botón a Jugando
            self.set_playing_state(server_name, True)

            # Esperar proceso real de Ark
            self.game_watcher = GameWatcher("ShooterGame.exe", server_name)
            self.game_watcher.finished_signal.connect(
                lambda name: self.set_playing_state(name, False)
            )
            self.game_watcher.start()

        except Exception as e:
            print("Error lanzando Steam:", e)

            error_dialog = QDialog(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.setFixedSize(400, 120)

            layout = QVBoxLayout(error_dialog)
            label = QLabel(
                "No se pudo abrir Steam.\n"
                "Verificá que esté instalado correctamente."
            )
            label.setAlignment(Qt.AlignCenter)

            layout.addWidget(label)
            error_dialog.exec()
        
    def __init__(self):
        super().__init__()
        self.news_data = []
        
        self.config_manager = ConfigManager()
        
        # ===============================
        # BASE PATH LAUNCHER
        # ===============================
        self.base_path = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            ".D0cCtorHub"
        )

        self.instances_path = os.path.join(self.base_path, "instances")

        os.makedirs(self.instances_path, exist_ok=True)
        
        # ===== CARGAR MONTSERRAT VARIABLE =====
        font_path = resource_path("Montserrat-VariableFont_wght.ttf")

        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            self.montserrat = families[0] if families else "Arial"
        else:
            self.montserrat = "Arial"

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle(" ")
        self.resize(1400, 850)
        self.setMinimumSize(1180, 720)
        
        
        # ===============================
        # SERVERS DATA (REMOTO)
        # ===============================

        remote_servers = self.load_servers_from_remote()
        self.load_news_from_remote()

        if remote_servers:
            self.servers_data = {s["id"]: s for s in remote_servers}
        else:
            self.servers_data = {}

        for server in remote_servers:

            instance_folder = os.path.join(self.instances_path, server["id"])
            version_file = os.path.join(instance_folder, "version.txt")

            is_installed = False
            needs_update = False

            # ===== VANILLA =====
            if server.get("loader") == "vanilla":

                if os.path.exists(instance_folder):
                    is_installed = True

            # ===== MODPACK =====
            elif os.path.exists(version_file):

                with open(version_file, "r") as f:
                    local_version = f.read().strip()

                if local_version == server.get("modpack_version"):
                    is_installed = True
                else:
                    needs_update = True

            self.servers_data[server["id"]] = {
                "workshop_collection": server.get("workshop_collection"),
                "installed": is_installed if server.get("type") != "steam" else True,
                "description": server.get("description", ""),
                "image_url": server.get("image_url"),
                "id": server["id"],
                "modpack_url": server.get("modpack_url"),
                "modpack_version": server.get("modpack_version"),
                "loader": server.get("loader"),
                "minecraft_version": server.get("minecraft_version"),
                "loader_version": server.get("loader_version"),
                "needs_update": needs_update if server.get("type") != "steam" else False,
                "type": server.get("type"),
                "steam_appid": server.get("steam_appid")
            }
       

        central = QWidget()
        self.setCentralWidget(central)

        main_vertical = QVBoxLayout(central)
        main_vertical.setContentsMargins(0, 0, 0, 0)
        main_vertical.setSpacing(0)

        # ===============================
        # CONTENIDO PRINCIPAL
        # ===============================
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_vertical.addLayout(main_layout)

        # ===============================
        # SIDEBAR
        # ===============================
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setObjectName("sidebar")

        sidebar.setStyleSheet("""
        #sidebar {
            background: qlineargradient(
                x1:0, y1:0,
                x2:0, y2:1,
                stop:0 #0b1020,
                stop:0.55 #080d18,
                stop:1 #060a12
            );
            border-right: 1px solid rgba(122, 92, 255, 70);
        }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.setContentsMargins(18, 24, 18, 18)
        sidebar_layout.setSpacing(12)

        # ===== LOGO IMAGEN =====
        pixmap = self.get_remote_asset("logo.png").scaled(
            132, 132,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.logo = GlowLogo(pixmap)

        logo_container = QHBoxLayout()
        logo_container.addStretch()
        logo_container.addWidget(self.logo)
        logo_container.addStretch()

        sidebar_layout.addLayout(logo_container)
        sidebar_layout.addSpacing(25)

        # Animación flotante
        self.float_direction = 1
        self.float_offset = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_logo)
        self.timer.start(30)

        # ===== BOTONES =====

        menu_items = [
            ("⌂", "Inicio"),
            ("▤", "Servidores"),
            ("▦", "Noticias"),
            ("⚙", "Ajustes"),
            ("◉", "Soporte"),
        ]

        buttons = []

        for icon, text in menu_items:
            btn = QPushButton(f"{icon}  {text}")
            btn_font = QFont(self.montserrat, 13)
            btn_font.setWeight(QFont.Weight.Medium)
            btn.setFont(btn_font)
            btn.setFixedHeight(48)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("navButton", True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #aeb7cc;
                    border: 1px solid transparent;
                    border-radius: 12px;
                    text-align: left;
                    padding-left: 18px;
                }
                QPushButton:hover {
                    background-color: rgba(91, 108, 255, 28);
                    color: #ffffff;
                    border-color: rgba(91, 108, 255, 70);
                }
            """)
            sidebar_layout.addWidget(btn)
            buttons.append(btn)

        self.btn_inicio = buttons[0]
        self.btn_servers = buttons[1]
        self.btn_news = buttons[2]
        self.btn_settings = buttons[3]
        self.btn_support = buttons[4]

        self.btn_inicio.clicked.connect(lambda: self.switch_page(0))
        self.btn_servers.clicked.connect(lambda: self.switch_page(1))
        self.btn_news.clicked.connect(lambda: self.switch_page(2))
        self.btn_settings.clicked.connect(lambda: self.switch_page(3))
        self.btn_support.clicked.connect(lambda: self.switch_page(4))

        # ===============================
        # VERSION PANEL (ABAJO SIDEBAR)
        # ===============================

        version_card = QFrame()
        version_card.setFixedHeight(95)
        version_card.setStyleSheet("""
            QFrame {
                background-color: #1f1f2a;
                border-radius: 12px;
            }
        """)

        version_layout = QVBoxLayout(version_card)
        version_layout.setContentsMargins(10, 10, 10, 10)
        version_layout.setSpacing(4)
        version_layout.setAlignment(Qt.AlignCenter)

        # Versión principal
        version_label = QLabel(f"v{APP_VERSION} {APP_STAGE}")
        version_font = QFont(self.montserrat, 15)
        version_font.setWeight(QFont.Weight.DemiBold)
        version_label.setFont(version_font)
        version_label.setStyleSheet("color: white;")
        version_label.setAlignment(Qt.AlignCenter)

        # ✨ Glow efecto
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setOffset(0)
        glow.setColor(QColor(255, 255, 255, 120))
        version_label.setGraphicsEffect(glow)

        # Build pequeña
        build_label = QLabel(f"Build {APP_BUILD}")
        build_font = QFont(self.montserrat, 9)
        build_label.setFont(build_font)
        build_label.setStyleSheet("color: #8888aa;")
        build_label.setAlignment(Qt.AlignCenter)

        version_layout.addWidget(version_label)
        version_layout.addWidget(build_label)

        sidebar_layout.addSpacing(12)
        sidebar_layout.addWidget(version_card)

        sidebar_layout.addStretch()

        # ===============================
        # MAIN CONTENT CON STACK
        # ===============================
        main_content = QFrame()
        main_content.setStyleSheet("background-color: #060a12;")

        # Layout vertical principal del lado derecho
        content_wrapper = QVBoxLayout(main_content)
        content_wrapper.setContentsMargins(28, 14, 24, 18)
        content_wrapper.setSpacing(0)

        # ===============================
        # BOTONES VENTANA (arriba derecha)
        # ===============================
        window_controls = QHBoxLayout()
        window_controls.setSpacing(5)
        window_controls.addStretch()

        min_btn = QPushButton("—")
        min_btn.setFixedSize(30, 30)
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                color: white;
                font-size: 15px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: red;
            }
        """)
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                color: white;
                font-size: 15px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: red;
            }
        """)
        close_btn.clicked.connect(self.close)

        window_controls.addWidget(min_btn)
        window_controls.addWidget(close_btn)

        content_wrapper.addLayout(window_controls)

        # ===============================
        # STACK
        # ===============================
        self.stack_container = QFrame()
        self.stack_container.setStyleSheet("background: transparent;")

        container_layout = QVBoxLayout(self.stack_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.stack = QStackedLayout()
        container_layout.addLayout(self.stack)

        content_wrapper.addWidget(self.stack_container, 1)
        # ===============================
        # FOOTER GLOBAL
        # ===============================
        footer_label = QLabel("© 2026 D0cCtor's Hub — No afiliado con Mojang, Valve o Studio Wildcard.")
        footer_label.setFont(QFont(self.montserrat, 10))
        footer_label.setStyleSheet("color: #555566;")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setFixedHeight(18)

        content_wrapper.addSpacing(2)
        content_wrapper.addWidget(footer_label)

        # Crear páginas
        self.home_page = self.create_home_page()
        self.servers_page = self.create_servers_page()
        self.news_page = self.create_news_page()
        self.settings_page = self.create_settings_page()
        self.support_page = self.create_support_page()

        # Agregar páginas al stack
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.servers_page)
        self.stack.addWidget(self.news_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.support_page)
        self.refresh_server_buttons()
        self.auto_detect_paths()

        main_layout.addWidget(sidebar)
        main_layout.addWidget(main_content)

        # Esperar a que Qt termine de montar y medir toda la ventana antes de
        # mostrar Inicio. Evita que la primera página aparezca comprimida.
        QTimer.singleShot(0, lambda: self.switch_page(0, animate=False))
        QTimer.singleShot(60, self._refresh_home_layout)
        
        # Cargar RAM guardada
        saved_ram = self.config_manager.get("ram", "4 GB")
        index = self.ram_selector.findText(saved_ram)
        if index >= 0:
            self.ram_selector.setCurrentIndex(index)

        self.ram_selector.currentTextChanged.connect(
            lambda value: self.config_manager.set("ram", value)
        )

        # 🔥 Verificar actualizaciones al iniciar
        self.check_for_updates()
            
        
    # =====================================================
    # SELECT FOLDERS
    # =====================================================
    def select_minecraft_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta Minecraft")
        if folder:
            self.minecraft_path.setText(folder)

    def select_steam_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta Steam")
        if folder:
            self.steam_path.setText(folder)
            
    # =====================================================
    # AUTO DETECT PATHS
    # =====================================================
    def auto_detect_paths(self):
        # Detectar .minecraft
        user_home = os.path.expanduser("~")
        minecraft_default = os.path.join(user_home, "AppData", "Roaming", ".minecraft")

        if os.path.exists(minecraft_default):
            self.minecraft_path.setText(minecraft_default)
        else:
            self.minecraft_path.setText("No encontrado")

        # Detectar Steam (rutas comunes)
        possible_steam_paths = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            os.path.join(user_home, "AppData", "Local", "Steam")
        ]

        steam_found = False
        for path in possible_steam_paths:
            if os.path.exists(path):
                self.steam_path.setText(path)
                steam_found = True
                break

        if not steam_found:
            self.steam_path.setText("No encontrado")
            
    def load_servers_from_remote(self):
        SERVERS_URL = "https://raw.githubusercontent.com/D0cCto0r/d0cctors-hub/main/remote/servers.json"

        try:
            response = requests.get(SERVERS_URL)
            data = response.json()

            print("Servers remotos cargados:")
            print(data)

            return data.get("servers", [])

        except Exception as e:
            print("Error cargando servers remotos:", e)
            return []
  
    def load_news_from_remote(self):
        try:
            url = "https://raw.githubusercontent.com/D0cCto0r/d0cctors-hub/main/remote/news.json"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.news_data = data.get("news", [])
                print("Noticias remotas cargadas:", self.news_data)
            else:
                self.news_data = []

        except Exception as e:
            print("Error cargando noticias:", e)
            self.news_data = []


    def get_remote_pixmap(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                return pixmap
        except:
            pass

        return QPixmap()
        
    # ===============================
    # DRAG WINDOW
    # ===============================
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()

    # ===============================
    # LOGO FLOAT
    # ===============================
    def animate_logo(self):
        self.float_offset += self.float_direction * 0.3

        if self.float_offset > 8:
            self.float_direction = -1
        elif self.float_offset < -8:
            self.float_direction = 1

        self.logo.move(self.logo.x(), int(30 + self.float_offset))
        
    # ===============================
    # NEWS CARD REUTILIZABLE
    # ===============================
    def create_news_card(self, news_item):
        news_card = QFrame()
        news_card.setFixedHeight(250)
        news_card.setMinimumWidth(660)   # 🔧 evita que Qt comprima la card
        news_card.setStyleSheet("""
            QFrame {
                background-color: #1a1a22;
                border-radius: 12px;
            }
        """)

        card_layout = QVBoxLayout(news_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Imagen
        pixmap = self.get_remote_pixmap(news_item["image"])
        image_label = RoundedImage(pixmap, radius=12)
        card_layout.addWidget(image_label)

        black_height = 100
        fade_height = 110

        black_bar = QFrame(news_card)
        black_bar.setStyleSheet("""
            background-color: rgb(0,0,0);
            border-bottom-left-radius: 12px;
            border-bottom-right-radius: 12px;
        """)

        fade_overlay = QFrame(news_card)
        fade_overlay.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0,
                x2:0, y2:1,
                stop:0 rgba(0,0,0,0),
                stop:0.3 rgba(0,0,0,120),
                stop:0.6 rgba(0,0,0,180),
                stop:1 rgba(0,0,0,255)
            );
        """)

        # Texto
        overlay_layout = QVBoxLayout(black_bar)
        overlay_layout.setContentsMargins(15, 10, 20, 10)
        overlay_layout.setSpacing(5)

        title = QLabel(news_item["title"])
        title.setFont(QFont(self.montserrat, 14))
        title.setStyleSheet("color: white;")

        desc = QLabel(news_item["description"])
        desc.setStyleSheet("color: #dddddd;")
        desc.setWordWrap(True)

        overlay_layout.addWidget(title)
        overlay_layout.addWidget(desc)

        # Posicionamiento dinámico
        def resize_overlays(event):
            width = news_card.width()
            height = news_card.height()

            black_bar.setGeometry(
                0,
                height - black_height,
                width,
                black_height
            )

            fade_overlay.setGeometry(
                0,
                height - black_height - fade_height + 20,  # 👈 ACÁ lo bajás
                width,
                fade_height
            )

        news_card.resizeEvent = resize_overlays

        return news_card
        
    # ===============================
    # HOME PAGE
    # ===============================
    def create_home_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical {
                background: rgba(255,255,255,0.035);
                width: 10px;
                margin: 4px 0 4px 2px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(117,128,255,0.38);
                border-radius: 5px;
                min-height: 48px;
            }
            QScrollBar::handle:vertical:hover { background: rgba(117,128,255,0.62); }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)

        page = QWidget()
        page.setObjectName("homePage")
        page.setStyleSheet("#homePage { background: transparent; }")
        page.setMinimumWidth(860)

        layout = QVBoxLayout(page)
        layout.setSpacing(18)
        layout.setContentsMargins(4, 8, 10, 16)
        layout.setAlignment(Qt.AlignTop)

        # HERO PRINCIPAL
        hero = QFrame()
        hero.setObjectName("hero")
        hero.setMinimumHeight(300)
        hero.setMaximumHeight(330)
        hero.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        hero.setStyleSheet("""
            #hero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(12, 20, 42, 245),
                    stop:0.55 rgba(18, 24, 55, 230),
                    stop:1 rgba(36, 20, 70, 225));
                border: 1px solid rgba(91, 108, 255, 85);
                border-radius: 18px;
            }
        """)
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(38, 28, 30, 26)
        hero_layout.setSpacing(24)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(8)
        eyebrow = QLabel("D0CCTOR'S HUB")
        eyebrow.setStyleSheet("color:#7f8cff; font-size:12px; font-weight:700; letter-spacing:2px;")

        title = QLabel("EXPLORÁ. CONSTRUÍ. <span style='color:#6d78ff'>SOBREVIVÍ.</span>")
        title.setTextFormat(Qt.RichText)
        title.setWordWrap(True)
        title.setMinimumHeight(92)
        title.setFont(QFont(self.montserrat, 27, QFont.Weight.Bold))
        title.setStyleSheet("color:white; background:transparent; border:none;")

        subtitle = QLabel("Entrá a nuestros servidores, instalá modpacks y mantené todo actualizado desde un solo lugar.")
        subtitle.setWordWrap(True)
        subtitle.setMaximumWidth(560)
        subtitle.setStyleSheet("color:#aeb7cc; font-size:13px; background:transparent; border:none;")

        hero_buttons = QHBoxLayout()
        hero_buttons.setSpacing(10)
        play_btn = QPushButton("▶   JUGAR")
        play_btn.setFixedSize(190, 56)
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.setStyleSheet("""
            QPushButton { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #4d5cff,stop:1 #765cff); color:white; border:none; border-radius:14px; font-size:16px; font-weight:700; }
            QPushButton:hover { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6370ff,stop:1 #8b72ff); }
        """)
        install_btn = QPushButton("⇩   SERVIDORES")
        install_btn.setFixedSize(190, 56)
        install_btn.setCursor(Qt.PointingHandCursor)
        install_btn.setStyleSheet("""
            QPushButton { background:rgba(8,12,24,180); color:#e8ebf5; border:1px solid rgba(255,255,255,35); border-radius:14px; font-size:14px; font-weight:650; }
            QPushButton:hover { border-color:#6875ff; background:rgba(31,39,74,210); }
        """)
        play_btn.clicked.connect(lambda: self.switch_page(1))
        install_btn.clicked.connect(lambda: self.switch_page(1))
        hero_buttons.addWidget(play_btn)
        hero_buttons.addWidget(install_btn)
        hero_buttons.addStretch()

        hero_text.addWidget(eyebrow)
        hero_text.addWidget(title)
        hero_text.addWidget(subtitle)
        hero_text.addSpacing(8)
        hero_text.addLayout(hero_buttons)
        hero_text.addStretch()
        hero_layout.addLayout(hero_text, 3)

        visual = QLabel()
        visual.setObjectName("heroVisual")
        visual.setMinimumWidth(250)
        visual.setMaximumWidth(340)
        visual.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        hero_pixmap = self.get_remote_asset("minecraft.png")
        if hero_pixmap and not hero_pixmap.isNull():
            visual.setPixmap(hero_pixmap.scaled(250, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        visual.setAlignment(Qt.AlignCenter)
        visual.setStyleSheet("#heroVisual { background:rgba(5,8,16,90); border:1px solid rgba(255,255,255,22); border-radius:16px; }")
        hero_layout.addWidget(visual, 2)
        layout.addWidget(hero)

        # ESTADO Y SERVIDORES DESTACADOS
        section_header = QHBoxLayout()
        status_dot = QLabel("●")
        status_dot.setStyleSheet("color:#49d17d; font-size:14px; background:transparent; border:none;")
        section_title = QLabel("ESTADO DE SERVIDORES")
        section_title.setFont(QFont(self.montserrat, 12, QFont.Weight.Bold))
        section_title.setStyleSheet("color:#f2f5ff; letter-spacing:1px; background:transparent; border:none;")
        all_btn = QPushButton("VER TODOS  ›")
        all_btn.setCursor(Qt.PointingHandCursor)
        all_btn.setStyleSheet("QPushButton{background:#0d1424;color:#c7cee0;border:1px solid rgba(255,255,255,25);border-radius:9px;padding:8px 15px;font-weight:650;} QPushButton:hover{border-color:#6572ff;color:white;}")
        all_btn.clicked.connect(lambda: self.switch_page(1))
        section_header.addWidget(status_dot)
        section_header.addWidget(section_title)
        section_header.addStretch()
        section_header.addWidget(all_btn)
        layout.addLayout(section_header)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        for server_name, data in list(self.servers_data.items())[:4]:
            card = QFrame()
            card.setObjectName("homeServerCard")
            card.setMinimumHeight(112)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            card.setStyleSheet("""
                #homeServerCard {
                    background:#0d1421;
                    border:1px solid rgba(255,255,255,22);
                    border-radius:14px;
                }
                #homeServerCard:hover { border-color:rgba(91,108,255,95); }
                #homeServerCard QLabel { background:transparent; border:none; }
            """)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 13, 14, 13)
            card_layout.setSpacing(12)

            image = QLabel()
            image.setObjectName("serverThumb")
            pixmap = self.get_remote_pixmap(data.get("image_url"))
            if pixmap and not pixmap.isNull():
                image.setPixmap(pixmap.scaled(62, 62, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            image.setFixedSize(68, 68)
            image.setAlignment(Qt.AlignCenter)
            image.setStyleSheet("#serverThumb { background:#111a2d; border:1px solid rgba(255,255,255,18); border-radius:12px; }")

            text = QVBoxLayout()
            text.setSpacing(3)
            name = QLabel(server_name)
            name.setFont(QFont(self.montserrat, 12, QFont.Weight.Bold))
            name.setStyleSheet("color:white;")
            version = QLabel(str(data.get("minecraft_version") or "Steam"))
            version.setStyleSheet("color:#7f899f;font-size:11px;")
            state = QLabel("●  Disponible")
            state.setStyleSheet("color:#49d17d;font-size:11px;font-weight:650;")
            text.addWidget(name)
            text.addWidget(version)
            text.addStretch()
            text.addWidget(state)
            card_layout.addWidget(image)
            card_layout.addLayout(text, 1)
            cards_layout.addWidget(card, 1)
        layout.addLayout(cards_layout)

        # NOTICIA DESTACADA
        news_header = QHBoxLayout()
        news_title = QLabel("NOTICIAS DESTACADAS")
        news_title.setFont(QFont(self.montserrat, 12, QFont.Weight.Bold))
        news_title.setStyleSheet("color:#f2f5ff; letter-spacing:1px; background:transparent; border:none;")
        more_news_btn = QPushButton("VER TODAS  ›")
        more_news_btn.setCursor(Qt.PointingHandCursor)
        more_news_btn.setStyleSheet("QPushButton{background:#0d1424;color:#c7cee0;border:1px solid rgba(255,255,255,25);border-radius:9px;padding:8px 15px;font-weight:650;} QPushButton:hover{border-color:#6572ff;color:white;}")
        more_news_btn.clicked.connect(lambda: self.switch_page(2))
        news_header.addWidget(news_title)
        news_header.addStretch()
        news_header.addWidget(more_news_btn)
        layout.addLayout(news_header)

        latest = self.news_data[0] if self.news_data else None
        if latest:
            news_card = self.create_news_card(latest)
            news_card.setMinimumWidth(0)
            news_card.setFixedHeight(240)
            news_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            layout.addWidget(news_card)

        scroll.setWidget(page)
        self.home_scroll = scroll
        return scroll

    def _refresh_home_layout(self):
        if hasattr(self, "home_page"):
            self.home_page.updateGeometry()
        if hasattr(self, "home_scroll"):
            self.home_scroll.viewport().update()
        self.stack_container.updateGeometry()
        self.centralWidget().updateGeometry()
        QApplication.processEvents()


    # ===============================
    # SERVERS PAGE
    # ===============================
    def create_servers_page(self):

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 👇 scrollbar izquierda (igual que noticias)
        scroll.setLayoutDirection(Qt.RightToLeft)

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }

            QScrollBar:vertical {
                background: rgba(255,255,255,0.06);
                width: 12px;
                margin: 5px 0px 5px 4px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.35);
                border-radius: 6px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.55);
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        container = QWidget()

        # 👇 esto hace que el contenido vuelva a la normalidad
        container.setLayoutDirection(Qt.LeftToRight)

        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(100, 20, 40, 30)

        title = QLabel("Servidores Disponibles")
        title.setFont(QFont(self.montserrat, 16))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        description = QLabel(
            "Conectate a nuestros servidores oficiales.\n"
            "Modpacks optimizados y soporte activo."
        )
        description.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(description)

        layout.addSpacing(20)

        for server_name, data in self.servers_data.items():

            pixmap = self.get_remote_pixmap(data.get("image_url"))

            card = ServerCard(
                server_name,
                data["description"],
                self.montserrat,
                pixmap,
                data.get("installed", False),
                self.handle_server_action,
                large=True
            )

            layout.addWidget(card)

        layout.addStretch()

        scroll.setWidget(container)

        return scroll
        
    def create_server_big_card(self, server_name, data):

        card = QFrame()
        card.setFixedHeight(140)
        card.setStyleSheet("""
            QFrame {
                background-color: #1a1a22;
                border-radius: 14px;
            }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        pixmap = self.get_remote_pixmap(data.get("image_url"))

        image = QLabel()
        image.setFixedSize(90, 90)

        if pixmap and not pixmap.isNull():
            image.setPixmap(
                pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        layout.addWidget(image)

        text_layout = QVBoxLayout()

        title = QLabel(server_name)
        title.setFont(QFont(self.montserrat, 15))
        title.setStyleSheet("color: white;")

        desc = QLabel(data.get("description", "Servidor disponible"))
        desc.setStyleSheet("color: #aaaaaa;")
        desc.setWordWrap(True)

        text_layout.addWidget(title)
        text_layout.addWidget(desc)

        layout.addLayout(text_layout)

        layout.addStretch()

        button = QPushButton()
        button.setFixedSize(120, 36)
        button.setCursor(Qt.PointingHandCursor)

        if data.get("needs_update"):
            button.setText("Actualizar")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ffaa00;
                    color: black;
                    border-radius: 12px;
                    font-weight: bold;
                }
            """)
        elif data.get("installed"):
            button.setText("Jugar")
            button.setStyleSheet("""
                QPushButton {
                    background-color: #ff2d55;
                    color: white;
                    border-radius: 12px;
                    font-weight: bold;
                }
            """)
        else:
            button.setText("Instalar")
            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: black;
                    border-radius: 12px;
                    font-weight: bold;
                }
            """)

        button.clicked.connect(lambda: self.handle_server_action(server_name))

        layout.addWidget(button)

        return card


    # ===============================
    # NEWS PAGE (con scroll)
    # ===============================
    def create_news_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 👇 mueve la scrollbar al lado izquierdo
        scroll.setLayoutDirection(Qt.RightToLeft)

        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }

            /* TRACK (lado izquierdo) */
            QScrollBar:vertical {
                background: rgba(255,255,255,0.06);
                width: 12px;
                margin: 5px 0px 5px 4px;
                border-radius: 6px;
            }

            /* HANDLE */
            QScrollBar::handle:vertical {
                background: rgba(255,255,255,0.35);
                border-radius: 6px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: rgba(255,255,255,0.55);
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        container = QWidget()
        container.setMinimumWidth(700)

        # 👇 volvemos el contenido a LeftToRight para que el texto no se invierta
        container.setLayoutDirection(Qt.LeftToRight)

        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 20, 40, 30)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        title = QLabel("Noticias")
        title.setFont(QFont(self.montserrat, 16))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        for news in self.news_data:
            layout.addWidget(self.create_news_card(news))

        layout.addStretch()

        scroll.setWidget(container)

        return scroll


    # ===============================
    # SETTINGS PAGE
    # ===============================
    def create_settings_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(40, 20, 40, 30)
        main_layout.setSpacing(20)

        title = QLabel("Ajustes")
        title.setFont(QFont(self.montserrat, 20))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # =====================================================
        # SECCIÓN MINECRAFT
        # =====================================================
        minecraft_frame = QFrame()
        minecraft_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a22;
                border-radius: 14px;
            }
        """)
        mc_layout = QVBoxLayout(minecraft_frame)
        mc_layout.setContentsMargins(20, 20, 20, 20)
        mc_layout.setSpacing(12)

        mc_title = QLabel("Minecraft")
        mc_title.setFont(QFont(self.montserrat, 14))
        mc_title.setStyleSheet("color: white;")
        mc_layout.addWidget(mc_title)

        self.minecraft_path = QLabel("No configurado")
        self.minecraft_path.setStyleSheet("color: #aaaaaa;")
        self.minecraft_path.setWordWrap(True)
        mc_layout.addWidget(self.minecraft_path)

        mc_btn = QPushButton("Seleccionar carpeta Minecraft")
        mc_btn.setCursor(Qt.PointingHandCursor)
        mc_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a38;
                color: white;
                border-radius: 10px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #3a3a4a;
            }
        """)
        mc_btn.clicked.connect(self.select_minecraft_folder)
        mc_layout.addWidget(mc_btn)

        main_layout.addWidget(minecraft_frame)
        
        # ================= RAM SELECTOR =================

        ram_label = QLabel("RAM asignada:")
        ram_label.setStyleSheet("color: white;")
        mc_layout.addWidget(ram_label)

        self.ram_selector = QComboBox()
        self.ram_selector.addItems([
            "2 GB",
            "4 GB",
            "6 GB",
            "8 GB",
            "12 GB"
        ])
        self.ram_selector.setStyleSheet("""
            QComboBox {
                background-color: #2a2a38;
                color: white;
                border-radius: 8px;
                padding: 5px;
            }
        """)

        mc_layout.addWidget(self.ram_selector)

        # =====================================================
        # SECCIÓN STEAM
        # =====================================================
        steam_frame = QFrame()
        steam_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a22;
                border-radius: 14px;
            }
        """)
        steam_layout = QVBoxLayout(steam_frame)
        steam_layout.setContentsMargins(20, 20, 20, 20)
        steam_layout.setSpacing(12)

        steam_title = QLabel("Steam")
        steam_title.setFont(QFont(self.montserrat, 14))
        steam_title.setStyleSheet("color: white;")
        steam_layout.addWidget(steam_title)

        self.steam_path = QLabel("No configurado")
        self.steam_path.setStyleSheet("color: #aaaaaa;")
        self.steam_path.setWordWrap(True)
        steam_layout.addWidget(self.steam_path)

        steam_btn = QPushButton("Seleccionar carpeta Steam")
        steam_btn.setCursor(Qt.PointingHandCursor)
        steam_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a38;
                color: white;
                border-radius: 10px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #3a3a4a;
            }
        """)
        steam_btn.clicked.connect(self.select_steam_folder)
        steam_layout.addWidget(steam_btn)

        main_layout.addWidget(steam_frame)

        main_layout.addStretch()

        return page
        

    # ===============================
    # SUPPORT PAGE
    # ===============================
    def create_support_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(40, 20, 40, 30)

        # Centrar todo verticalmente
        main_layout.addStretch()

        # Contenedor central
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)

        # TÍTULO
        title = QLabel("Soporte")
        title.setFont(QFont(self.montserrat, 20))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # DESCRIPCIÓN
        desc = QLabel(
            "¿Necesitás ayuda?\n\n"
            "Unite a nuestro Discord oficial para soporte técnico,\n"
            "reportar bugs o sugerencias."
        )
        desc.setFont(QFont(self.montserrat, 12))
        desc.setStyleSheet("color: #aaaaaa;")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setMaximumWidth(500)  # 👈 limita ancho para mejor lectura
        layout.addWidget(desc)

        # BOTÓN DISCORD
        discord_btn = QPushButton("Unirse al Discord")
        discord_btn.setFixedSize(220, 45)
        discord_btn.setCursor(Qt.PointingHandCursor)
        discord_btn.setStyleSheet("""
            QPushButton {
                background-color: #5865F2;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7289da;
            }
        """)
        discord_btn.clicked.connect(lambda: webbrowser.open("https://discord.gg/FcsSSe6ReA"))

        layout.addWidget(discord_btn, alignment=Qt.AlignCenter)

        main_layout.addWidget(container)
        main_layout.addStretch()

        return page
        
    def handle_server_action(self, server_name):

        # ===== REINSTALAR MODS =====
        if server_name == "__RESET_MODS__":
            ark_path = os.path.join(self.instances_path, "ark")
            flag_file = os.path.join(ark_path, "mods_installed.txt")

            if os.path.exists(flag_file):
                os.remove(flag_file)
                print("Mods de Ark reseteados")

            return

        server = self.servers_data.get(server_name)

        if not server:
            return

        # ================= STEAM GAME =================
        if server.get("type") == "steam":

            instance_folder = os.path.join(self.instances_path, server["id"])
            flag_file = os.path.join(instance_folder, "mods_installed.txt")
            collection = server.get("workshop_collection")

            collection_id = None
            if collection and "id=" in collection:
                collection_id = collection.split("id=")[-1]

            # ===== PRIMERA VEZ =====
            if not os.path.exists(flag_file):

                print("Entrando a popup Ark")
                os.makedirs(instance_folder, exist_ok=True)

                dialog = QDialog(self)
                dialog.setWindowTitle("Instalar mods de Ark")
                dialog.setFixedSize(420, 180)

                layout = QVBoxLayout(dialog)

                label = QLabel(
                    "Antes de jugar, tenés que suscribirte a los mods.\n\n"
                    "Se va a abrir la colección de Steam.\n"
                    "Hacé click en 'Suscribirse a todo' y luego volvé al juego."
                )
                label.setAlignment(Qt.AlignCenter)
                label.setWordWrap(True)

                btn = QPushButton("Abrir colección y continuar")
                btn.setCursor(Qt.PointingHandCursor)

                layout.addWidget(label)
                layout.addWidget(btn)

                # ===== CLICK =====
                def open_collection():
                    print("CLICK DETECTADO - abriendo colección")

                    if collection_id:
                        try:
                            subprocess.Popen([
                                "cmd",
                                "/c",
                                "start",
                                f"steam://openurl/https://steamcommunity.com/sharedfiles/filedetails/?id={collection_id}"
                            ], shell=True)
                        except Exception as e:
                            print("Error abriendo Steam:", e)

                    dialog.accept()

                    # ===== POPUP CONFIRMACIÓN =====
                    confirm = QDialog(self)
                    confirm.setWindowTitle("Confirmación")
                    confirm.setFixedSize(350, 150)

                    confirm_layout = QVBoxLayout(confirm)

                    confirm_label = QLabel("¿Ya te suscribiste a la colección?")
                    confirm_label.setAlignment(Qt.AlignCenter)

                    btn_yes = QPushButton("Sí")
                    btn_no = QPushButton("No")

                    btn_layout = QHBoxLayout()
                    btn_layout.addWidget(btn_yes)
                    btn_layout.addWidget(btn_no)

                    confirm_layout.addWidget(confirm_label)
                    confirm_layout.addLayout(btn_layout)

                    # ===== SI CONFIRMA =====
                    def confirm_yes():
                        os.makedirs(instance_folder, exist_ok=True)
                        with open(flag_file, "w") as f:
                            f.write("ok")

                        confirm.accept()

                        # ===== POPUP FAVORITOS =====
                        fav_dialog = QDialog(self)
                        fav_dialog.setWindowTitle("Agregar a favoritos")
                        fav_dialog.setFixedSize(360, 150)

                        fav_layout = QVBoxLayout(fav_dialog)

                        fav_label = QLabel("¿Querés agregar el servidor a favoritos?")
                        fav_label.setAlignment(Qt.AlignCenter)

                        fav_yes = QPushButton("Sí")
                        fav_no = QPushButton("No")

                        fav_btn_layout = QHBoxLayout()
                        fav_btn_layout.addWidget(fav_yes)
                        fav_btn_layout.addWidget(fav_no)

                        fav_layout.addWidget(fav_label)
                        fav_layout.addLayout(fav_btn_layout)

                        def add_favorite():
                            try:
                                server_ip = "shibuyaz.ddns.net:7777"

                                os.startfile(f"steam://connect/{server_ip}")
                                print("Servidor agregado a favoritos")
                            except Exception as e:
                                print("Error agregando favorito:", e)

                            fav_dialog.accept()
                            self.launch_steam_game(server, server_name)

                        def skip_favorite():
                            fav_dialog.accept()
                            self.launch_steam_game(server, server_name)

                        fav_yes.clicked.connect(add_favorite)
                        fav_no.clicked.connect(skip_favorite)

                        fav_dialog.exec()

                    def confirm_no():
                        confirm.close()

                    btn_yes.clicked.connect(confirm_yes)
                    btn_no.clicked.connect(confirm_no)

                    confirm.exec()

                # 🔥 IMPORTANTE
                btn.clicked.connect(open_collection)

                dialog.exec()
                return

            # ===== YA INSTALADO =====
            self.launch_steam_game(server, server_name)
            return

        # ================= INSTALAR / ACTUALIZAR =================
        if not server["installed"] or server.get("needs_update"):
            
            # ===== VANILLA SERVER (sin modpack) =====
            if server.get("loader") == "vanilla":
                status_dialog = self.show_status_dialog("Iniciando Minecraft...")
                self.launch_minecraft(server, server_name)
                status_dialog.close()
                return

            import shutil

            instance_folder = os.path.join(self.instances_path, server["id"])

            if os.path.exists(instance_folder):
                print("Eliminando instancia anterior...")
                shutil.rmtree(instance_folder)

            # --- Java ---
            status_dialog = self.show_status_dialog("Verificando Java...")
            if not self.check_java_installed():
                status_dialog.close()
                print("Java no detectado")
                return
            status_dialog.close()

            # --- Forge ---
            if server.get("loader") == "forge":
                mc_version = server.get("minecraft_version")
                forge_version = server.get("loader_version")

                if not self.is_forge_installed(mc_version, forge_version):
                    status_dialog = self.show_status_dialog("Instalando Forge...")
                    if not self.install_forge(mc_version, forge_version):
                        status_dialog.close()
                        print("No se pudo instalar Forge")
                        return
                    status_dialog.close()
                    
            # --- Fabric ---
            elif server.get("loader") == "fabric":

                mc_version = server.get("minecraft_version")
                fabric_version = server.get("loader_version")

                status_dialog = self.show_status_dialog("Instalando Fabric...")

                if not self.install_fabric(mc_version, fabric_version):
                    status_dialog.close()
                    print("No se pudo instalar Fabric")
                    return

                status_dialog.close()

            # --- Modpack ---
            self.show_install_dialog(server)

            if os.path.exists(os.path.join(instance_folder, "version.txt")):
                server["installed"] = True
                server["needs_update"] = False
                self.create_minecraft_profile(server)

        # ================= JUGAR =================
        else:
            status_dialog = self.show_status_dialog("Iniciando Minecraft...")
            print(f"Jugando {server_name}...")
            self.launch_minecraft(server, server_name)
            status_dialog.close()

        self.refresh_server_buttons()


    def refresh_server_buttons(self):
        for card in self.findChildren(ServerCard):
            name = card.title

            if name in self.servers_data:
                server = self.servers_data[name]

                if server.get("needs_update"):
                    card.button.setText("Actualizar")
                    card.button.setStyleSheet("""
                        QPushButton {
                            background-color: #ffaa00;
                            color: black;
                            border-radius: 12px;
                            font-weight: bold;
                        }
                    """)

                elif server.get("installed"):
                    card.button.setText("Jugar")
                    card.button.setStyleSheet("""
                        QPushButton {
                            background-color: #ff2d55;
                            color: white;
                            border-radius: 12px;
                            font-weight: bold;
                        }
                    """)

                else:
                    card.button.setText("Instalar")
                    card.button.setStyleSheet("""
                        QPushButton {
                            background-color: white;
                            color: black;
                            border-radius: 12px;
                            font-weight: bold;
                        }
                    """)
                    
    # =====================================================
    # PAGE TRANSITION (FADE FIXED)
    # =====================================================
    def switch_page(self, index, animate=True):

        # Cambiar página primero
        self.stack.setCurrentIndex(index)
        if index == 0:
            QTimer.singleShot(0, self._refresh_home_layout)

        nav_buttons = [self.btn_inicio, self.btn_servers, self.btn_news, self.btn_settings, self.btn_support]
        for i, button in enumerate(nav_buttons):
            if i == index:
                button.setStyleSheet("""
                    QPushButton { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(75,88,255,90),stop:1 rgba(92,70,190,55)); color:white; border:1px solid rgba(103,116,255,150); border-radius:12px; text-align:left; padding-left:18px; font-weight:650; }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton { background:transparent; color:#aeb7cc; border:1px solid transparent; border-radius:12px; text-align:left; padding-left:18px; }
                    QPushButton:hover { background-color:rgba(91,108,255,28); color:white; border-color:rgba(91,108,255,70); }
                """)

        if not animate:
            return

        # Animar el contenedor (NO el widget interno)
        geo = self.stack_container.geometry()

        bounce_anim = QPropertyAnimation(self.stack_container, b"geometry")
        bounce_anim.setDuration(220)
        bounce_anim.setStartValue(geo.adjusted(0, -10, 0, -10))
        bounce_anim.setEndValue(geo)
        bounce_anim.setEasingCurve(QEasingCurve.OutCubic)

        bounce_anim.start()
        self._bounce_anim = bounce_anim
        
    def show_install_dialog(self, server_data):
        dialog = QDialog(self)
        dialog.setWindowTitle("Instalando...")
        dialog.setFixedSize(400, 150)

        # ===== VANILLA INSTALL =====
        if server_data.get("loader") == "vanilla":

            instance_folder = os.path.join(self.instances_path, server_data["id"])
            os.makedirs(instance_folder, exist_ok=True)

            with open(os.path.join(instance_folder, "version.txt"), "w") as v:
                v.write(server_data["minecraft_version"])

            server_ip = server_data.get("server_ip")

            if server_ip:
                with open(os.path.join(instance_folder, "server.txt"), "w") as f:
                    f.write(server_ip)

            print("Instancia vanilla creada")
            self.install_servers_dat()
            server_data["installed"] = True

            return

        layout = QVBoxLayout(dialog)

        label = QLabel("Descargando modpack...")
        label.setAlignment(Qt.AlignCenter)

        progress = QProgressBar()
        progress.setValue(0)

        layout.addWidget(label)
        layout.addWidget(progress)

        server_id = server_data["id"]
        instance_folder = os.path.join(self.instances_path, server_id)

        self.worker = InstallWorker(
            server_data["modpack_url"],
            instance_folder,
            server_data["modpack_version"]
        )

        self.worker.progress.connect(progress.setValue)
        self.worker.finished.connect(dialog.accept)
        self.worker.error.connect(lambda e: print("Error:", e))

        print("Iniciando worker...")
        self.worker.start()

        dialog.exec()
        
    def show_status_dialog(self, message):
        dialog = QDialog(self)
        dialog.setWindowTitle("Procesando...")
        dialog.setFixedSize(400, 140)

        layout = QVBoxLayout(dialog)

        label = QLabel(message)
        label.setAlignment(Qt.AlignCenter)

        progress = QProgressBar()
        progress.setRange(0, 0)

        layout.addWidget(label)
        layout.addWidget(progress)

        dialog.show()
        QApplication.processEvents()

        return dialog

        self.worker.progress.connect(progress.setValue)
        self.worker.finished.connect(dialog.accept)
        self.worker.error.connect(lambda e: print("Error:", e))

        progress.setValue(0)
        print("Iniciando worker...")
        self.worker.start()
        dialog.exec()     
        
    def launch_minecraft(self, server, server_name):
        print("Preparando perfil para launcher oficial...")

        self.create_minecraft_profile(server)

        print("Intentando abrir Minecraft Launcher...")

        # ===== Intentar versión Microsoft Store =====
        try:
            subprocess.Popen(
                r'explorer.exe shell:AppsFolder\Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft'
            )

            # 🔥 CAMBIO ESTADO A JUGANDO
            self.set_playing_state(server_name, True)

            # 🔥 WATCHER PARA JAVA (JUEGO REAL)
            self.game_watcher = GameWatcher("javaw.exe", server_name)
            self.game_watcher.finished_signal.connect(
                lambda name: self.set_playing_state(name, False)
            )
            self.game_watcher.start()

            return

        except Exception:
            pass

        # ===== Intentar versión clásica Win32 =====
        possible_paths = [
            r"C:\Program Files (x86)\Minecraft Launcher\MinecraftLauncher.exe",
            r"C:\Program Files\Minecraft Launcher\MinecraftLauncher.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                subprocess.Popen(path)

                # 🔥 CAMBIO ESTADO A JUGANDO
                self.set_playing_state(server_name, True)

                # 🔥 WATCHER PARA JAVA
                self.game_watcher = GameWatcher("javaw.exe", server_name)
                self.game_watcher.finished_signal.connect(
                    lambda name: self.set_playing_state(name, False)
                )
                self.game_watcher.start()

                return

        # ===== Si no se encontró =====
        error_dialog = QDialog(self)
        error_dialog.setWindowTitle("Error")
        error_dialog.setFixedSize(420, 150)

        layout = QVBoxLayout(error_dialog)

        label = QLabel(
            "No se detectó Minecraft Launcher instalado.\n\n"
            "Instalalo desde la Microsoft Store o desde minecraft.net"
        )
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)

        layout.addWidget(label)

        error_dialog.exec()
    
    def create_minecraft_profile(self, server):
        import json
        from datetime import datetime

        mc_path = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            ".minecraft"
        )

        profiles_path = os.path.join(mc_path, "launcher_profiles.json")

        if not os.path.exists(profiles_path):
            print("No existe launcher_profiles.json")
            return

        with open(profiles_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        profile_name = f"Servidor {server['id']}"

        instance_folder = os.path.join(self.instances_path, server["id"])

        if server.get("loader") == "forge":
            version_id = f"{server['minecraft_version']}-forge-{server['loader_version']}"

        elif server.get("loader") == "fabric":
            version_id = f"fabric-loader-{server['loader_version']}-{server['minecraft_version']}"

        else:
            version_id = server["minecraft_version"]

        ram_value = server.get(
            "recommended_ram",
            self.config_manager.get("ram", "4 GB")
        )
        ram_number = ram_value.split()[0]

        if "profiles" not in data:
            data["profiles"] = {}

        data["profiles"][profile_name] = {
            "name": profile_name,
            "type": "custom",
            "created": datetime.now().isoformat(),
            "lastUsed": datetime.now().isoformat(),
            "icon": "Grass",
            "lastVersionId": version_id,
            "gameDir": instance_folder,
            "javaArgs": f"-Xmx{ram_number}G"
        }

        with open(profiles_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print("Perfil creado/actualizado correctamente.")    

    def install_servers_dat(self):

        import shutil

        url = "https://raw.githubusercontent.com/D0cCto0r/d0cctors-hub/main/remote/servers.dat"

        mc_path = os.path.join(
            os.path.expanduser("~"),
            "AppData",
            "Roaming",
            ".minecraft"
        )

        servers_path = os.path.join(mc_path, "servers.dat")

        try:
            response = requests.get(url)

            if response.status_code == 200:

                with open(servers_path, "wb") as f:
                    f.write(response.content)

                print("servers.dat instalado")

        except Exception as e:
            print("Error instalando servers.dat:", e)        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec())