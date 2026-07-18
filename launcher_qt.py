APP_VERSION = "0.3"
APP_STAGE = "Beta"
APP_BUILD = "2026.6.5"
APP_FULL_VERSION = f"{APP_VERSION}-{APP_BUILD}"

# ===============================
# PALETA VISUAL DEL LAUNCHER
# ===============================
COLOR_BG = "#04080c"
COLOR_BG_SECONDARY = "#0e1529"
COLOR_SIDEBAR_TOP = "#0b1019"
COLOR_SIDEBAR_MIDDLE = "#080d15"
COLOR_SIDEBAR_BOTTOM = "#070b11"

COLOR_CARD = "#0e1529"
COLOR_CARD_DARK = "#0d131c"
COLOR_CARD_HOVER = "#151d29"

COLOR_BORDER = "rgba(19, 28, 31)"
COLOR_BORDER_STRONG = "rgba(19, 28, 31)"
COLOR_BORDER_HOVER = "rgba(125,115,255,125)"

COLOR_PRIMARY = "#6c63ff"
COLOR_PRIMARY_LIGHT = "#837bff"
COLOR_PRIMARY_DARK = "#554ce5"

COLOR_TEXT = "#f3f5fb"
COLOR_TEXT_SECONDARY = "#a8b0c1"
COLOR_TEXT_MUTED = "#747e91"

COLOR_ONLINE = "#55dc7a"
COLOR_WARNING = "#f5bf57"
COLOR_OFFLINE = "#ff6674"

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
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRectF, QPointF, QRectF, QSize
from PySide6.QtGui import QFont, QIcon, QPen, QPolygonF
from PySide6.QtSvg import QSvgRenderer
from config_manager import ConfigManager
import requests
import minecraft_launcher_lib
import psutil
import subprocess
import socket
import struct
import json
import time
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
    def __init__(
        self,
        pixmap,
        radius=12,
        background_color="#172232",
        round_mode="all"
    ):
        super().__init__()
        self.pixmap_original = pixmap
        self.radius = radius
        self.background_color = QColor(background_color)
        self.round_mode = round_mode

        # Evita fondos rectangulares detrás del recorte.
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background:transparent; border:none;")

    def _clip_path(self):
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()

        if self.round_mode == "left":
            # Extiende el rectángulo hacia la derecha para que solo queden
            # redondeadas las dos esquinas exteriores izquierdas.
            extended = QRectF(
                rect.x(),
                rect.y(),
                rect.width() + self.radius,
                rect.height()
            )
            path.addRoundedRect(extended, self.radius, self.radius)

        elif self.round_mode == "none":
            path.addRect(rect)

        else:
            path.addRoundedRect(rect, self.radius, self.radius)

        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        path = self._clip_path()
        painter.setClipPath(path)
        painter.fillPath(path, self.background_color)

        if self.pixmap_original and not self.pixmap_original.isNull():
            scaled = self.pixmap_original.scaled(
                self.width(),
                self.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )

            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            
            
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
            

class ServerStatusWorker(QThread):
    """Consulta servidores reales sin bloquear la interfaz."""

    status_ready = Signal(str, dict)

    def __init__(self, servers, interval_seconds=30):
        super().__init__()
        self.servers = servers
        self.interval_seconds = max(10, int(interval_seconds))
        self._running = True

    def stop(self):
        self._running = False

    @staticmethod
    def _split_address(address, default_port):
        address = str(address or "").strip()

        if not address:
            return None, None

        if address.startswith("[") and "]" in address:
            host, remainder = address[1:].split("]", 1)
            port = int(remainder[1:]) if remainder.startswith(":") else default_port
            return host, port

        if address.count(":") == 1:
            host, port_text = address.rsplit(":", 1)
            try:
                return host.strip(), int(port_text)
            except ValueError:
                return address, default_port

        return address, default_port

    @staticmethod
    def _encode_varint(value):
        result = bytearray()
        while True:
            current = value & 0x7F
            value >>= 7
            if value:
                current |= 0x80
            result.append(current)
            if not value:
                return bytes(result)

    @staticmethod
    def _read_varint(sock):
        value = 0
        position = 0

        while True:
            raw = sock.recv(1)
            if not raw:
                raise ConnectionError("Conexión cerrada leyendo VarInt")

            current = raw[0]
            value |= (current & 0x7F) << position

            if not current & 0x80:
                return value

            position += 7
            if position >= 35:
                raise ValueError("VarInt demasiado grande")

    @classmethod
    def query_minecraft(cls, address, timeout=3.0):
        host, port = cls._split_address(address, 25565)
        if not host:
            raise ValueError("Falta server_ip")

        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            host_bytes = host.encode("utf-8")

            handshake = (
                cls._encode_varint(0)
                + cls._encode_varint(760)
                + cls._encode_varint(len(host_bytes))
                + host_bytes
                + struct.pack(">H", port)
                + cls._encode_varint(1)
            )

            sock.sendall(cls._encode_varint(len(handshake)) + handshake)
            sock.sendall(b"\x01\x00")

            cls._read_varint(sock)
            packet_id = cls._read_varint(sock)

            if packet_id != 0:
                raise ValueError(f"Respuesta Minecraft inesperada: {packet_id}")

            json_length = cls._read_varint(sock)
            response = bytearray()

            while len(response) < json_length:
                chunk = sock.recv(json_length - len(response))
                if not chunk:
                    raise ConnectionError("Respuesta Minecraft incompleta")
                response.extend(chunk)

            # Ping real del protocolo Minecraft.
            # Esto mide solo el viaje ping/pong y evita incluir DNS,
            # conexión TCP y descarga del JSON de estado.
            ping_payload = int(time.time_ns() // 1_000_000)
            ping_packet = cls._encode_varint(1) + struct.pack(">q", ping_payload)

            ping_started = time.perf_counter()
            sock.sendall(cls._encode_varint(len(ping_packet)) + ping_packet)

            cls._read_varint(sock)
            pong_packet_id = cls._read_varint(sock)

            if pong_packet_id != 1:
                raise ValueError(
                    f"Respuesta pong inesperada: {pong_packet_id}"
                )

            pong_payload = sock.recv(8)
            if len(pong_payload) != 8:
                raise ConnectionError("Respuesta pong incompleta")

            latency_ms = round((time.perf_counter() - ping_started) * 1000)

        payload = json.loads(response.decode("utf-8"))

        players = payload.get("players", {})
        version = payload.get("version", {})

        return {
            "status": "online",
            "players_online": int(players.get("online", 0) or 0),
            "players_max": int(players.get("max", 0) or 0),
            "ping": latency_ms,
            "version": str(version.get("name", "") or ""),
        }

    @classmethod
    def query_source(cls, address, timeout=3.0):
        """Consulta A2S_INFO para servidores Steam/Source, incluido ARK."""
        host, port = cls._split_address(address, 27015)
        if not host:
            raise ValueError("Falta query_ip o server_ip")

        query = b"\xFF\xFF\xFF\xFFTSource Engine Query\x00"
        started = time.perf_counter()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(query, (host, port))
            response, _ = sock.recvfrom(65535)

        latency_ms = round((time.perf_counter() - started) * 1000)

        if not response.startswith(b"\xFF\xFF\xFF\xFFI"):
            raise ValueError("Respuesta A2S_INFO no reconocida")

        offset = 5

        def read_cstring():
            nonlocal offset
            end = response.index(b"\x00", offset)
            value = response[offset:end].decode("utf-8", errors="replace")
            offset = end + 1
            return value

        protocol = response[offset]
        offset += 1
        server_name = read_cstring()
        map_name = read_cstring()
        folder = read_cstring()
        game_name = read_cstring()

        if offset + 5 > len(response):
            raise ValueError("Respuesta A2S_INFO incompleta")

        app_id = struct.unpack_from("<H", response, offset)[0]
        offset += 2

        players_online = response[offset]
        players_max = response[offset + 1]
        bots = response[offset + 2]

        return {
            "status": "online",
            "players_online": int(players_online),
            "players_max": int(players_max),
            "ping": latency_ms,
            "version": game_name or folder,
            "server_name": server_name,
            "map": map_name,
            "app_id": int(app_id),
            "bots": int(bots),
            "protocol": int(protocol),
        }

    @classmethod
    def query_server(cls, server):
        manual_maintenance = bool(
            server.get("maintenance")
            or str(server.get("status_override", "")).lower() == "maintenance"
            or str(server.get("status", "")).lower() == "maintenance"
        )

        if manual_maintenance:
            return {
                "status": "maintenance",
                "players_online": 0,
                "players_max": int(server.get("players_max", 0) or 0),
                "ping": None,
            }

        server_type = str(
            server.get("status_type")
            or server.get("type")
            or "minecraft"
        ).lower()

        try:
            if server_type in {"steam", "source", "ark"}:
                address = (
                    server.get("query_ip")
                    or server.get("query_address")
                    or server.get("server_ip")
                )
                return cls.query_source(address)

            address = server.get("server_ip") or server.get("address")
            return cls.query_minecraft(address)

        except Exception as exc:
            return {
                "status": "offline",
                "players_online": 0,
                "players_max": int(server.get("players_max", 0) or 0),
                "ping": None,
                "error": str(exc),
            }

    def run(self):
        while self._running:
            for server_id, server in list(self.servers.items()):
                if not self._running:
                    return
                self.status_ready.emit(server_id, self.query_server(server))

            for _ in range(self.interval_seconds * 10):
                if not self._running:
                    return
                self.msleep(100)

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
        self._svg_icon_cache = {}
        self.home_server_status_widgets = {}
        self.server_status_worker = None
        
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

        # Suavizado global del texto.
        app_font = QFont(self.montserrat, 10)
        app_font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        app_font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
        QApplication.instance().setFont(app_font)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle("D0cCtor's Hub")
        self.resize(1380, 820)
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
                "steam_appid": server.get("steam_appid"),
                "server_ip": server.get("server_ip"),
                "query_ip": server.get("query_ip"),
                "query_address": server.get("query_address"),
                "status_type": server.get("status_type"),
                "maintenance": server.get("maintenance", False),
                "status_override": server.get("status_override"),
                "players_max": server.get("players_max", 0)
            }
       

        central = QWidget()
        central.setObjectName("appRoot")
        central.setStyleSheet("#appRoot { background: #070b12; border-radius: 18px; }")
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
        sidebar.setFixedWidth(244)
        sidebar.setObjectName("sidebar")

        sidebar.setStyleSheet("""
        #sidebar {
            background: qlineargradient(
                x1:0, y1:0,
                x2:0, y2:1,
                stop:0 #0b1019,
                stop:0.55 #080d15,
                stop:1 #070b11
            );
            border-right: 1px solid rgba(108, 99, 255, 60);
            border-top-left-radius: 18px;
            border-bottom-left-radius: 18px;
        }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignTop)
        sidebar_layout.setContentsMargins(16, 20, 16, 16)
        sidebar_layout.setSpacing(12)

        # ===== LOGO IMAGEN =====
        pixmap = self.get_remote_asset("logo.png").scaled(
            112, 112,
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
        def create_nav_button(icon_kind, text):
            btn = QPushButton(f"   {text}")
            btn_font = QFont(self.montserrat, 13)
            btn_font.setWeight(QFont.Weight.Medium)
            btn.setFont(btn_font)
            btn.setFixedHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("navButton", True)
            btn.setProperty("iconKind", icon_kind)
            btn.setIcon(self.get_svg_icon(icon_kind, 21, "#a8b0c1"))
            btn.setIconSize(QSize(21, 21))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #a8b0c1;
                    border: 1px solid transparent;
                    border-radius: 14px;
                    text-align: left;
                    padding-left: 14px;
                    font-weight: 560;
                }
                QPushButton:hover {
                    background-color: rgba(108, 99, 255, 30);
                    color: #ffffff;
                    border-color: rgba(125, 115, 255, 90);
                }
            """)
            return btn

        menu_items = [
            ("home", "Inicio"),
            ("servers", "Servidores"),
            ("news", "Noticias"),
            ("settings", "Ajustes"),
            ("support", "Soporte"),
            ("store", "Tienda"),
        ]

        buttons = []
        for icon_kind, button_text in menu_items:
            btn = create_nav_button(icon_kind, button_text)
            sidebar_layout.addWidget(btn)
            buttons.append(btn)

        self.btn_inicio = buttons[0]
        self.btn_servers = buttons[1]
        self.btn_news = buttons[2]
        self.btn_settings = buttons[3]
        self.btn_support = buttons[4]
        self.btn_store = buttons[5]

        self.btn_inicio.clicked.connect(lambda: self.switch_page(0))
        self.btn_servers.clicked.connect(lambda: self.switch_page(1))
        self.btn_news.clicked.connect(lambda: self.switch_page(2))
        self.btn_settings.clicked.connect(lambda: self.switch_page(3))
        self.btn_support.clicked.connect(lambda: self.switch_page(4))
        self.btn_store.clicked.connect(lambda: self.switch_page(5))

        sidebar_layout.addSpacing(10)
        sidebar_layout.addStretch()

        # ===============================
        # STATUS PANEL (ABAJO SIDEBAR)
        # ===============================
        status_card = QFrame()
        status_card.setFixedHeight(96)
        status_card.setStyleSheet("""
            QFrame {
                background:qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0c141f,
                    stop:1 #091019
                );
                border:1px solid rgba(255,255,255,18);
                border-radius:14px;
            }
        """)

        status_layout = QHBoxLayout(status_card)
        status_layout.setContentsMargins(14, 14, 14, 14)
        status_layout.setSpacing(12)

        status_icon = QLabel()
        status_icon.setFixedSize(28, 28)
        status_icon.setPixmap(self.make_icon("check", 18, QColor("#5ee07a")))
        status_icon.setAlignment(Qt.AlignCenter)
        status_icon.setStyleSheet("""
            background:rgba(94,224,122,0.12);
            border:1px solid rgba(94,224,122,0.20);
            border-radius:14px;
        """)

        status_texts = QVBoxLayout()
        status_texts.setSpacing(1)

        status_title = QLabel("Launcher actualizado")
        status_title.setStyleSheet("color:#f0f3fb;font-size:12px;font-weight:700;border:none;")

        status_version = QLabel(f"Versión {APP_FULL_VERSION}")
        status_version.setStyleSheet("color:#7f8aa1;font-size:10px;border:none;")

        status_texts.addWidget(status_title)
        status_texts.addWidget(status_version)

        status_arrow = QLabel()
        status_arrow.setPixmap(self.make_icon("chevron", 14, QColor("#99a5bb")))
        status_arrow.setAlignment(Qt.AlignCenter)
        status_arrow.setStyleSheet("background:transparent;border:none;")

        status_layout.addWidget(status_icon)
        status_layout.addLayout(status_texts, 1)
        status_layout.addWidget(status_arrow)

        sidebar_layout.addWidget(status_card)

        # ===============================
        # MAIN CONTENT CON STACK
        # ===============================
        main_content = QFrame()
        main_content.setObjectName("mainContent")
        main_content.setStyleSheet("""
            #mainContent {
                background-color: #070b12;
                border-top-right-radius: 18px;
                border-bottom-right-radius: 18px;
                border-top: 1px solid rgba(255,255,255,18);
                border-right: 1px solid rgba(255,255,255,18);
                border-bottom: 1px solid rgba(255,255,255,18);
            }
        """)

        # Layout vertical principal del lado derecho
        content_wrapper = QVBoxLayout(main_content)
        content_wrapper.setContentsMargins(24, 10, 20, 14)
        content_wrapper.setSpacing(0)

        # ===============================
        # TOPBAR / CONTROLES DE VENTANA
        # ===============================
        topbar = QHBoxLayout()
        topbar.setContentsMargins(0, 0, 0, 8)
        topbar.setSpacing(8)
        topbar.addStretch()

        notify_btn = QPushButton("♢")
        notify_btn.setToolTip("Notificaciones")
        notify_btn.setFixedSize(36, 36)
        notify_btn.setCursor(Qt.PointingHandCursor)
        notify_btn.setStyleSheet("""
            QPushButton { background:transparent; color:#a8b0c1; border:none; border-radius:9px; font-size:18px; }
            QPushButton:hover { background:rgba(91,108,255,32); color:white; }
        """)

        profile = QFrame()
        profile.setObjectName("profileTop")
        profile.setFixedSize(192, 42)
        profile.setStyleSheet("""
            #profileTop { background:#0d141f; border:1px solid rgba(255,255,255,25); border-radius:12px; }
        """)
        profile_layout = QHBoxLayout(profile)
        profile_layout.setContentsMargins(10, 5, 12, 5)
        profile_layout.setSpacing(9)
        avatar = QLabel()
        avatar.setFixedSize(30, 30)
        avatar_pm = self.get_remote_asset("logo.png")
        if avatar_pm and not avatar_pm.isNull():
            avatar.setPixmap(avatar_pm.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        avatar.setAlignment(Qt.AlignCenter)
        profile_text = QVBoxLayout()
        profile_text.setSpacing(0)
        profile_name = QLabel("D0cCtor")
        profile_name.setStyleSheet("color:white; font-weight:700; font-size:13px; border:none;")
        profile_status = QLabel("●  En línea")
        profile_status.setStyleSheet("color:#49d17d; font-size:10px; border:none;")
        profile_text.addWidget(profile_name)
        profile_text.addWidget(profile_status)
        profile_layout.addWidget(avatar)
        profile_layout.addLayout(profile_text)
        profile_layout.addStretch()
        profile_layout.addWidget(QLabel("⌄"))

        def window_button(icon_kind, hover_bg):
            btn = QPushButton()
            btn.setFixedSize(38, 38)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(QIcon(self.make_icon(icon_kind, 15, QColor("#b8c0d0"))))
            btn.setIconSize(QSize(15, 15))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:transparent;
                    border:none;
                    border-radius:9px;
                }}
                QPushButton:hover {{
                    background:{hover_bg};
                }}
                QPushButton:pressed {{
                    background:rgba(255,255,255,30);
                }}
            """)
            return btn

        min_btn = window_button("window_minimize", "rgba(255,255,255,18)")
        max_btn = window_button("window_maximize", "rgba(255,255,255,18)")
        close_btn = window_button("window_close", "#d83b45")
        min_btn.clicked.connect(self.showMinimized)
        max_btn.clicked.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        close_btn.clicked.connect(self.close)

        topbar.addWidget(notify_btn)
        topbar.addWidget(profile)
        topbar.addSpacing(10)
        topbar.addWidget(min_btn)
        topbar.addWidget(max_btn)
        topbar.addWidget(close_btn)
        content_wrapper.addLayout(topbar)

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
        footer_label.setStyleSheet("color:#596174;")
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
        self.store_page = self.create_store_page()

        # Agregar páginas al stack
        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.servers_page)
        self.stack.addWidget(self.news_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.support_page)
        self.stack.addWidget(self.store_page)
        self.refresh_server_buttons()
        self.auto_detect_paths()
        self.start_server_status_monitor()

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
    # REAL SERVER STATUS
    # =====================================================
    def start_server_status_monitor(self):
        if self.server_status_worker is not None:
            return

        self.server_status_worker = ServerStatusWorker(
            self.servers_data,
            interval_seconds=30
        )
        self.server_status_worker.status_ready.connect(
            self.update_home_server_status
        )
        self.server_status_worker.start()

    def update_home_server_status(self, server_name, result):
        widgets = self.home_server_status_widgets.get(server_name)
        if not widgets:
            return

        status = str(result.get("status", "offline")).lower()

        status_styles = {
            "online": ("En línea", "#55dc7a"),
            "offline": ("Offline", "#ff6674"),
            "maintenance": ("Mantenimiento", "#f5bf57"),
        }

        status_text, color = status_styles.get(
            status,
            status_styles["offline"]
        )

        widgets["state_dot"].setText("●")
        widgets["state_dot"].setStyleSheet(
            f"color:{color};font-size:10px;border:none;"
        )
        widgets["state_label"].setText(status_text)
        widgets["state_label"].setStyleSheet(
            f"color:{color};font-size:10px;font-weight:700;border:none;"
        )

        online = int(result.get("players_online", 0) or 0)
        maximum = int(result.get("players_max", 0) or 0)
        widgets["players_label"].setText(
            f"{online}/{maximum}" if maximum > 0 else str(online)
        )

        ping = result.get("ping")
        if status == "online" and ping is not None:
            ping_value = int(ping)

            if ping_value < 70:
                ping_color = "#59da72"
            elif ping_value <= 200:
                ping_color = "#f5bf57"
            else:
                ping_color = "#ff6674"

            widgets["ping_label"].setText(f"{ping_value}ms")
            widgets["ping_label"].setStyleSheet(
                f"color:{ping_color};"
                "font-size:10px;"
                "font-weight:700;"
                "border:none;"
            )
        else:
            widgets["ping_label"].setText("—")
            widgets["ping_label"].setStyleSheet(
                "color:#687286;font-size:10px;border:none;"
            )

        detected_version = str(result.get("version", "") or "").strip()
        if detected_version:
            widgets["version_label"].setText(detected_version)

    def closeEvent(self, event):
        worker = getattr(self, "server_status_worker", None)
        if worker is not None:
            worker.stop()
            worker.wait(1500)

        super().closeEvent(event)

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
    # ICONOS SVG DEL LAUNCHER
    # ===============================
    def get_svg_icon(self, icon_name, size=21, color="#a8b0c1"):
        cache_key = (icon_name, size, color)
        cached = self._svg_icon_cache.get(cache_key)
        if cached is not None:
            return cached

        svg_data = None
        local_path = resource_path(os.path.join("icons", f"{icon_name}.svg"))

        try:
            if os.path.exists(local_path):
                with open(local_path, "rb") as svg_file:
                    svg_data = svg_file.read()
            else:
                remote_url = (
                    "https://raw.githubusercontent.com/"
                    "D0cCto0r/d0cctors-hub/main/remote/assets/icons/"
                    f"{icon_name}.svg"
                )
                response = requests.get(remote_url, timeout=8)
                if response.status_code == 200:
                    svg_data = response.content
        except Exception as exc:
            print(f"No se pudo cargar el icono SVG {icon_name}:", exc)

        if not svg_data:
            fallback = QIcon(self.make_icon(icon_name, size, QColor(color), filled=True))
            self._svg_icon_cache[cache_key] = fallback
            return fallback

        try:
            svg_text = svg_data.decode("utf-8")
            svg_text = svg_text.replace('fill="#000000"', f'fill="{color}"')
            svg_text = svg_text.replace("fill='#000000'", f"fill='{color}'")
            svg_text = svg_text.replace('stroke="#000000"', f'stroke="{color}"')
            svg_text = svg_text.replace("stroke='#000000'", f"stroke='{color}'")

            renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            renderer.render(painter)
            painter.end()

            icon = QIcon(pixmap)
            self._svg_icon_cache[cache_key] = icon
            return icon

        except Exception as exc:
            print(f"No se pudo renderizar el icono SVG {icon_name}:", exc)
            fallback = QIcon(self.make_icon(icon_name, size, QColor(color), filled=True))
            self._svg_icon_cache[cache_key] = fallback
            return fallback

    def update_nav_icon(self, button, active=False):
        icon_name = button.property("iconKind")
        if not icon_name:
            return

        color = "#ffffff" if active else "#a8b0c1"
        button.setIcon(self.get_svg_icon(icon_name, 21, color))
        button.setIconSize(QSize(21, 21))

    # ===============================
    # ICONOS VECTORIALES DE RESPALDO
    # ===============================
    def make_icon(self, kind, size=18, color=None, filled=False):
        """Crea iconos limpios sin depender de caracteres Unicode."""
        color = color or QColor("#ffffff")
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        pen = QPen(color)
        pen.setWidthF(max(1.6, size * 0.095))
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(color) if filled else Qt.NoBrush)

        if kind == "home":
            painter.drawLine(QPointF(size * 0.22, size * 0.45), QPointF(size * 0.50, size * 0.21))
            painter.drawLine(QPointF(size * 0.78, size * 0.45), QPointF(size * 0.50, size * 0.21))
            painter.drawLine(QPointF(size * 0.30, size * 0.42), QPointF(size * 0.30, size * 0.78))
            painter.drawLine(QPointF(size * 0.70, size * 0.42), QPointF(size * 0.70, size * 0.78))
            painter.drawLine(QPointF(size * 0.30, size * 0.78), QPointF(size * 0.70, size * 0.78))
            painter.drawLine(QPointF(size * 0.44, size * 0.78), QPointF(size * 0.44, size * 0.57))
            painter.drawLine(QPointF(size * 0.56, size * 0.78), QPointF(size * 0.56, size * 0.57))

        elif kind == "servers":
            for y in (0.28, 0.50, 0.72):
                painter.drawRoundedRect(QRectF(size * 0.20, size * y, size * 0.60, size * 0.10), size * 0.05, size * 0.05)
            for y in (0.33, 0.55, 0.77):
                painter.drawPoint(QPointF(size * 0.28, size * y))

        elif kind == "news":
            painter.drawRoundedRect(QRectF(size * 0.20, size * 0.20, size * 0.60, size * 0.60), size * 0.08, size * 0.08)
            painter.drawLine(QPointF(size * 0.32, size * 0.35), QPointF(size * 0.68, size * 0.35))
            painter.drawLine(QPointF(size * 0.32, size * 0.49), QPointF(size * 0.68, size * 0.49))
            painter.drawLine(QPointF(size * 0.32, size * 0.63), QPointF(size * 0.56, size * 0.63))

        elif kind == "settings":
            painter.drawEllipse(QRectF(size * 0.34, size * 0.34, size * 0.32, size * 0.32))
            for p1, p2 in [
                (QPointF(0.50, 0.12), QPointF(0.50, 0.26)),
                (QPointF(0.50, 0.74), QPointF(0.50, 0.88)),
                (QPointF(0.12, 0.50), QPointF(0.26, 0.50)),
                (QPointF(0.74, 0.50), QPointF(0.88, 0.50)),
                (QPointF(0.23, 0.23), QPointF(0.32, 0.32)),
                (QPointF(0.68, 0.68), QPointF(0.77, 0.77)),
                (QPointF(0.68, 0.32), QPointF(0.77, 0.23)),
                (QPointF(0.23, 0.77), QPointF(0.32, 0.68)),
            ]:
                painter.drawLine(QPointF(size * p1.x(), size * p1.y()), QPointF(size * p2.x(), size * p2.y()))

        elif kind == "support":
            painter.drawArc(int(size * 0.18), int(size * 0.20), int(size * 0.64), int(size * 0.56), 0, 180 * 16)
            painter.drawLine(QPointF(size * 0.22, size * 0.46), QPointF(size * 0.22, size * 0.70))
            painter.drawLine(QPointF(size * 0.78, size * 0.46), QPointF(size * 0.78, size * 0.70))
            painter.drawLine(QPointF(size * 0.22, size * 0.70), QPointF(size * 0.32, size * 0.70))
            painter.drawLine(QPointF(size * 0.68, size * 0.70), QPointF(size * 0.78, size * 0.70))
            painter.drawLine(QPointF(size * 0.40, size * 0.78), QPointF(size * 0.60, size * 0.78))

        elif kind == "store":
            painter.drawRoundedRect(QRectF(size * 0.20, size * 0.34, size * 0.60, size * 0.42), size * 0.08, size * 0.08)
            painter.drawLine(QPointF(size * 0.32, size * 0.34), QPointF(size * 0.38, size * 0.20))
            painter.drawLine(QPointF(size * 0.68, size * 0.34), QPointF(size * 0.62, size * 0.20))
            painter.drawLine(QPointF(size * 0.38, size * 0.20), QPointF(size * 0.62, size * 0.20))

        elif kind == "check":
            painter.drawLine(QPointF(size * 0.22, size * 0.54), QPointF(size * 0.42, size * 0.73))
            painter.drawLine(QPointF(size * 0.42, size * 0.73), QPointF(size * 0.79, size * 0.28))

        elif kind == "play":
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            painter.drawPolygon(QPolygonF([
                QPointF(size * 0.30, size * 0.19),
                QPointF(size * 0.30, size * 0.81),
                QPointF(size * 0.78, size * 0.50),
            ]))

        elif kind == "download":
            painter.drawLine(QPointF(size * 0.50, size * 0.13), QPointF(size * 0.50, size * 0.61))
            painter.drawLine(QPointF(size * 0.31, size * 0.45), QPointF(size * 0.50, size * 0.65))
            painter.drawLine(QPointF(size * 0.69, size * 0.45), QPointF(size * 0.50, size * 0.65))
            painter.drawLine(QPointF(size * 0.21, size * 0.84), QPointF(size * 0.79, size * 0.84))
            painter.drawLine(QPointF(size * 0.21, size * 0.84), QPointF(size * 0.21, size * 0.70))
            painter.drawLine(QPointF(size * 0.79, size * 0.84), QPointF(size * 0.79, size * 0.70))

        elif kind == "heart":
            path = QPainterPath()
            path.moveTo(size * 0.50, size * 0.82)
            path.cubicTo(size * 0.08, size * 0.58, size * 0.16, size * 0.17, size * 0.38, size * 0.22)
            path.cubicTo(size * 0.47, size * 0.24, size * 0.50, size * 0.34, size * 0.50, size * 0.34)
            path.cubicTo(size * 0.50, size * 0.34, size * 0.53, size * 0.24, size * 0.62, size * 0.22)
            path.cubicTo(size * 0.84, size * 0.17, size * 0.92, size * 0.58, size * 0.50, size * 0.82)
            painter.setBrush(QBrush(color) if filled else Qt.NoBrush)
            painter.drawPath(path)

        elif kind == "comment":
            bubble = QRectF(size * 0.15, size * 0.16, size * 0.69, size * 0.51)
            painter.drawRoundedRect(bubble, size * 0.11, size * 0.11)
            painter.drawLine(QPointF(size * 0.37, size * 0.67), QPointF(size * 0.31, size * 0.84))
            painter.drawLine(QPointF(size * 0.31, size * 0.84), QPointF(size * 0.51, size * 0.69))

        elif kind == "chevron":
            painter.drawLine(QPointF(size * 0.36, size * 0.22), QPointF(size * 0.64, size * 0.50))
            painter.drawLine(QPointF(size * 0.36, size * 0.78), QPointF(size * 0.64, size * 0.50))

        elif kind == "window_minimize":
            painter.setPen(QPen(color, max(1.7, size * 0.11), Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                QPointF(size * 0.22, size * 0.66),
                QPointF(size * 0.78, size * 0.66)
            )

        elif kind == "window_maximize":
            painter.setPen(QPen(color, max(1.5, size * 0.10), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(
                QRectF(size * 0.22, size * 0.20, size * 0.56, size * 0.56),
                size * 0.04,
                size * 0.04
            )

        elif kind == "window_close":
            painter.setPen(QPen(color, max(1.7, size * 0.11), Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(
                QPointF(size * 0.24, size * 0.24),
                QPointF(size * 0.76, size * 0.76)
            )
            painter.drawLine(
                QPointF(size * 0.76, size * 0.24),
                QPointF(size * 0.24, size * 0.76)
            )

        elif kind == "players":
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawEllipse(
                QRectF(size * 0.34, size * 0.12, size * 0.32, size * 0.32)
            )
            painter.drawRoundedRect(
                QRectF(size * 0.22, size * 0.52, size * 0.56, size * 0.34),
                size * 0.12,
                size * 0.12
            )

        painter.end()
        return pixmap
        
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
    def create_news_card(self, news_item, compact=False):
        """Card de noticias compartida por Inicio y la pestaña Noticias."""
        card = QFrame()
        card.setObjectName("newsFeedCard")
        card.setFixedHeight(142 if compact else 188)
        card.setMinimumWidth(620 if compact else 700)
        card.setStyleSheet("""
            #newsFeedCard {
                background:qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #151c27,
                    stop:1 #0e141d
                );
                border:1px solid rgba(255,255,255,22);
                border-radius:14px;
            }
            #newsFeedCard:hover {
                border-color:rgba(125,115,255,120);
                background:#171f2b;
            }
        """)

        root = QHBoxLayout(card)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card_height = 142 if compact else 188

        # Noticias destacadas conserva una miniatura horizontal grande.
        # Solo las esquinas exteriores izquierdas siguen redondeadas.
        image_width = 285 if compact else 340

        pixmap = self.get_remote_pixmap(news_item.get("image"))
        image = RoundedImage(
            pixmap,
            radius=13,
            round_mode="left"
        )
        image.setFixedSize(image_width, card_height)
        image.setStyleSheet("background:transparent;border:none;")
        root.addWidget(image)

        content = QVBoxLayout()
        content.setContentsMargins(17, 13, 15, 12)
        content.setSpacing(5)

        title_text = news_item.get("title", "Novedades")
        desc_text = news_item.get("description", "")
        badge_text = str(
            news_item.get("tag")
            or news_item.get("category")
            or ("EVENTO" if "evento" in title_text.lower() else "ACTUALIZACIÓN")
        ).upper()
        time_text = str(news_item.get("time_ago", "Novedad reciente"))
        likes_value = int(news_item.get("likes", 0) or 0)
        comments_value = int(news_item.get("comments", 0) or 0)

        is_event = "EVENTO" in badge_text or "EVENT" in badge_text
        badge_color = "#c58cff" if is_event else "#8580ff"
        badge_background = "rgba(174,103,255,38)" if is_event else "rgba(108,99,255,42)"
        badge_border = "rgba(197,140,255,105)" if is_event else "rgba(133,128,255,105)"

        top = QHBoxLayout()
        top.setSpacing(8)

        badge = QLabel(badge_text)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            color:{badge_color};
            background:{badge_background};
            border:1px solid {badge_border};
            border-radius:7px;
            padding:3px 7px;
            font-size:9px;
            font-weight:800;
        """)

        when = QLabel(time_text)
        when.setStyleSheet("color:#8c96aa;font-size:9px;border:none;")

        top.addWidget(badge, alignment=Qt.AlignLeft)
        top.addWidget(when, alignment=Qt.AlignVCenter)
        top.addStretch()

        title = QLabel(title_text)
        title.setWordWrap(True)
        title.setMaximumHeight(42 if compact else 48)
        title.setStyleSheet("""
            color:#f3f5fb;
            font-size:12px;
            font-weight:800;
            border:none;
        """)

        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setMaximumHeight(34 if compact else 52)
        desc.setStyleSheet("""
            color:#9fa8b9;
            font-size:10px;
            border:none;
        """)

        actions = QHBoxLayout()
        actions.setSpacing(2)

        like_btn = QPushButton()
        like_btn.setCheckable(True)
        like_btn.setCursor(Qt.PointingHandCursor)
        like_btn.setFixedSize(28, 26)
        like_btn.setIcon(QIcon(self.make_icon("heart", 14, QColor("#8994aa"))))
        like_btn.setIconSize(QSize(14, 14))
        like_btn.setToolTip("Me gusta")
        like_btn.setStyleSheet("""
            QPushButton { background:transparent; border:none; border-radius:8px; }
            QPushButton:hover { background:rgba(255,255,255,14); }
            QPushButton:checked { background:rgba(255,86,126,24); }
        """)

        like_count = QLabel(str(likes_value))
        like_count.setMinimumWidth(24)
        like_count.setStyleSheet("color:#8c96aa;font-size:9px;border:none;")

        def toggle_like(checked):
            like_btn.setIcon(QIcon(self.make_icon(
                "heart", 14,
                QColor("#ff668c") if checked else QColor("#8994aa"),
                filled=checked
            )))
            like_count.setText(str(likes_value + (1 if checked else 0)))

        like_btn.toggled.connect(toggle_like)

        comment_btn = QPushButton()
        comment_btn.setCursor(Qt.PointingHandCursor)
        comment_btn.setFixedSize(28, 26)
        comment_btn.setIcon(QIcon(self.make_icon("comment", 14, QColor("#8994aa"))))
        comment_btn.setIconSize(QSize(14, 14))
        comment_btn.setToolTip("Ver comentarios")
        comment_btn.setStyleSheet("""
            QPushButton { background:transparent; border:none; border-radius:8px; }
            QPushButton:hover { background:rgba(255,255,255,14); }
        """)
        comment_btn.clicked.connect(lambda checked=False: self.switch_page(2))

        comment_count = QLabel(str(comments_value))
        comment_count.setMinimumWidth(24)
        comment_count.setStyleSheet("color:#8c96aa;font-size:9px;border:none;")

        open_btn = QPushButton()
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setFixedSize(30, 28)
        open_btn.setIcon(QIcon(self.make_icon("chevron", 15, QColor("#c8d0df"))))
        open_btn.setIconSize(QSize(15, 15))
        open_btn.setToolTip("Abrir noticia")
        open_btn.setStyleSheet("""
            QPushButton { background:transparent; border:none; border-radius:9px; }
            QPushButton:hover { background:rgba(255,255,255,14); }
        """)
        open_btn.clicked.connect(lambda checked=False: self.switch_page(2))

        actions.addWidget(like_btn)
        actions.addWidget(like_count)
        actions.addSpacing(5)
        actions.addWidget(comment_btn)
        actions.addWidget(comment_count)
        actions.addStretch()
        actions.addWidget(open_btn)

        content.addLayout(top)
        content.addWidget(title)
        content.addWidget(desc)
        content.addStretch()
        content.addLayout(actions)

        root.addLayout(content, 1)
        return card

    # ===============================
    # HOME PAGE
    # ===============================
    def create_home_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background:transparent; border:none; }")

        page = QWidget()
        page.setObjectName("homePage")
        page.setStyleSheet("#homePage { background:transparent; }")
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setContentsMargins(4, 0, 4, 2)

        # Servidor principal: prioriza Minecraft
        primary_name = next((name for name, data in self.servers_data.items() if data.get("type") != "steam"), None)
        if primary_name is None and self.servers_data:
            primary_name = next(iter(self.servers_data))
        primary = self.servers_data.get(primary_name, {}) if primary_name else {}
        self.home_primary_name = primary_name

        # HERO: una sola imagen de fondo
        hero = QFrame()
        hero.setObjectName("hero")
        hero.setFixedHeight(238)
        hero.setStyleSheet("""
            #hero {
                background:#0b111a;
                border:1px solid rgba(91,108,255,70);
                border-radius:16px;
            }
        """)

        hero_stack = QStackedLayout(hero)
        hero_stack.setStackingMode(QStackedLayout.StackAll)
        hero_stack.setContentsMargins(0, 0, 0, 0)

        hero_pm = self.get_remote_asset("hero_banner.png")
        if (not hero_pm or hero_pm.isNull()) and self.news_data:
            hero_pm = self.get_remote_pixmap(self.news_data[0].get("image"))

        hero_bg = RoundedImage(hero_pm, radius=16)
        hero_bg.setMinimumHeight(238)
        hero_bg.setMaximumHeight(238)
        hero_bg.setStyleSheet("background:transparent;border:none;")
        hero_stack.addWidget(hero_bg)

        hero_overlay = QFrame()
        hero_overlay.setObjectName("heroOverlay")
        hero_overlay.setStyleSheet("""
            #heroOverlay {
                background:qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(5,9,18,248),
                    stop:0.36 rgba(5,9,18,218),
                    stop:0.65 rgba(5,9,18,92),
                    stop:1 rgba(5,9,18,8)
                );
                border-radius:16px;
            }
        """)
        hero_stack.addWidget(hero_overlay)

        # En StackAll, el widget actual queda por encima del resto.
        # Marcamos el overlay como actual para que el texto y los botones
        # aparezcan delante de la imagen de fondo.
        hero_stack.setCurrentWidget(hero_overlay)
        hero_bg.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        hero_overlay.raise_()

        hero_layout = QHBoxLayout(hero_overlay)
        hero_layout.setContentsMargins(38, 25, 30, 23)

        left = QVBoxLayout()
        left.setSpacing(5)

        eyebrow = QLabel("D0CCTOR'S HUB")
        eyebrow.setStyleSheet(
            "color:#8993ff;font-size:10px;font-weight:800;"
            "letter-spacing:2px;border:none;"
        )

        hero_title = QLabel(
            "EXPLORÁ.<br>CONSTRUÍ. "
            "<span style='color:#7580ff'>SOBREVIVÍ.</span>"
        )
        hero_title.setTextFormat(Qt.RichText)
        hero_title.setWordWrap(True)
        hero_title.setMaximumWidth(540)
        hero_title.setFont(QFont(self.montserrat, 23, QFont.Weight.Bold))
        hero_title.setStyleSheet("color:white;border:none;")

        hero_sub = QLabel(
            "Jugá, instalá y actualizá tus servidores desde un único launcher."
        )
        hero_sub.setWordWrap(True)
        hero_sub.setMaximumWidth(470)
        hero_sub.setStyleSheet("color:#b2bdd1;font-size:11px;border:none;")

        actions = QHBoxLayout()
        actions.setSpacing(11)

        play_btn = QPushButton("JUGAR")
        play_btn.setFixedSize(178, 48)
        play_btn.setCursor(Qt.PointingHandCursor)
        play_btn.setIcon(QIcon(self.make_icon("play", 19, QColor("#ffffff"), filled=True)))
        play_btn.setIconSize(QSize(19, 19))
        play_btn.setStyleSheet("""
            QPushButton {
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #655cff,
                    stop:1 #8068ff
                );
                color:white;
                border:1px solid rgba(164,155,255,150);
                border-radius:13px;
                font-size:14px;
                font-weight:800;
                padding:0 16px;
            }
            QPushButton:hover { background:#746cff; }
            QPushButton:pressed { background:#5951d9; }
            QPushButton:disabled {
                background:#303750;
                color:#7f899e;
                border-color:rgba(255,255,255,18);
            }
        """)

        install_btn = QPushButton("INSTALAR")
        install_btn.setFixedSize(178, 48)
        install_btn.setCursor(Qt.PointingHandCursor)
        install_btn.setIcon(QIcon(self.make_icon("download", 19, QColor("#f1f3fa"))))
        install_btn.setIconSize(QSize(19, 19))
        install_btn.setStyleSheet("""
            QPushButton {
                background:rgba(8,13,23,225);
                color:#f1f3fa;
                border:1px solid rgba(255,255,255,38);
                border-radius:13px;
                font-size:13px;
                font-weight:750;
                padding:0 16px;
            }
            QPushButton:hover {
                border-color:#6f7aff;
                background:rgba(25,32,60,235);
            }
            QPushButton:pressed { background:#151d35; }
            QPushButton:disabled {
                color:#7f899e;
                background:rgba(20,25,38,215);
            }
        """)

        self.home_play_btn = play_btn
        self.home_install_btn = install_btn

        installed = bool(primary.get("installed"))
        needs_update = bool(primary.get("needs_update"))
        play_btn.setEnabled(installed and not needs_update)
        install_btn.setText(
            "ACTUALIZAR" if needs_update
            else ("INSTALADO" if installed else "INSTALAR")
        )
        install_btn.setEnabled((not installed) or needs_update)

        if primary_name:
            play_btn.clicked.connect(
                lambda checked=False, n=primary_name: self.handle_server_action(n)
            )
            install_btn.clicked.connect(
                lambda checked=False, n=primary_name: self.handle_server_action(n)
            )

        actions.addWidget(play_btn)
        actions.addWidget(install_btn)
        actions.addStretch()

        left.addWidget(eyebrow)
        left.addWidget(hero_title)
        left.addWidget(hero_sub)
        left.addSpacing(8)
        left.addLayout(actions)
        left.addStretch()

        hero_layout.addLayout(left, 5)
        hero_layout.addStretch(3)
        layout.addWidget(hero)

        # SERVIDORES
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color:#49d17d;font-size:13px;border:none;")
        htitle = QLabel("ESTADO DE SERVIDORES")
        htitle.setFont(QFont(self.montserrat, 11, QFont.Weight.Bold))
        htitle.setStyleSheet("color:#f3f5fb;letter-spacing:1px;border:none;")
        hsub = QLabel("●  Todos los sistemas operativos")
        hsub.setStyleSheet("color:#687086;font-size:10px;border:none;")
        view_all = QPushButton("VER TODOS  ›")
        view_all.setCursor(Qt.PointingHandCursor)
        view_all.setStyleSheet("QPushButton{background:#0b111a;color:#c7cee0;border:1px solid rgba(255,255,255,24);border-radius:8px;padding:7px 13px;font-weight:650;} QPushButton:hover{border-color:#6572ff;color:white;}")
        view_all.clicked.connect(lambda: self.switch_page(1))
        header.addWidget(dot)
        header.addWidget(htitle)
        header.addWidget(hsub)
        header.addStretch()
        header.addWidget(view_all)
        layout.addLayout(header)

        cards = QHBoxLayout()
        cards.setSpacing(10)

        for server_name, data in list(self.servers_data.items())[:4]:
            # Los valores reales llegan desde ServerStatusWorker.
            server_status = "maintenance" if data.get("maintenance") else "offline"
            players_online = 0
            players_max = int(data.get("players_max", 0) or 0)
            ping = None

            status_styles = {
                "online": {
                    "text": "En línea",
                    "color": "#55dc7a",
                    "dot": "#55dc7a",
                },
                "offline": {
                    "text": "Offline",
                    "color": "#ff6674",
                    "dot": "#ff6674",
                },
                "maintenance": {
                    "text": "Mantenimiento",
                    "color": "#f5bf57",
                    "dot": "#f5bf57",
                },
            }
            status_info = status_styles.get(
                server_status,
                status_styles["offline"]
            )

            card = QFrame()
            card.setObjectName("homeServerCard")
            card.setFixedSize(250, 84)
            card.setStyleSheet("""
                #homeServerCard {
                    background:qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #121923,
                        stop:1 #0d131c
                    );
                    border:1px solid rgba(255,255,255,22);
                    border-radius:13px;
                }
                #homeServerCard:hover {
                    border-color:rgba(125,115,255,115);
                    background:#151d29;
                }
            """)

            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(10, 9, 10, 9)
            card_layout.setSpacing(9)

            icon = QLabel()
            icon.setFixedSize(60, 60)
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("""
                background:#111827;
                border:1px solid rgba(255,255,255,18);
                border-radius:10px;
            """)

            pm = self.get_remote_pixmap(data.get("image_url"))
            if pm and not pm.isNull():
                icon.setPixmap(
                    pm.scaled(
                        54, 54,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )

            content_widget = QWidget()
            content_widget.setFixedHeight(60)
            content_widget.setStyleSheet("background:transparent;border:none;")

            content = QVBoxLayout(content_widget)
            content.setSpacing(0)
            content.setContentsMargins(0, 0, 0, 0)

            header_row = QHBoxLayout()
            header_row.setSpacing(6)
            header_row.setContentsMargins(0, 0, 0, 0)

            title_block = QVBoxLayout()
            title_block.setSpacing(0)

            name = QLabel(server_name)
            name.setStyleSheet("""
                color:#f3f5fb;
                font-size:12px;
                font-weight:750;
                border:none;
            """)

            version_text = str(
                data.get("minecraft_version")
                or data.get("version")
                or "Steam"
            )
            version = QLabel(version_text)
            version.setStyleSheet("""
                color:#7d8799;
                font-size:10px;
                border:none;
            """)

            title_block.addWidget(name)
            title_block.addWidget(version)

            players_box = QHBoxLayout()
            players_box.setSpacing(4)
            players_box.setContentsMargins(0, 1, 0, 0)

            players_icon = QLabel()
            players_icon.setFixedSize(14, 14)
            players_icon.setPixmap(
                self.make_icon("players", 13, QColor("#a9b2c5"))
            )
            players_icon.setAlignment(Qt.AlignCenter)
            players_icon.setStyleSheet("background:transparent;border:none;")

            if players_max > 0:
                players_text = f"{players_online}/{players_max}"
            elif server_status == "maintenance":
                players_text = "0/0"
            else:
                players_text = str(players_online)

            players_label = QLabel(players_text)
            players_label.setStyleSheet("""
                color:#aab3c5;
                font-size:10px;
                font-weight:600;
                border:none;
            """)

            players_box.addWidget(players_icon)
            players_box.addWidget(players_label)

            header_row.addLayout(title_block)
            header_row.addStretch()
            header_row.addLayout(players_box)

            footer_row = QHBoxLayout()
            footer_row.setSpacing(4)
            footer_row.setContentsMargins(0, 0, 0, 0)

            state_dot = QLabel("●")
            state_dot.setStyleSheet(
                f"color:{status_info['dot']};"
                "font-size:10px;border:none;"
            )

            state_label = QLabel(status_info["text"])
            state_label.setStyleSheet(
                f"color:{status_info['color']};"
                "font-size:10px;font-weight:700;border:none;"
            )

            if server_status == "online" and ping is not None:
                ping_value = int(ping)
                ping_color = (
                    "#59da72" if ping_value < 70
                    else "#f5bf57" if ping_value <= 200
                    else "#ff6674"
                )

                ping_label = QLabel(f"{ping_value}ms")
                ping_label.setStyleSheet(f"""
                    color:{ping_color};
                    font-size:10px;
                    font-weight:700;
                    border:none;
                """)
            else:
                ping_label = QLabel("—")
                ping_label.setStyleSheet("""
                    color:#687286;
                    font-size:10px;
                    border:none;
                """)

            footer_row.addWidget(state_dot)
            footer_row.addWidget(state_label)
            footer_row.addStretch()
            footer_row.addWidget(ping_label)

            content.addLayout(header_row)
            content.addStretch()
            content.addLayout(footer_row)

            card_layout.addWidget(icon, alignment=Qt.AlignVCenter)
            card_layout.addWidget(content_widget, 1, alignment=Qt.AlignVCenter)

            self.home_server_status_widgets[server_name] = {
                "state_dot": state_dot,
                "state_label": state_label,
                "players_label": players_label,
                "ping_label": ping_label,
                "version_label": version,
            }

            cards.addWidget(card)

        cards.addStretch()
        layout.addLayout(cards)

        # NOTICIAS + ACTIVIDAD RECIENTE
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        news_col = QVBoxLayout()
        news_col.setSpacing(5)
        news_head = QHBoxLayout()
        news_head.setContentsMargins(0, 10, 0, 0)
        news_title = QLabel("NOTICIAS DESTACADAS")
        news_title.setFont(QFont(self.montserrat, 11, QFont.Weight.Bold))
        news_title.setStyleSheet("color:#f3f5fb;letter-spacing:1px;border:none;")
        news_more = QPushButton("VER TODAS  ›")
        news_more.setCursor(Qt.PointingHandCursor)
        news_more.setStyleSheet("QPushButton{background:#0b111a;color:#c7cee0;border:1px solid rgba(255,255,255,24);border-radius:8px;padding:7px 13px;font-weight:650;} QPushButton:hover{border-color:#6572ff;color:white;}")
        news_more.clicked.connect(lambda: self.switch_page(2))
        news_head.addWidget(news_title)
        news_head.addStretch()
        news_head.addWidget(news_more, alignment=Qt.AlignBottom)
        news_col.addLayout(news_head)

        if self.news_data:
            for item in self.news_data[:2]:
                news_col.addWidget(self.create_news_card(item, compact=True))

        activity = QFrame()
        activity.setObjectName("activityPanel")
        activity.setMinimumWidth(230)
        activity.setMaximumWidth(260)
        activity.setMinimumHeight(325)
        activity.setMaximumHeight(325)
        activity.setStyleSheet("#activityPanel{background:#0d131e;border:1px solid rgba(255,255,255,22);border-radius:14px;}")
        act = QVBoxLayout(activity)
        act.setContentsMargins(16,12,16,12)
        act.setSpacing(8)
        atitle = QLabel("ACTIVIDAD RECIENTE")
        atitle.setStyleSheet("color:#f3f5fb;font-size:11px;font-weight:800;letter-spacing:1px;border:none;")
        act.addWidget(atitle)
        activities = [
            ("●", "ShibuyaSMP disponible", "Servidor online"),
            ("●", "Modpack verificado", "Archivos sincronizados"),
            ("●", "ARK conectado", "Steam listo"),
            ("●", "Launcher actualizado", f"Build {APP_BUILD}"),
        ]
        for symbol, title_text, detail in activities:
            row = QHBoxLayout()
            ico = QLabel(symbol)
            ico.setFixedSize(22,22)
            ico.setAlignment(Qt.AlignCenter)
            ico.setStyleSheet("background:rgba(73,209,125,35);color:#49d17d;border-radius:12px;border:none;")
            texts = QVBoxLayout()
            texts.setSpacing(0)
            t = QLabel(title_text)
            t.setStyleSheet("color:#dce2ef;font-size:10px;font-weight:650;border:none;")
            d = QLabel(detail)
            d.setStyleSheet("color:#747e91;font-size:9px;border:none;")
            texts.addWidget(t)
            texts.addWidget(d)
            row.addWidget(ico)
            row.addLayout(texts)
            act.addLayout(row)
        act.addStretch()

        activity_wrapper = QVBoxLayout()
        activity_wrapper.setContentsMargins(0, 10, 0, 0)
        activity_wrapper.addWidget(activity)
        activity_wrapper.addStretch()

        bottom.addLayout(news_col,9)
        bottom.addLayout(activity_wrapper,1)
        layout.addLayout(bottom)
        layout.addStretch()

        scroll.setWidget(page)
        return scroll


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

        header_card = QFrame()
        header_card.setObjectName("newsPageHeader")
        header_card.setStyleSheet("""
            #newsPageHeader {
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #131b2a,
                    stop:1 #0d1420
                );
                border:1px solid rgba(91,108,255,55);
                border-radius:15px;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 17, 20, 17)
        header_layout.setSpacing(5)

        title = QLabel("NOTICIAS DE LA COMUNIDAD")
        title.setFont(QFont(self.montserrat, 17, QFont.Weight.Bold))
        title.setStyleSheet("color:#f3f5fb;letter-spacing:1px;border:none;")

        subtitle = QLabel(
            "Actualizaciones, eventos y novedades de D0cCtor's Hub y sus servidores."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color:#96a1b6;font-size:11px;border:none;")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header_card)

        for news in self.news_data:
            layout.addWidget(self.create_news_card(news, compact=False))

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
        

    # ===============================
    # STORE PAGE
    # ===============================
    def create_store_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(40, 20, 40, 30)

        main_layout.addStretch()

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background:qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #111826,
                    stop:1 #0b121d
                );
                border:1px solid rgba(255,255,255,22);
                border-radius:18px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(14)
        card_layout.setAlignment(Qt.AlignCenter)

        icon = QLabel()
        icon.setFixedSize(68, 68)
        icon.setPixmap(self.make_icon("store", 36, QColor("#7a83ff")))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("""
            background:rgba(122,131,255,0.10);
            border:1px solid rgba(122,131,255,0.22);
            border-radius:18px;
        """)

        title = QLabel("Tienda próximamente")
        title.setFont(QFont(self.montserrat, 20, QFont.Weight.Bold))
        title.setStyleSheet("color:white;border:none;")
        title.setAlignment(Qt.AlignCenter)

        desc = QLabel(
            "Esta sección va a quedar preparada para cosméticos, rangos y otros extras.\n"
            "Por ahora la dejamos con la misma línea visual del launcher."
        )
        desc.setWordWrap(True)
        desc.setMaximumWidth(560)
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color:#9aa6bc;font-size:12px;border:none;")

        card_layout.addWidget(icon)
        card_layout.addWidget(title)
        card_layout.addWidget(desc)

        main_layout.addWidget(card)
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


    def refresh_home_action_buttons(self):
        """Actualiza Jugar/Instalar del hero sin reconstruir la página Inicio."""
        primary_name = getattr(self, "home_primary_name", None)
        play_btn = getattr(self, "home_play_btn", None)
        install_btn = getattr(self, "home_install_btn", None)

        if not primary_name or play_btn is None or install_btn is None:
            return

        server = self.servers_data.get(primary_name, {})
        installed = bool(server.get("installed"))
        needs_update = bool(server.get("needs_update"))

        play_btn.setEnabled(installed and not needs_update)

        if needs_update:
            install_btn.setText("ACTUALIZAR")
            install_btn.setEnabled(True)
        elif installed:
            install_btn.setText("INSTALADO")
            install_btn.setEnabled(False)
        else:
            install_btn.setText("INSTALAR")
            install_btn.setEnabled(True)

        play_btn.update()
        install_btn.update()

    def refresh_server_buttons(self):
        self.refresh_home_action_buttons()

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
                    
    def _refresh_home_layout(self):
        """Fuerza a Qt a recalcular la geometría de Inicio tras montar la ventana."""
        try:
            if hasattr(self, "home_page") and self.home_page is not None:
                self.home_page.updateGeometry()
                self.home_page.adjustSize()

                viewport = getattr(self.home_page, "viewport", None)
                if callable(viewport):
                    self.home_page.viewport().update()

            if hasattr(self, "stack_container") and self.stack_container is not None:
                layout = self.stack_container.layout()
                if layout is not None:
                    layout.invalidate()
                    layout.activate()

                self.stack_container.updateGeometry()
                self.stack_container.update()

            central = self.centralWidget()
            if central is not None:
                layout = central.layout()
                if layout is not None:
                    layout.invalidate()
                    layout.activate()
                central.updateGeometry()
                central.update()

        except Exception as exc:
            print("No se pudo recalcular Inicio:", exc)

    # =====================================================
    # PAGE TRANSITION (FADE FIXED)
    # =====================================================
    def switch_page(self, index, animate=True):

        # Cambiar página primero
        self.stack.setCurrentIndex(index)
        if index == 0:
            QTimer.singleShot(0, self._refresh_home_layout)

        nav_buttons = [
            self.btn_inicio,
            self.btn_servers,
            self.btn_news,
            self.btn_settings,
            self.btn_support,
            self.btn_store,
        ]
        for i, button in enumerate(nav_buttons):
            is_active = i == index
            self.update_nav_icon(button, active=is_active)

            if is_active:
                button.setStyleSheet("""
                    QPushButton {
                        background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(108,99,255,100),stop:1 rgba(108,99,255,38));
                        color:white;
                        border:1px solid rgba(125,115,255,165);
                        border-radius:14px;
                        text-align:left;
                        padding-left:16px;
                        font-weight:650;
                    }
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background:transparent;
                        color:#a8b0c1;
                        border:1px solid transparent;
                        border-radius:14px;
                        text-align:left;
                        padding-left:16px;
                    }
                    QPushButton:hover {
                        background-color:rgba(91,108,255,28);
                        color:white;
                        border-color:rgba(91,108,255,70);
                    }
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
