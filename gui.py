"""
Interfaz gráfica de escritorio para Chamber.
Diseño moderno con tarjetas y panel lateral.
"""

import datetime
import threading
import webbrowser
import os
import uuid
import customtkinter as ctk
from tkinter import messagebox
import requests as http_requests
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from providers import PROVIDERS
from config import (
    load_config, save_config,
    get_api_key, set_api_key,
    is_enabled, set_enabled,
    get_selected_model, set_selected_model,
    get_stats, reset_stats, increment_stat,
)
from roulette import Roulette
from server import APIServer

# ── Paleta de colores ─────────────────────────────────────────
C = {
    "bg":           "#0f1118",
    "surface":      "#181b25",
    "card":         "#1e2233",
    "card_hover":   "#252a3a",
    "accent":       "#6c63ff",
    "accent_hover": "#7f78ff",
    "green":        "#22c55e",
    "green_hover":  "#16a34a",
    "red":          "#ef4444",
    "red_hover":    "#dc2626",
    "yellow":       "#eab308",
    "text":         "#e2e8f0",
    "text_dim":     "#8892a8",
    "text_muted":   "#4a5568",
    "border":       "#2d3348",
    "input_bg":     "#141720",
    "tag_free":     "#064e3b",
    "tag_trial":    "#78350f",
}

I18N = {
    "es": {
        "subtitle": "Maximiza tus tokens gratuitos",
        "server_stopped": "Servidor detenido",
        "no_connection": "Sin conexión",
        "current_provider": "PROVEEDOR ACTUAL",
        "local_port": "PUERTO LOCAL",
        "start_server": "▶  Iniciar Servidor",
        "stop_server": "■  Detener Servidor",
        "tab_chat": "Chat",
        "tab_providers": "Proveedores",
        "tab_stats": "Consumo",
        "tab_settings": "Configuración",
        "tab_log": "Registro",
        "tab_info": "Cómo usar",
        "settings_general": "CONFIGURACIÓN GENERAL",
        "settings_desc": "Centraliza acciones globales de Chamber desde este módulo.",
        "settings_language": "IDIOMA",
        "settings_actions": "ACCIONES",
        "gadget_mode": "Modo Gadget",
        "reset_exhausted": "Resetear agotados",
        "reset_stats": "Resetear estadísticas",
        "running_on": "Activo",
        "providers_connected": "proveedores conectados",
        "settings_port": "PUERTO LOCAL",
        "settings_port_desc": "Puerto del servidor local (requiere reiniciar servidor)",
        "settings_stream": "STREAMING",
        "settings_stream_desc": "Permitir respuestas en streaming (SSE). Desactívalo si el cliente no muestra las respuestas.",
        "settings_stream_on": "Activado",
        "settings_stream_off": "Desactivado",
        "info_quick_setup": "Configuración rápida",
        "info_quick_1": "1.  Haz clic en el nombre de cada proveedor para registrarte",
        "info_quick_2": "2.  Pega tu API Key y activa el switch",
        "info_quick_3": "3.  Pulsa  ▶ Iniciar Servidor",
        "info_quick_4": "4.  Listo — usa http://localhost:11411/v1 como si fuera OpenAI",
        "info_endpoint": "Endpoint local",
        "info_ep_key": "API Key:     cualquier valor (no se valida)",
        "info_ep_model": "Modelo:      auto  (o  proveedor/modelo)",
        "info_api_doc": "Módulo — Documentación API",
        "info_api_resp": "  Respuesta: ",
        "info_api_min_body": "  Body mínimo:",
        "info_api_params": "Parámetros soportados:",
        "info_api_compat": "Compatibilidad:",
        "info_api_compat_fmt": "  formato OpenAI Chat Completions",
        "info_example_python": "Ejemplo — Python",
        "info_example_curl": "Ejemplo — curl",
        "info_compatible": "Compatible con",
        "info_compatible_any": "·  Cualquier cliente OpenAI",
    },
    "en": {
        "subtitle": "Maximize your free tokens",
        "server_stopped": "Server stopped",
        "no_connection": "No connection",
        "current_provider": "CURRENT PROVIDER",
        "local_port": "LOCAL PORT",
        "start_server": "▶  Start Server",
        "stop_server": "■  Stop Server",
        "tab_chat": "Chat",
        "tab_providers": "Providers",
        "tab_stats": "Usage",
        "tab_settings": "Settings",
        "tab_log": "Log",
        "tab_info": "How to use",
        "settings_general": "GENERAL SETTINGS",
        "settings_desc": "Centralize Chamber global actions from this module.",
        "settings_language": "LANGUAGE",
        "settings_actions": "ACTIONS",
        "gadget_mode": "Gadget Mode",
        "reset_exhausted": "Reset exhausted",
        "reset_stats": "Reset stats",
        "running_on": "Active",
        "providers_connected": "connected providers",
        "settings_port": "LOCAL PORT",
        "settings_port_desc": "Local server port (requires server restart)",
        "settings_stream": "STREAMING",
        "settings_stream_desc": "Allow streaming responses (SSE). Disable if the client doesn't display responses.",
        "settings_stream_on": "Enabled",
        "settings_stream_off": "Disabled",
        "info_quick_setup": "Quick Setup",
        "info_quick_1": "1.  Click on each provider name to sign up",
        "info_quick_2": "2.  Paste your API Key and toggle the switch",
        "info_quick_3": "3.  Press  ▶ Start Server",
        "info_quick_4": "4.  Done — use http://localhost:11411/v1 as if it were OpenAI",
        "info_endpoint": "Local Endpoint",
        "info_ep_key": "API Key:     any value (not validated)",
        "info_ep_model": "Model:       auto  (or  provider/model)",
        "info_api_doc": "Module — API Documentation",
        "info_api_resp": "  Response: ",
        "info_api_min_body": "  Minimum body:",
        "info_api_params": "Supported parameters:",
        "info_api_compat": "Compatibility:",
        "info_api_compat_fmt": "  OpenAI Chat Completions format",
        "info_example_python": "Example — Python",
        "info_example_curl": "Example — curl",
        "info_compatible": "Compatible with",
        "info_compatible_any": "·  Any OpenAI client",
    },
}


class ChamberApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chamber")
        self.geometry("1200x780")
        self.minsize(1000, 650)
        self.configure(fg_color=C["bg"])

        ctk.set_appearance_mode("dark")

        # Load logo
        self._logo_image = None
        self._logo_icon = None
        self._load_logo()

        self.config_data = load_config()
        self.language = self.config_data.get("language", "es")
        if self.language not in I18N:
            self.language = "es"
        self.roulette = None
        self.api_server = None
        self.log_lines = []
        self.gadget_window = None
        self.gadget_mode = False
        self._closing = False
        self._last_stats_snapshot = None

        # Multi-conversation system
        self._migrate_legacy_chat()
        self.conversations = list(self.config_data.get("conversations", []))
        # Resume last conversation if it has messages, otherwise new chat
        if self.conversations and self.conversations[0].get("messages"):
            self._current_conv_id = self.conversations[0]["id"]
        else:
            self._current_conv_id = self._create_new_conversation(switch=False)
        self.chat_messages = self._get_current_conv()["messages"]

        self._build_ui()
        self._populate_providers()
        self._apply_language()
        self._update_status_loop()

    def _t(self, key):
        return I18N.get(self.language, I18N["es"]).get(key, key)

    def _load_logo(self):
        """Load logo.png from project directory if available."""
        if not HAS_PIL:
            return
        base = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base, "logo.png")
        ico_path = os.path.join(base, "logo.ico")
        if os.path.exists(logo_path):
            try:
                pil_img = Image.open(logo_path)
                self._logo_image = ctk.CTkImage(pil_img, size=(48, 48))
                self._logo_icon = ctk.CTkImage(pil_img, size=(28, 28))
                # Pre-render rotated frames for spinner animation
                self._spinner_frames = []
                for angle in range(0, 360, 30):
                    rotated = pil_img.rotate(-angle, resample=Image.BICUBIC)
                    self._spinner_frames.append(ctk.CTkImage(rotated, size=(24, 24)))
            except Exception:
                pass
        # Set window icon (.ico for Windows)
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════
    #  LAYOUT
    # ══════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── Sidebar ───────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=C["surface"], corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # ── Main area ─────────────────────────────────────────
        self.main = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

        self._build_main_header()
        self._build_main_content()

    # ── SIDEBAR ───────────────────────────────────────────────

    def _build_sidebar(self):
        sb = self.sidebar

        # Logo area
        logo_frame = ctk.CTkFrame(sb, fg_color="transparent", height=80)
        logo_frame.pack(fill="x", padx=20, pady=(24, 8))
        logo_frame.pack_propagate(False)

        logo_row = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        if self._logo_image:
            ctk.CTkLabel(logo_row, image=self._logo_image, text="").pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(logo_row, fg_color="transparent")
        title_col.pack(side="left")

        ctk.CTkLabel(
            title_col, text="Chamber",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=C["text"]
        ).pack(anchor="w")
        self.sidebar_subtitle_label = ctk.CTkLabel(
            title_col, text=self._t("subtitle"),
            font=ctk.CTkFont(size=11),
            text_color=C["text_dim"]
        )
        self.sidebar_subtitle_label.pack(anchor="w", pady=(2, 0))

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=8)

        # Status card
        self.status_card = ctk.CTkFrame(sb, fg_color=C["card"], corner_radius=12, height=100)
        self.status_card.pack(fill="x", padx=16, pady=8)
        self.status_card.pack_propagate(False)

        self.status_dot = ctk.CTkLabel(
            self.status_card, text="●",
            font=ctk.CTkFont(size=14), text_color=C["red"]
        )
        self.status_dot.pack(anchor="w", padx=16, pady=(12, 0))

        self.status_label = ctk.CTkLabel(
            self.status_card, text=self._t("server_stopped"),
            font=ctk.CTkFont(size=13, weight="bold"), text_color=C["text"],
            anchor="w"
        )
        self.status_label.pack(anchor="w", padx=16)

        self.status_detail = ctk.CTkLabel(
            self.status_card, text=self._t("no_connection"),
            font=ctk.CTkFont(size=11), text_color=C["text_dim"],
            anchor="w"
        )
        self.status_detail.pack(anchor="w", padx=16, pady=(0, 10))

        # Current provider card
        self.current_card = ctk.CTkFrame(sb, fg_color=C["card"], corner_radius=12, height=65)
        self.current_card.pack(fill="x", padx=16, pady=4)
        self.current_card.pack_propagate(False)

        self.current_provider_title = ctk.CTkLabel(
            self.current_card, text=self._t("current_provider"),
            font=ctk.CTkFont(size=9), text_color=C["text_muted"], anchor="w"
        )
        self.current_provider_title.pack(anchor="w", padx=16, pady=(10, 0))

        self.current_provider_label = ctk.CTkLabel(
            self.current_card, text="—",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C["accent"],
            anchor="w"
        )
        self.current_provider_label.pack(anchor="w", padx=16, pady=(0, 10))

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=8)

        # Port display (read-only)
        port_frame = ctk.CTkFrame(sb, fg_color="transparent")
        port_frame.pack(fill="x", padx=16, pady=4)
        self.port_title_label = ctk.CTkLabel(
            port_frame, text=self._t("local_port"),
            font=ctk.CTkFont(size=9), text_color=C["text_muted"], anchor="w"
        )
        self.port_title_label.pack(anchor="w")
        self.port_display_label = ctk.CTkLabel(
            port_frame, text=str(self.config_data.get("server_port", 11411)),
            font=ctk.CTkFont(size=13, weight="bold"), text_color=C["accent"], anchor="w"
        )
        self.port_display_label.pack(anchor="w", pady=(2, 0))

        # Spacer
        ctk.CTkFrame(sb, fg_color="transparent", height=8).pack(fill="x")

        # Action buttons
        self.start_btn = ctk.CTkButton(
            sb, text=self._t("start_server"), height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["green"], hover_color=C["green_hover"],
            text_color="#fff", corner_radius=10,
            command=self._start_server
        )
        self.start_btn.pack(fill="x", padx=16, pady=4)

        self.stop_btn = ctk.CTkButton(
            sb, text=self._t("stop_server"), height=42,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["red"], hover_color=C["red_hover"],
            text_color="#fff", corner_radius=10,
            state="disabled", command=self._stop_server
        )
        self.stop_btn.pack(fill="x", padx=16, pady=4)

        # Divider
        ctk.CTkFrame(sb, height=1, fg_color=C["border"]).pack(fill="x", padx=16, pady=8)

        # Spacer
        ctk.CTkFrame(sb, fg_color="transparent").pack(fill="both", expand=True)

    # ── MAIN HEADER (tab navigation) ─────────────────────────

    def _build_main_header(self):
        header = ctk.CTkFrame(self.main, fg_color="transparent", height=50)
        header.pack(fill="x", padx=24, pady=(18, 4))
        header.pack_propagate(False)

        self.nav_buttons = {}
        self.current_tab = "chat"
        tabs = ["chat", "providers", "stats", "settings", "log", "info"]
        nav_frame = ctk.CTkFrame(header, fg_color="transparent")
        nav_frame.pack(side="left")

        for tab_id in tabs:
            btn = ctk.CTkButton(
                nav_frame, text=self._t(f"tab_{tab_id}"), height=36, width=120,
                font=ctk.CTkFont(size=13),
                fg_color=C["accent"] if tab_id == "chat" else "transparent",
                hover_color=C["card_hover"],
                text_color=C["text"],
                corner_radius=10,
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(side="left", padx=3)
            self.nav_buttons[tab_id] = btn

    def _switch_tab(self, tab_id):
        self.current_tab = tab_id
        for tid, btn in self.nav_buttons.items():
            btn.configure(fg_color=C["accent"] if tid == tab_id else "transparent")

        for fid, frame in self.tab_frames.items():
            if fid == tab_id:
                frame.pack(fill="both", expand=True, padx=24, pady=(8, 16))
            else:
                frame.pack_forget()

    # ── MAIN CONTENT ──────────────────────────────────────────

    def _build_main_content(self):
        self.tab_frames = {}

        self.tab_frames["chat"] = ctk.CTkFrame(self.main, fg_color="transparent")
        self._build_chat_tab(self.tab_frames["chat"])

        self.tab_frames["providers"] = ctk.CTkFrame(self.main, fg_color="transparent")
        self._build_providers_tab(self.tab_frames["providers"])

        self.tab_frames["stats"] = ctk.CTkFrame(self.main, fg_color="transparent")
        self._build_stats_tab(self.tab_frames["stats"])

        self.tab_frames["settings"] = ctk.CTkFrame(self.main, fg_color="transparent")
        self._build_settings_tab(self.tab_frames["settings"])

        self.tab_frames["log"] = ctk.CTkFrame(self.main, fg_color="transparent")
        self._build_log_tab(self.tab_frames["log"])

        self.tab_frames["info"] = ctk.CTkFrame(self.main, fg_color="transparent")
        self._build_info_tab(self.tab_frames["info"])

        # Show initial tab
        self.tab_frames["chat"].pack(fill="both", expand=True, padx=24, pady=(8, 16))

    # ── CHAT TAB ──────────────────────────────────────────────

    def _build_chat_tab(self, parent):
        # Horizontal layout: conversation list | chat area
        chat_container = ctk.CTkFrame(parent, fg_color="transparent")
        chat_container.pack(fill="both", expand=True)

        # ── Conversation sidebar ──
        self._conv_sidebar = ctk.CTkFrame(chat_container, fg_color=C["surface"], width=220, corner_radius=12)
        self._conv_sidebar.pack(side="left", fill="y", padx=(0, 8))
        self._conv_sidebar.pack_propagate(False)

        new_chat_btn = ctk.CTkButton(
            self._conv_sidebar, text="+ Nuevo chat", height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#fff", corner_radius=8,
            command=self._new_chat
        )
        new_chat_btn.pack(fill="x", padx=10, pady=(10, 6))

        self._conv_list_frame = ctk.CTkScrollableFrame(
            self._conv_sidebar, fg_color="transparent",
            scrollbar_button_color=C["border"]
        )
        self._conv_list_frame.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        # ── Chat area ──
        chat_area = ctk.CTkFrame(chat_container, fg_color="transparent")
        chat_area.pack(side="left", fill="both", expand=True)

        # Messages area
        self.chat_display = ctk.CTkTextbox(
            chat_area,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=C["surface"], text_color=C["text"],
            corner_radius=12, border_width=1, border_color=C["border"],
            state="disabled", wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, pady=(0, 8))

        # Configure text tags for styling
        self.chat_display._textbox.tag_configure(
            "user_name", foreground=C["accent"],
            font=("Segoe UI", 11, "bold")
        )
        self.chat_display._textbox.tag_configure(
            "assistant_name", foreground=C["green"],
            font=("Segoe UI", 11, "bold")
        )
        self.chat_display._textbox.tag_configure(
            "system_msg", foreground=C["text_muted"],
            font=("Segoe UI", 11, "italic")
        )
        self.chat_display._textbox.tag_configure(
            "provider_tag", foreground=C["yellow"],
            font=("Segoe UI", 9)
        )

        # Bottom input area
        input_frame = ctk.CTkFrame(chat_area, fg_color=C["card"], corner_radius=12, height=56)
        input_frame.pack(fill="x")
        input_frame.pack_propagate(False)

        # System prompt toggle
        self.system_visible = False
        self.sys_btn = ctk.CTkButton(
            input_frame, text="Sys", width=36, height=36,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color=C["card_hover"],
            text_color=C["text_muted"], corner_radius=8,
            command=self._toggle_system_prompt
        )
        self.sys_btn.pack(side="left", padx=(10, 4), pady=10)

        # System prompt frame (created now, shown/hidden on toggle)
        self.system_frame = ctk.CTkFrame(chat_area, fg_color=C["card"], corner_radius=10)
        self.system_entry = ctk.CTkEntry(
            self.system_frame, height=34,
            placeholder_text="System prompt (opcional)...",
            font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], border_color=C["border"],
            text_color=C["text"], corner_radius=8
        )
        self.system_entry.insert(0, self.config_data.get("system_prompt", ""))
        self.system_entry.pack(fill="x", padx=10, pady=8)

        self.chat_input = ctk.CTkEntry(
            input_frame, height=36,
            placeholder_text="Escribe un mensaje...",
            font=ctk.CTkFont(size=13),
            fg_color=C["input_bg"], border_color=C["border"],
            text_color=C["text"], corner_radius=8
        )
        self.chat_input.pack(side="left", fill="x", expand=True, padx=4, pady=10)
        self.chat_input.bind("<Return>", lambda e: self._send_message())

        self.send_btn = ctk.CTkButton(
            input_frame, text="Enviar", width=80, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#fff", corner_radius=8,
            command=self._send_message
        )
        self.send_btn.pack(side="right", padx=(4, 10), pady=10)

        self.clear_chat_btn = ctk.CTkButton(
            input_frame, text="Limpiar", width=64, height=36,
            font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color=C["card_hover"],
            text_color=C["text_muted"], corner_radius=8,
            command=self._clear_chat
        )
        self.clear_chat_btn.pack(side="right", padx=2, pady=10)

        # Spinner overlay (hidden by default)
        self._spinner_frame_idx = 0
        self._spinner_active = False
        self._chat_spinner_frame = ctk.CTkFrame(
            chat_area, fg_color=C["card"], corner_radius=10, height=40
        )
        self._chat_spinner_label = ctk.CTkLabel(
            self._chat_spinner_frame, text="",
            image=self._spinner_frames[0] if getattr(self, "_spinner_frames", None) else None,
        )
        self._chat_spinner_label.pack(side="left", padx=(12, 6), pady=6)
        self._chat_spinner_text = ctk.CTkLabel(
            self._chat_spinner_frame, text="Pensando...",
            font=ctk.CTkFont(size=12), text_color=C["text_dim"]
        )
        self._chat_spinner_text.pack(side="left", pady=6)

        self._render_chat_history()
        self._refresh_conv_list()

    def _toggle_system_prompt(self):
        if self.system_visible:
            self.system_frame.pack_forget()
            self.sys_btn.configure(text_color=C["text_muted"])
        else:
            # Pack between chat display and input
            self.system_frame.pack(fill="x", pady=(4, 0), after=self.chat_display)
            self.sys_btn.configure(text_color=C["accent"])
        self.system_visible = not self.system_visible

    def _send_message(self):
        text = self.chat_input.get().strip()
        if not text:
            return
        if not self.roulette:
            self._chat_append_system("Inicia el servidor primero (▶ Iniciar Servidor)")
            return

        self.chat_input.delete(0, "end")
        self.send_btn.configure(state="disabled", text="...")

        # Append user message
        self.chat_messages.append({"role": "user", "content": text})
        self._persist_chat_state()
        self._chat_append_user(text)
        self._show_chat_spinner()
        self._refresh_conv_list()

        # Build messages for API
        api_messages = []
        sys_text = ""
        if hasattr(self, "system_entry"):
            sys_text = self.system_entry.get().strip()
        if sys_text:
            api_messages.append({"role": "system", "content": sys_text})
        api_messages.extend(
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in self.chat_messages
            if msg.get("role") in ("user", "assistant")
        )

        # Send in background thread (never stream in GUI — we need full text)
        def do_request():
            try:
                result = self.roulette.chat_completion(api_messages, stream=False)
                if self._closing:
                    return
                if "choices" not in result or not result["choices"]:
                    err = result.get("error", {}).get("message", "Respuesta inválida del proveedor")
                    self.after(0, lambda e=err: self._chat_append_system(f"Error: {e}"))
                else:
                    content = result["choices"][0]["message"]["content"]
                    model = result.get("model", "")
                    provider = self.roulette.get_current_provider_id()
                    prov_name = PROVIDERS.get(provider, {}).get("name", provider)
                    tag = f"{prov_name}" + (f" · {model}" if model else "")
                    self.chat_messages.append(
                        {"role": "assistant", "content": content, "provider_tag": tag}
                    )
                    self._persist_chat_state()
                    self.after(0, lambda c=content, t=tag: self._chat_append_assistant(c, t))
            except Exception as e:
                if self._closing:
                    return
                self.after(0, lambda err=e: self._chat_append_system(f"Error: {err}"))
            finally:
                if not self._closing:
                    self.after(0, self._hide_chat_spinner)
                    self.after(0, lambda: self.send_btn.configure(state="normal", text="Enviar"))

        threading.Thread(target=do_request, daemon=True).start()

    def _chat_append_user(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", "Tú\n", "user_name")
        self.chat_display.insert("end", f"{text}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _chat_append_assistant(self, text, provider_tag=""):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", "AI", "assistant_name")
        if provider_tag:
            self.chat_display._textbox.insert("end", f"  [{provider_tag}]", "provider_tag")
        self.chat_display._textbox.insert("end", "\n")
        self.chat_display.insert("end", f"{text}\n\n")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _chat_append_system(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display._textbox.insert("end", f"{text}\n\n", "system_msg")
        self.chat_display.see("end")
        self.chat_display.configure(state="disabled")

    def _show_chat_spinner(self):
        self._spinner_active = True
        self._spinner_frame_idx = 0
        self._chat_spinner_frame.pack(fill="x", pady=(4, 0), before=self.chat_display.master.winfo_children()[-1] if False else None)
        # Place after chat display, before input
        self._chat_spinner_frame.pack_forget()
        self._chat_spinner_frame.pack(fill="x", pady=(0, 4), after=self.chat_display)
        self._animate_spinner()

    def _hide_chat_spinner(self):
        self._spinner_active = False
        self._chat_spinner_frame.pack_forget()

    def _animate_spinner(self):
        if not self._spinner_active or self._closing:
            return
        if getattr(self, "_spinner_frames", None):
            self._spinner_frame_idx = (self._spinner_frame_idx + 1) % len(self._spinner_frames)
            self._chat_spinner_label.configure(image=self._spinner_frames[self._spinner_frame_idx])
        self.after(80, self._animate_spinner)

    def _clear_chat(self):
        self.chat_messages.clear()
        self._persist_chat_state()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")

    def _migrate_legacy_chat(self):
        """Migrate old flat chat_history into conversations list."""
        old = self.config_data.get("chat_history", [])
        convs = self.config_data.get("conversations", [])
        if old and not convs:
            title = self._conv_title_from_messages(old)
            convs.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "messages": list(old),
                "created_at": datetime.datetime.now().isoformat(),
            })
            self.config_data["conversations"] = convs
            self.config_data["chat_history"] = []
            save_config(self.config_data)

    def _conv_title_from_messages(self, messages):
        for msg in messages:
            if msg.get("role") == "user" and msg.get("content", "").strip():
                text = msg["content"].strip()
                return text[:40] + ("..." if len(text) > 40 else "")
        return "Chat"

    def _create_new_conversation(self, switch=True):
        conv = {
            "id": str(uuid.uuid4()),
            "title": "Nuevo chat",
            "messages": [],
            "created_at": datetime.datetime.now().isoformat(),
        }
        self.conversations.insert(0, conv)
        self._current_conv_id = conv["id"]
        self._save_conversations()
        if switch:
            self._switch_conversation(conv["id"])
        return conv["id"]

    def _get_current_conv(self):
        for c in self.conversations:
            if c["id"] == self._current_conv_id:
                return c
        return self.conversations[0] if self.conversations else {"id": "", "title": "", "messages": [], "created_at": ""}

    def _new_chat(self):
        # Save current if it has messages
        self._save_conversations()
        cid = self._create_new_conversation(switch=True)
        self._refresh_conv_list()

    def _switch_conversation(self, conv_id):
        self._current_conv_id = conv_id
        conv = self._get_current_conv()
        self.chat_messages = conv["messages"]
        if hasattr(self, "chat_display"):
            self._render_chat_history()
        if hasattr(self, "_conv_list_frame"):
            self._refresh_conv_list()

    def _delete_conversation(self, conv_id):
        self.conversations = [c for c in self.conversations if c["id"] != conv_id]
        self._save_conversations()
        if conv_id == self._current_conv_id:
            if self.conversations:
                self._switch_conversation(self.conversations[0]["id"])
            else:
                self._create_new_conversation(switch=True)
        self._refresh_conv_list()

    def _save_conversations(self):
        # Update title of current conv based on first user message
        conv = self._get_current_conv()
        if conv and conv["messages"] and conv["title"] == "Nuevo chat":
            conv["title"] = self._conv_title_from_messages(conv["messages"])
        # Remove empty non-current conversations
        self.conversations = [
            c for c in self.conversations
            if c["messages"] or c["id"] == self._current_conv_id
        ]
        # Keep max 50 conversations
        self.config_data["conversations"] = self.conversations[:50]
        save_config(self.config_data)

    def _refresh_conv_list(self):
        if not hasattr(self, "_conv_list_frame"):
            return
        for w in self._conv_list_frame.winfo_children():
            w.destroy()

        for conv in self.conversations:
            is_active = conv["id"] == self._current_conv_id
            msg_count = len([m for m in conv["messages"] if m.get("role") == "user"])

            item_frame = ctk.CTkFrame(
                self._conv_list_frame,
                fg_color=C["card"] if is_active else "transparent",
                corner_radius=8,
            )
            item_frame.pack(fill="x", pady=1)

            btn = ctk.CTkButton(
                item_frame,
                text=conv["title"][:28],
                anchor="w", height=32,
                font=ctk.CTkFont(size=11, weight="bold" if is_active else "normal"),
                fg_color="transparent", hover_color=C["card_hover"],
                text_color=C["accent"] if is_active else C["text_dim"],
                corner_radius=6,
                command=lambda cid=conv["id"]: self._switch_conversation(cid),
            )
            btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

            if len(self.conversations) > 1:
                del_btn = ctk.CTkButton(
                    item_frame, text="×", width=24, height=24,
                    font=ctk.CTkFont(size=13),
                    fg_color="transparent", hover_color=C["red"],
                    text_color=C["text_muted"], corner_radius=4,
                    command=lambda cid=conv["id"]: self._delete_conversation(cid),
                )
                del_btn.pack(side="right", padx=(0, 4), pady=4)

    def _persist_chat_state(self):
        self._save_conversations()
        if hasattr(self, "system_entry"):
            self.config_data["system_prompt"] = self.system_entry.get().strip()
            save_config(self.config_data)

    def _render_chat_history(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        for msg in self.chat_messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                self._chat_append_user(content)
            elif role == "assistant":
                self._chat_append_assistant(content, msg.get("provider_tag", ""))

    # ── PROVIDERS TAB ─────────────────────────────────────────

    def _build_providers_tab(self, parent):
        self.provider_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["text_muted"]
        )
        self.provider_scroll.pack(fill="both", expand=True)
        self.provider_widgets = {}

    def _populate_providers(self):
        free_ids = [
            "openrouter", "groq", "cerebras", "cohere",
            "github_models", "mistral", "google_ai", "nvidia_nim"
        ]
        trial_ids = [
            "sambanova", "hyperbolic", "fireworks", "nebius"
        ]

        self._add_section_header(self.provider_scroll, "GRATUITOS PERMANENTES", len(free_ids))
        for pid in free_ids:
            if pid in PROVIDERS:
                self._add_provider_card(pid, PROVIDERS[pid], is_trial=False)

        ctk.CTkFrame(self.provider_scroll, height=12, fg_color="transparent").pack(fill="x")
        self._add_section_header(self.provider_scroll, "CON CRÉDITOS DE PRUEBA", len(trial_ids))
        for pid in trial_ids:
            if pid in PROVIDERS:
                self._add_provider_card(pid, PROVIDERS[pid], is_trial=True)

    def _add_section_header(self, parent, title, count):
        frame = ctk.CTkFrame(parent, fg_color="transparent", height=32)
        frame.pack(fill="x", pady=(8, 4))
        frame.pack_propagate(False)
        ctk.CTkLabel(
            frame, text=f"{title}  ({count})",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"]
        ).pack(side="left")

    def _add_provider_card(self, pid, prov, is_trial=False):
        card = ctk.CTkFrame(
            self.provider_scroll,
            fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["border"]
        )
        card.pack(fill="x", pady=4, ipady=4)

        widgets = {}

        # ── Row 1: header (switch + name + tags + stats) ──
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 4))

        left = ctk.CTkFrame(row1, fg_color="transparent")
        left.pack(side="left")

        enabled_var = ctk.BooleanVar(value=is_enabled(self.config_data, pid))
        switch = ctk.CTkSwitch(
            left, text="", variable=enabled_var,
            width=42, height=22,
            progress_color=C["green"],
            button_color="#fff",
            fg_color=C["text_muted"]
        )
        switch.pack(side="left", padx=(0, 10))
        widgets["enabled_var"] = enabled_var

        name_btn = ctk.CTkButton(
            left, text=prov["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent", hover_color=C["card_hover"],
            text_color=C["text"], anchor="w",
            cursor="hand2", height=28,
            command=lambda u=prov["signup_url"]: webbrowser.open(u)
        )
        name_btn.pack(side="left")

        ctk.CTkButton(
            left, text="↗", width=24, height=24,
            font=ctk.CTkFont(size=13),
            fg_color="transparent", hover_color=C["card_hover"],
            text_color=C["text_dim"], cursor="hand2",
            command=lambda u=prov["signup_url"]: webbrowser.open(u)
        ).pack(side="left", padx=(2, 0))

        right = ctk.CTkFrame(row1, fg_color="transparent")
        right.pack(side="right")

        tag_color = C["tag_trial"] if is_trial else C["tag_free"]
        tag_text = "TRIAL" if is_trial else "FREE"
        ctk.CTkLabel(
            right, text=f" {tag_text} ",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=tag_color, corner_radius=4,
            text_color=C["text"], height=20
        ).pack(side="left", padx=(0, 8))

        stats = get_stats(self.config_data, pid)
        stats_label = ctk.CTkLabel(
            right,
            text=f"✓ {stats['requests']}   ✗ {stats['errors']}",
            font=ctk.CTkFont(size=11),
            text_color=C["text_dim"]
        )
        stats_label.pack(side="left")
        widgets["stats_label"] = stats_label

        # ── Row 2: limits + notes ──
        ctk.CTkLabel(
            card, text=prov["limits"] + "  ·  " + prov["notes"],
            font=ctk.CTkFont(size=11),
            text_color=C["text_muted"], anchor="w"
        ).pack(fill="x", padx=16, pady=(0, 6))

        # ── Row 3: API key + model selector ──
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(0, 12))

        # API Key
        key_frame = ctk.CTkFrame(row3, fg_color="transparent")
        key_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkLabel(
            key_frame, text="API KEY",
            font=ctk.CTkFont(size=9), text_color=C["text_muted"], anchor="w"
        ).pack(anchor="w")

        key_row = ctk.CTkFrame(key_frame, fg_color="transparent")
        key_row.pack(fill="x")

        key_entry = ctk.CTkEntry(
            key_row, height=34, show="•",
            placeholder_text="Pegar API Key...",
            font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], border_color=C["border"],
            text_color=C["text"], corner_radius=8
        )
        saved_key = get_api_key(self.config_data, pid)
        if saved_key:
            key_entry.insert(0, saved_key)
        key_entry.pack(side="left", fill="x", expand=True)
        widgets["key_entry"] = key_entry

        def make_toggle(entry):
            showing = [False]
            def toggle():
                showing[0] = not showing[0]
                entry.configure(show="" if showing[0] else "•")
            return toggle

        ctk.CTkButton(
            key_row, text="👁", width=34, height=34,
            font=ctk.CTkFont(size=13),
            fg_color=C["input_bg"], hover_color=C["card_hover"],
            border_width=1, border_color=C["border"],
            text_color=C["text_dim"], corner_radius=8,
            command=make_toggle(key_entry)
        ).pack(side="left", padx=(4, 0))

        # Sync models button
        sync_btn = ctk.CTkButton(
            key_row, text="⟳", width=34, height=34,
            font=ctk.CTkFont(size=15),
            fg_color=C["input_bg"], hover_color=C["card_hover"],
            border_width=1, border_color=C["border"],
            text_color=C["accent"], corner_radius=8,
            command=lambda p=pid: self._sync_models(p)
        )
        sync_btn.pack(side="left", padx=(4, 0))
        widgets["sync_btn"] = sync_btn

        # Model selector
        model_frame = ctk.CTkFrame(row3, fg_color="transparent", width=260)
        model_frame.pack(side="right")
        model_frame.pack_propagate(False)

        ctk.CTkLabel(
            model_frame, text="MODELO",
            font=ctk.CTkFont(size=9), text_color=C["text_muted"], anchor="w"
        ).pack(anchor="w")

        models = prov["models"]
        selected = get_selected_model(self.config_data, pid)
        model_var = ctk.StringVar(value=selected)
        model_menu = ctk.CTkOptionMenu(
            model_frame, variable=model_var, values=models,
            height=34, font=ctk.CTkFont(size=11),
            fg_color=C["input_bg"], button_color=C["border"],
            button_hover_color=C["text_muted"],
            dropdown_fg_color=C["surface"],
            dropdown_hover_color=C["card"],
            text_color=C["text"],
            corner_radius=8
        )
        model_menu.pack(fill="x")
        widgets["model_var"] = model_var
        widgets["model_menu"] = model_menu

        self.provider_widgets[pid] = widgets

    # ── LOG TAB ───────────────────────────────────────────────

    def _build_log_tab(self, parent):
        top = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        top.pack(fill="x", pady=(0, 6))
        top.pack_propagate(False)

        ctk.CTkLabel(
            top, text="REGISTRO DE ACTIVIDAD",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"]
        ).pack(side="left")

        ctk.CTkButton(
            top, text="Limpiar", width=70, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text_dim"], corner_radius=6,
            command=self._clear_log
        ).pack(side="right")

        self.log_text = ctk.CTkTextbox(
            parent,
            font=ctk.CTkFont(family="Cascadia Code, Consolas, monospace", size=12),
            fg_color=C["surface"], text_color=C["text"],
            corner_radius=12, border_width=1, border_color=C["border"],
            state="disabled"
        )
        self.log_text.pack(fill="both", expand=True)

    def _build_settings_tab(self, parent):
        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["text_muted"]
        )
        scroll.pack(fill="both", expand=True)

        top_card = ctk.CTkFrame(
            scroll, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["border"]
        )
        top_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            top_card, text=self._t("settings_general"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"], anchor="w"
        ).pack(fill="x", padx=18, pady=(14, 4))

        self.settings_desc_label = ctk.CTkLabel(
            top_card,
            text=self._t("settings_desc"),
            font=ctk.CTkFont(size=12),
            text_color=C["text_dim"], anchor="w"
        )
        self.settings_desc_label.pack(fill="x", padx=18, pady=(0, 14))

        language_card = ctk.CTkFrame(
            scroll, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["border"]
        )
        language_card.pack(fill="x", pady=6)

        self.settings_language_title = ctk.CTkLabel(
            language_card, text=self._t("settings_language"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"], anchor="w"
        )
        self.settings_language_title.pack(fill="x", padx=18, pady=(14, 8))

        self.language_var = ctk.StringVar(value="Español" if self.language == "es" else "English")
        self.language_menu = ctk.CTkOptionMenu(
            language_card,
            variable=self.language_var,
            values=["Español", "English"],
            height=36, font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], button_color=C["border"],
            button_hover_color=C["text_muted"],
            dropdown_fg_color=C["surface"],
            dropdown_hover_color=C["card"],
            text_color=C["text"],
            corner_radius=8,
            command=self._on_language_change,
        )
        self.language_menu.pack(fill="x", padx=18, pady=(0, 14))

        port_card = ctk.CTkFrame(
            scroll, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["border"]
        )
        port_card.pack(fill="x", pady=6)

        self.settings_port_title = ctk.CTkLabel(
            port_card, text=self._t("settings_port"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"], anchor="w"
        )
        self.settings_port_title.pack(fill="x", padx=18, pady=(14, 2))

        self.settings_port_desc = ctk.CTkLabel(
            port_card, text=self._t("settings_port_desc"),
            font=ctk.CTkFont(size=11),
            text_color=C["text_dim"], anchor="w"
        )
        self.settings_port_desc.pack(fill="x", padx=18, pady=(0, 8))

        self.port_entry = ctk.CTkEntry(
            port_card, height=36, font=ctk.CTkFont(size=13),
            fg_color=C["input_bg"], border_color=C["border"],
            text_color=C["text"], corner_radius=8
        )
        self.port_entry.insert(0, str(self.config_data.get("server_port", 11411)))
        self.port_entry.pack(fill="x", padx=18, pady=(0, 14))
        self.port_entry.bind("<FocusOut>", self._on_port_change)
        self.port_entry.bind("<Return>", self._on_port_change)

        stream_card = ctk.CTkFrame(
            scroll, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["border"]
        )
        stream_card.pack(fill="x", pady=6)

        self.settings_stream_title = ctk.CTkLabel(
            stream_card, text=self._t("settings_stream"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"], anchor="w"
        )
        self.settings_stream_title.pack(fill="x", padx=18, pady=(14, 2))

        self.settings_stream_desc = ctk.CTkLabel(
            stream_card, text=self._t("settings_stream_desc"),
            font=ctk.CTkFont(size=11),
            text_color=C["text_dim"], anchor="w", wraplength=500
        )
        self.settings_stream_desc.pack(fill="x", padx=18, pady=(0, 8))

        stream_row = ctk.CTkFrame(stream_card, fg_color="transparent")
        stream_row.pack(fill="x", padx=18, pady=(0, 14))

        self.stream_var = ctk.BooleanVar(value=self.config_data.get("stream_enabled", False))
        self.stream_switch = ctk.CTkSwitch(
            stream_row, text=self._t("settings_stream_on") if self.stream_var.get() else self._t("settings_stream_off"),
            variable=self.stream_var,
            font=ctk.CTkFont(size=12),
            text_color=C["text"],
            fg_color=C["border"],
            progress_color=C["green"],
            button_color=C["text"],
            button_hover_color=C["accent"],
            command=self._on_stream_change
        )
        self.stream_switch.pack(side="left")

        actions_card = ctk.CTkFrame(
            scroll, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["border"]
        )
        actions_card.pack(fill="x", pady=6)

        self.settings_actions_title = ctk.CTkLabel(
            actions_card, text=self._t("settings_actions"),
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"], anchor="w"
        )
        self.settings_actions_title.pack(fill="x", padx=18, pady=(14, 10))

        self.settings_gadget_btn = ctk.CTkButton(
            actions_card, text=self._t("gadget_mode"), height=38,
            font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], hover_color=C["card_hover"],
            text_color=C["text"], corner_radius=10,
            command=self._toggle_gadget
        )
        self.settings_gadget_btn.pack(fill="x", padx=18, pady=4)

        self.settings_reset_exhausted_btn = ctk.CTkButton(
            actions_card, text=self._t("reset_exhausted"), height=38,
            font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], hover_color=C["card_hover"],
            text_color=C["text"], corner_radius=10,
            command=self._reset_exhausted
        )
        self.settings_reset_exhausted_btn.pack(fill="x", padx=18, pady=4)

        self.settings_reset_stats_btn = ctk.CTkButton(
            actions_card, text=self._t("reset_stats"), height=38,
            font=ctk.CTkFont(size=12),
            fg_color=C["input_bg"], hover_color=C["card_hover"],
            text_color=C["text"], corner_radius=10,
            command=self._reset_all_stats
        )
        self.settings_reset_stats_btn.pack(fill="x", padx=18, pady=(4, 18))

    def _on_language_change(self, selected):
        self.language = "en" if selected == "English" else "es"
        self.config_data["language"] = self.language
        save_config(self.config_data)
        self._apply_language()

    def _on_stream_change(self):
        enabled = self.stream_var.get()
        self.config_data["stream_enabled"] = enabled
        save_config(self.config_data)
        label = self._t("settings_stream_on") if enabled else self._t("settings_stream_off")
        self.stream_switch.configure(text=label)

    def _on_port_change(self, event=None):
        raw = self.port_entry.get().strip()
        try:
            port = int(raw)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            port = self.config_data.get("server_port", 11411)
            self.port_entry.delete(0, "end")
            self.port_entry.insert(0, str(port))
        self.config_data["server_port"] = port
        save_config(self.config_data)
        if hasattr(self, "port_display_label"):
            self.port_display_label.configure(text=str(port))

    def _apply_language(self):
        if hasattr(self, "sidebar_subtitle_label"):
            self.sidebar_subtitle_label.configure(text=self._t("subtitle"))
        if hasattr(self, "current_provider_title"):
            self.current_provider_title.configure(text=self._t("current_provider"))
        if hasattr(self, "port_title_label"):
            self.port_title_label.configure(text=self._t("local_port"))
        if hasattr(self, "start_btn"):
            self.start_btn.configure(text=self._t("start_server"))
        if hasattr(self, "stop_btn"):
            self.stop_btn.configure(text=self._t("stop_server"))

        for tab_id, btn in self.nav_buttons.items():
            btn.configure(text=self._t(f"tab_{tab_id}"))

        if hasattr(self, "settings_desc_label"):
            self.settings_desc_label.configure(text=self._t("settings_desc"))
        if hasattr(self, "settings_language_title"):
            self.settings_language_title.configure(text=self._t("settings_language"))
        if hasattr(self, "settings_actions_title"):
            self.settings_actions_title.configure(text=self._t("settings_actions"))
        if hasattr(self, "settings_gadget_btn"):
            self.settings_gadget_btn.configure(text=self._t("gadget_mode"))
        if hasattr(self, "settings_reset_exhausted_btn"):
            self.settings_reset_exhausted_btn.configure(text=self._t("reset_exhausted"))
        if hasattr(self, "settings_reset_stats_btn"):
            self.settings_reset_stats_btn.configure(text=self._t("reset_stats"))

        if hasattr(self, "settings_port_title"):
            self.settings_port_title.configure(text=self._t("settings_port"))
        if hasattr(self, "settings_port_desc"):
            self.settings_port_desc.configure(text=self._t("settings_port_desc"))
        if hasattr(self, "settings_stream_title"):
            self.settings_stream_title.configure(text=self._t("settings_stream"))
        if hasattr(self, "settings_stream_desc"):
            self.settings_stream_desc.configure(text=self._t("settings_stream_desc"))
        if hasattr(self, "stream_switch"):
            enabled = self.stream_var.get()
            self.stream_switch.configure(text=self._t("settings_stream_on") if enabled else self._t("settings_stream_off"))

        if hasattr(self, "status_label"):
            self._update_status()

        if hasattr(self, "_info_parent"):
            self._rebuild_info_content()

    # ── INFO TAB ──────────────────────────────────────────────

    def _build_info_tab(self, parent):
        self._info_parent = parent
        self._rebuild_info_content()

    def _get_info_sections(self):
        return [
            (self._t("info_quick_setup"), [
                self._t("info_quick_1"),
                self._t("info_quick_2"),
                self._t("info_quick_3"),
                self._t("info_quick_4"),
            ]),
            (self._t("info_endpoint"), [
                "Base URL:    http://localhost:11411/v1",
                self._t("info_ep_key"),
                self._t("info_ep_model"),
            ]),
            (self._t("info_api_doc"), [
                "GET  /health",
                self._t("info_api_resp") + '{"status":"ok","active_providers":N,"current_provider":"id"}',
                "",
                "GET  /v1/models",
                self._t("info_api_resp") + '{"object":"list","data":[{"id":"...","owned_by":"..."}]}',
                "",
                "POST /v1/chat/completions",
                self._t("info_api_min_body"),
                '  {"model":"auto","messages":[{"role":"user","content":"Hello"}]}',
                "",
                self._t("info_api_params"),
                "  model, messages, temperature, max_tokens, top_p",
                "",
                self._t("info_api_compat"),
                self._t("info_api_compat_fmt"),
            ]),
            (self._t("info_example_python"), [
                "from openai import OpenAI",
                'client = OpenAI(base_url="http://localhost:11411/v1", api_key="x")',
                "r = client.chat.completions.create(",
                '    model="auto",',
                '    messages=[{"role":"user","content":"Hello!"}]',
                ")",
                "print(r.choices[0].message.content)",
            ]),
            (self._t("info_example_curl"), [
                "curl http://localhost:11411/v1/chat/completions \\",
                '  -H "Content-Type: application/json" \\',
                '  -d \'{"model":"auto","messages":[{"role":"user","content":"Hello!"}]}\'',
            ]),
            (self._t("info_compatible"), [
                "·  Continue (VS Code)     ·  Open WebUI",
                "·  LangChain / LlamaIndex " + self._t("info_compatible_any"),
            ]),
        ]

    def _rebuild_info_content(self):
        for w in self._info_parent.winfo_children():
            w.destroy()

        scroll = ctk.CTkScrollableFrame(
            self._info_parent, fg_color="transparent",
            scrollbar_button_color=C["border"]
        )
        scroll.pack(fill="both", expand=True)

        for title, lines in self._get_info_sections():
            sec = ctk.CTkFrame(scroll, fg_color=C["card"], corner_radius=12)
            sec.pack(fill="x", pady=6)

            ctk.CTkLabel(
                sec, text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=C["text"], anchor="w"
            ).pack(fill="x", padx=20, pady=(14, 4))

            content = "\n".join(lines)
            ctk.CTkLabel(
                sec, text=content,
                font=ctk.CTkFont(family="Cascadia Code, Consolas, monospace", size=12),
                text_color=C["text_dim"], anchor="nw", justify="left",
                wraplength=700
            ).pack(fill="x", padx=20, pady=(0, 14))

    # ── STATS / CONSUMO TAB ───────────────────────────────────

    def _build_stats_tab(self, parent):
        # Header with refresh button
        top = ctk.CTkFrame(parent, fg_color="transparent", height=36)
        top.pack(fill="x", pady=(0, 6))
        top.pack_propagate(False)

        ctk.CTkLabel(
            top, text="CONSUMO POR PROVEEDOR",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C["text_muted"]
        ).pack(side="left")

        ctk.CTkButton(
            top, text="Actualizar", width=80, height=28,
            font=ctk.CTkFont(size=11),
            fg_color=C["card"], hover_color=C["card_hover"],
            text_color=C["text_dim"], corner_radius=6,
            command=self._refresh_stats_tab
        ).pack(side="right")

        # Scrollable area for provider stats cards
        self.stats_scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=C["border"],
            scrollbar_button_hover_color=C["text_muted"]
        )
        self.stats_scroll.pack(fill="both", expand=True)

        # Summary card at top
        self.stats_summary_frame = ctk.CTkFrame(
            self.stats_scroll, fg_color=C["card"], corner_radius=12,
            border_width=1, border_color=C["accent"]
        )
        self.stats_summary_frame.pack(fill="x", pady=(0, 12))

        self.stats_summary_labels = {}
        row = ctk.CTkFrame(self.stats_summary_frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=16)

        for i, (key, icon, label) in enumerate([
            ("total_req", "✓", "Peticiones"),
            ("total_err", "✗", "Errores"),
            ("total_tokens", "◈", "Tokens totales"),
            ("prompt_tokens", "→", "Prompt tokens"),
            ("compl_tokens", "←", "Completion tokens"),
        ]):
            col = ctk.CTkFrame(row, fg_color="transparent")
            col.pack(side="left", expand=True)
            val_label = ctk.CTkLabel(
                col, text=f"{icon} 0",
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=C["green"] if "req" in key else (C["red"] if "err" in key else C["accent"])
            )
            val_label.pack()
            ctk.CTkLabel(
                col, text=label,
                font=ctk.CTkFont(size=10), text_color=C["text_muted"]
            ).pack()
            self.stats_summary_labels[key] = val_label

        # Per-provider cards container
        self.stats_cards_frame = ctk.CTkFrame(self.stats_scroll, fg_color="transparent")
        self.stats_cards_frame.pack(fill="x")

        self.stats_provider_widgets = {}
        self._build_stats_provider_cards()

    def _build_stats_provider_cards(self):
        """Build one card per provider with bar chart of usage."""
        for widget in self.stats_cards_frame.winfo_children():
            widget.destroy()
        self.stats_provider_widgets.clear()

        all_stats = {pid: get_stats(self.config_data, pid) for pid in PROVIDERS}
        max_tok = max((s.get("total_tokens", 0) for s in all_stats.values()), default=1) or 1

        for pid, prov in PROVIDERS.items():
            stats = all_stats[pid]
            if stats["requests"] == 0 and stats["errors"] == 0:
                continue  # Skip providers with no usage

            card = ctk.CTkFrame(
                self.stats_cards_frame, fg_color=C["card"],
                corner_radius=10, border_width=1, border_color=C["border"]
            )
            card.pack(fill="x", pady=3)

            # Row: name + numbers
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(10, 2))

            ctk.CTkLabel(
                row, text=prov["name"],
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=C["text"]
            ).pack(side="left")

            nums = ctk.CTkFrame(row, fg_color="transparent")
            nums.pack(side="right")

            ctk.CTkLabel(
                nums, text=f"✓ {stats['requests']}",
                font=ctk.CTkFont(size=12), text_color=C["green"]
            ).pack(side="left", padx=(0, 12))
            ctk.CTkLabel(
                nums, text=f"✗ {stats['errors']}",
                font=ctk.CTkFont(size=12), text_color=C["red"]
            ).pack(side="left", padx=(0, 12))

            tok = stats.get("total_tokens", 0)
            ctk.CTkLabel(
                nums, text=f"◈ {self._fmt_tokens(tok)} tokens",
                font=ctk.CTkFont(size=12), text_color=C["accent"]
            ).pack(side="left")

            # Token detail row
            pt = stats.get("prompt_tokens", 0)
            ct = stats.get("completion_tokens", 0)
            if pt or ct:
                tok_row = ctk.CTkFrame(card, fg_color="transparent")
                tok_row.pack(fill="x", padx=16, pady=(0, 2))
                ctk.CTkLabel(
                    tok_row,
                    text=f"→ {self._fmt_tokens(pt)} prompt   ← {self._fmt_tokens(ct)} completion",
                    font=ctk.CTkFont(size=10), text_color=C["text_muted"]
                ).pack(side="left")

            # Usage bar
            bar_bg = ctk.CTkFrame(card, fg_color=C["input_bg"], corner_radius=4, height=8)
            bar_bg.pack(fill="x", padx=16, pady=(2, 4))
            bar_bg.pack_propagate(False)

            ratio = stats.get("total_tokens", 0) / max_tok
            bar_fill = ctk.CTkFrame(
                bar_bg, fg_color=C["accent"], corner_radius=4,
                width=max(int(ratio * 600), 4), height=8
            )
            bar_fill.pack(side="left", fill="y")

            # Last error if any
            last_err = stats.get("last_error", "")
            if last_err:
                ctk.CTkLabel(
                    card, text=f"Último error: {last_err[:80]}",
                    font=ctk.CTkFont(size=10), text_color=C["red"],
                    anchor="w"
                ).pack(fill="x", padx=16, pady=(0, 8))
            else:
                ctk.CTkFrame(card, fg_color="transparent", height=4).pack()

            self.stats_provider_widgets[pid] = card

    def _refresh_stats_tab(self, auto=False):
        """Refresh all stats displays."""
        all_stats = {pid: get_stats(self.config_data, pid) for pid in PROVIDERS}
        snapshot = self._stats_snapshot(all_stats)
        if auto and snapshot == self._last_stats_snapshot:
            return
        self._last_stats_snapshot = snapshot

        total_req = sum(s["requests"] for s in all_stats.values())
        total_err = sum(s["errors"] for s in all_stats.values())
        total_tok = sum(s.get("total_tokens", 0) for s in all_stats.values())
        prompt_tok = sum(s.get("prompt_tokens", 0) for s in all_stats.values())
        compl_tok = sum(s.get("completion_tokens", 0) for s in all_stats.values())

        self.stats_summary_labels["total_req"].configure(text=f"✓ {total_req}")
        self.stats_summary_labels["total_err"].configure(text=f"✗ {total_err}")
        self.stats_summary_labels["total_tokens"].configure(text=f"◈ {self._fmt_tokens(total_tok)}")
        self.stats_summary_labels["prompt_tokens"].configure(text=f"→ {self._fmt_tokens(prompt_tok)}")
        self.stats_summary_labels["compl_tokens"].configure(text=f"← {self._fmt_tokens(compl_tok)}")

        self._build_stats_provider_cards()

    @staticmethod
    def _stats_snapshot(all_stats):
        """Build a compact immutable snapshot to detect visible stats changes."""
        return tuple(
            (pid,
             s.get("requests", 0),
             s.get("errors", 0),
             s.get("total_tokens", 0),
             s.get("prompt_tokens", 0),
             s.get("completion_tokens", 0),
             s.get("last_error", ""))
            for pid, s in sorted(all_stats.items())
        )

    @staticmethod
    def _fmt_tokens(n):
        """Format token count for display."""
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.1f}K"
        return str(n)

    # ── GADGET MODE ───────────────────────────────────────────

    def _toggle_gadget(self):
        """Switch between normal mode and gadget-only mode."""
        if self.gadget_mode:
            self._exit_gadget_mode()
            return
        self._enter_gadget_mode()

    def _enter_gadget_mode(self):
        """Hide normal window and show floating gadget."""
        if self.gadget_mode:
            return

        self.gadget_mode = True
        gw = ctk.CTkToplevel(self)
        gw.title("Chamber")
        gw.geometry("350x420")
        gw.resizable(False, False)
        gw.attributes("-topmost", True)
        gw.configure(fg_color=C["bg"])
        gw.overrideredirect(True)  # Borderless
        gw.protocol("WM_DELETE_WINDOW", self._exit_gadget_mode)

        # Make draggable
        gw._drag_x = 0
        gw._drag_y = 0

        def start_drag(e):
            gw._drag_x = e.x
            gw._drag_y = e.y

        def do_drag(e):
            x = gw.winfo_x() + e.x - gw._drag_x
            y = gw.winfo_y() + e.y - gw._drag_y
            gw.geometry(f"+{x}+{y}")

        # Main container with rounded border
        container = ctk.CTkFrame(gw, fg_color=C["surface"], corner_radius=16,
                                 border_width=1, border_color=C["border"])
        container.pack(fill="both", expand=True, padx=2, pady=2)

        # Header row: logo + title + close
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))
        header.bind("<Button-1>", start_drag)
        header.bind("<B1-Motion>", do_drag)

        if self._logo_icon:
            ctk.CTkLabel(header, image=self._logo_icon, text="").pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            header, text="Chamber",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C["text"]
        ).pack(side="left")

        ctk.CTkButton(
            header, text="✕", width=24, height=24,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", hover_color=C["card_hover"],
            text_color=C["text_dim"], corner_radius=6,
            command=self._exit_gadget_mode
        ).pack(side="right")

        ctk.CTkButton(
            header, text="□", width=24, height=24,
            font=ctk.CTkFont(size=12),
            fg_color="transparent", hover_color=C["card_hover"],
            text_color=C["text_dim"], corner_radius=6,
            command=self._exit_gadget_mode
        ).pack(side="right", padx=2)

        # Status row
        status_row = ctk.CTkFrame(container, fg_color="transparent")
        status_row.pack(fill="x", padx=12, pady=2)

        self._gadget_dot = ctk.CTkLabel(
            status_row, text="●", font=ctk.CTkFont(size=12), text_color=C["red"]
        )
        self._gadget_dot.pack(side="left")
        self._gadget_status = ctk.CTkLabel(
            status_row, text="Detenido",
            font=ctk.CTkFont(size=12), text_color=C["text_dim"]
        )
        self._gadget_status.pack(side="left", padx=(6, 0))

        # Provider row
        prov_row = ctk.CTkFrame(container, fg_color="transparent")
        prov_row.pack(fill="x", padx=12, pady=2)

        ctk.CTkLabel(
            prov_row, text="Proveedor:",
            font=ctk.CTkFont(size=11), text_color=C["text_muted"]
        ).pack(side="left")
        self._gadget_provider = ctk.CTkLabel(
            prov_row, text="—",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=C["accent"]
        )
        self._gadget_provider.pack(side="left", padx=(6, 0))

        # Stats row
        stats_row = ctk.CTkFrame(container, fg_color="transparent")
        stats_row.pack(fill="x", padx=12, pady=(2, 4))

        all_stats = {pid: get_stats(self.config_data, pid) for pid in PROVIDERS}
        total_req = sum(s["requests"] for s in all_stats.values())
        total_err = sum(s["errors"] for s in all_stats.values())

        self._gadget_reqs = ctk.CTkLabel(
            stats_row, text=f"✓ {total_req}",
            font=ctk.CTkFont(size=12), text_color=C["green"]
        )
        self._gadget_reqs.pack(side="left")
        self._gadget_errs = ctk.CTkLabel(
            stats_row, text=f"✗ {total_err}",
            font=ctk.CTkFont(size=12), text_color=C["red"]
        )
        self._gadget_errs.pack(side="left", padx=(16, 0))

        total_tok = sum(s.get("total_tokens", 0) for s in all_stats.values())
        self._gadget_tokens = ctk.CTkLabel(
            stats_row, text=f"◈ {self._fmt_tokens(total_tok)}",
            font=ctk.CTkFont(size=12), text_color=C["accent"]
        )
        self._gadget_tokens.pack(side="left", padx=(16, 0))

        # Mini chatbot
        chat_frame = ctk.CTkFrame(container, fg_color="transparent")
        chat_frame.pack(fill="both", expand=True, padx=12, pady=(4, 4))

        self._gadget_chat_box = ctk.CTkTextbox(
            chat_frame,
            font=ctk.CTkFont(size=11),
            fg_color=C["input_bg"], text_color=C["text"],
            corner_radius=8, border_width=1, border_color=C["border"],
            wrap="word"
        )
        self._gadget_chat_box.pack(fill="both", expand=True)
        self._gadget_chat_box.configure(state="disabled")
        self._render_gadget_chat_history()

        gadget_input_row = ctk.CTkFrame(chat_frame, fg_color="transparent")
        gadget_input_row.pack(fill="x", pady=(6, 0))

        self._gadget_chat_input = ctk.CTkEntry(
            gadget_input_row,
            placeholder_text="Mensaje...",
            height=32,
            font=ctk.CTkFont(size=11),
            fg_color=C["input_bg"], border_color=C["border"],
            text_color=C["text"], corner_radius=8
        )
        self._gadget_chat_input.pack(side="left", fill="x", expand=True)
        self._gadget_chat_input.bind("<Return>", lambda e: self._send_gadget_message())

        self._gadget_send_btn = ctk.CTkButton(
            gadget_input_row, text="Enviar", width=62, height=32,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C["accent"], hover_color=C["accent_hover"],
            text_color="#fff", corner_radius=8,
            command=self._send_gadget_message
        )
        self._gadget_send_btn.pack(side="left", padx=(6, 0))

        # Bottom bar with quick actions
        bottom = ctk.CTkFrame(container, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(4, 8))

        ctk.CTkButton(
            bottom, text="▶", width=36, height=28,
            font=ctk.CTkFont(size=13),
            fg_color=C["green"], hover_color=C["green_hover"],
            text_color="#fff", corner_radius=6,
            command=self._start_server
        ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            bottom, text="■", width=36, height=28,
            font=ctk.CTkFont(size=13),
            fg_color=C["red"], hover_color=C["red_hover"],
            text_color="#fff", corner_radius=6,
            command=self._stop_server
        ).pack(side="left")

        self.gadget_window = gw
        self.withdraw()
        self._update_gadget()

    def _exit_gadget_mode(self):
        """Close gadget and restore normal window."""
        self.gadget_mode = False
        if self.gadget_window and self.gadget_window.winfo_exists():
            self.gadget_window.destroy()
        self.gadget_window = None
        self.deiconify()
        self.lift()
        self.focus_force()
        if hasattr(self, "chat_display"):
            self._render_chat_history()

    def _update_gadget(self):
        """Update gadget widget with current status."""
        if not self.gadget_window or not self.gadget_window.winfo_exists():
            return

        running = self.roulette and self.api_server and self.api_server.running
        if running:
            port = self.config_data.get("server_port", 11411)
            self._gadget_dot.configure(text_color=C["green"])
            self._gadget_status.configure(text=f"Activo :{port}", text_color=C["text"])
            current = self.roulette.get_current_provider_id()
            if current:
                self._gadget_provider.configure(text=PROVIDERS.get(current, {}).get("name", current))
            else:
                self._gadget_provider.configure(text="—")
        else:
            self._gadget_dot.configure(text_color=C["red"])
            self._gadget_status.configure(text="Detenido", text_color=C["text_dim"])
            self._gadget_provider.configure(text="—")

        all_stats = {pid: get_stats(self.config_data, pid) for pid in PROVIDERS}
        total_req = sum(s["requests"] for s in all_stats.values())
        total_err = sum(s["errors"] for s in all_stats.values())
        total_tok = sum(s.get("total_tokens", 0) for s in all_stats.values())
        self._gadget_reqs.configure(text=f"✓ {total_req}")
        self._gadget_errs.configure(text=f"✗ {total_err}")
        self._gadget_tokens.configure(text=f"◈ {self._fmt_tokens(total_tok)}")

        if not self._closing:
            self.gadget_window.after(2000, self._update_gadget)

    def _append_gadget_chat(self, speaker, text):
        """Append a chat line to the gadget chat box."""
        if not self.gadget_window or not self.gadget_window.winfo_exists():
            return
        self._gadget_chat_box.configure(state="normal")
        self._gadget_chat_box.insert("end", f"{speaker}: {text}\n\n")
        self._gadget_chat_box.see("end")
        self._gadget_chat_box.configure(state="disabled")

    def _render_gadget_chat_history(self):
        if not self.gadget_window or not self.gadget_window.winfo_exists():
            return
        self._gadget_chat_box.configure(state="normal")
        self._gadget_chat_box.delete("1.0", "end")
        self._gadget_chat_box.configure(state="disabled")
        for msg in self.chat_messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                self._append_gadget_chat("Tu", content)
            elif role == "assistant":
                self._append_gadget_chat("AI", content)

    def _send_gadget_message(self):
        """Send a chat message from gadget mode."""
        if not self.gadget_window or not self.gadget_window.winfo_exists():
            return
        text = self._gadget_chat_input.get().strip()
        if not text:
            return
        if not self.roulette:
            self._append_gadget_chat("Sistema", "Inicia el servidor primero")
            return

        self._gadget_chat_input.delete(0, "end")
        self._gadget_send_btn.configure(state="disabled", text="...")
        self.chat_messages.append({"role": "user", "content": text})
        self._persist_chat_state()
        self._append_gadget_chat("Tu", text)

        payload_messages = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in self.chat_messages
            if msg.get("role") in ("user", "assistant")
        ]

        def do_request():
            try:
                result = self.roulette.chat_completion(payload_messages, stream=False)
                if self._closing:
                    return
                if "choices" not in result or not result["choices"]:
                    err = result.get("error", {}).get("message", "Respuesta inválida del proveedor")
                    self.after(0, lambda e=err: self._append_gadget_chat("Sistema", f"Error: {e}"))
                else:
                    content = result["choices"][0]["message"]["content"]
                    model = result.get("model", "")
                    provider = self.roulette.get_current_provider_id()
                    prov_name = PROVIDERS.get(provider, {}).get("name", provider)
                    tag = f"{prov_name}" + (f" · {model}" if model else "")
                    self.chat_messages.append(
                        {"role": "assistant", "content": content, "provider_tag": tag}
                    )
                    self._persist_chat_state()
                    self.after(0, lambda c=content: self._append_gadget_chat("AI", c))
            except Exception as e:
                if self._closing:
                    return
                self.after(0, lambda err=e: self._append_gadget_chat("Sistema", f"Error: {err}"))
            finally:
                if not self._closing:
                    self.after(0, lambda: self._gadget_send_btn.configure(state="normal", text="Enviar"))

        threading.Thread(target=do_request, daemon=True).start()

    # ══════════════════════════════════════════════════════════
    #  SERVER CONTROL
    # ══════════════════════════════════════════════════════════

    def _start_server(self):
        self._save_all(quiet=True)

        any_active = any(
            is_enabled(self.config_data, pid) and get_api_key(self.config_data, pid).strip()
            for pid in PROVIDERS
        )
        if not any_active:
            messagebox.showwarning(
                "Sin proveedores",
                "Activa al menos un proveedor con su API Key antes de iniciar."
            )
            return

        port = int(self.port_entry.get() or 11411)
        self.config_data["server_port"] = port
        save_config(self.config_data)
        if hasattr(self, "port_display_label"):
            self.port_display_label.configure(text=str(port))

        self.roulette = Roulette(
            self.config_data,
            on_switch=self._on_provider_switch,
            on_log=self._append_log
        )
        host = self.config_data.get("server_host", "0.0.0.0")
        self.api_server = APIServer(
            self.roulette, port=port, host=host, on_log=self._append_log
        )
        self.api_server.start()

        self._append_log(f"Servidor iniciado — http://localhost:{port}/v1")
        self._append_log(f"Proveedores activos: {self.roulette.get_active_count()}")
        current = self.roulette.get_current_provider_id()
        if current:
            self._append_log(f"Proveedor actual: {PROVIDERS[current]['name']}")

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._update_status()

    def _stop_server(self):
        if self.api_server:
            self.api_server.stop()
        self._append_log("Servidor detenido")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.roulette = None
        self.api_server = None
        self._update_status()

    # ══════════════════════════════════════════════════════════
    #  CALLBACKS & HELPERS
    # ══════════════════════════════════════════════════════════

    def _on_provider_switch(self, provider_id, reason):
        self.after(0, self._update_status)

    def _append_log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        self.log_lines.append(line)
        if len(self.log_lines) > 500:
            self.log_lines = self.log_lines[-400:]

        def _update():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.after(0, _update)

    def _clear_log(self):
        self.log_lines.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _update_status(self):
        running = self.roulette and self.api_server and self.api_server.running
        if running:
            port = self.config_data.get("server_port", 11411)
            count = self.roulette.get_active_count()
            current = self.roulette.get_current_provider_id()

            self.status_dot.configure(text_color=C["green"])
            self.status_label.configure(text=f"{self._t('running_on')} — :{port}")
            self.status_detail.configure(text=f"{count} {self._t('providers_connected')}")

            if current:
                name = PROVIDERS.get(current, {}).get("name", current)
                self.current_provider_label.configure(text=name)
            else:
                self.current_provider_label.configure(text="—")
        else:
            self.status_dot.configure(text_color=C["red"])
            self.status_label.configure(text=self._t("server_stopped"))
            self.status_detail.configure(text=self._t("no_connection"))
            self.current_provider_label.configure(text="—")

        for pid, widgets in self.provider_widgets.items():
            stats = get_stats(self.config_data, pid)
            widgets["stats_label"].configure(
                text=f"✓ {stats['requests']}   ✗ {stats['errors']}"
            )

    def _update_status_loop(self):
        if self._closing:
            return
        self._update_status()
        if hasattr(self, "stats_summary_labels") and self.current_tab == "stats":
            self._refresh_stats_tab(auto=True)
        if self.gadget_window and self.gadget_window.winfo_exists():
            self._update_gadget()
        if not self._closing:
            self.after(2000, self._update_status_loop)

    def _save_all(self, quiet=False):
        for pid, widgets in self.provider_widgets.items():
            set_api_key(self.config_data, pid, widgets["key_entry"].get().strip())
            set_enabled(self.config_data, pid, widgets["enabled_var"].get())
            set_selected_model(self.config_data, pid, widgets["model_var"].get())

        port = self.port_entry.get().strip()
        if port.isdigit():
            self.config_data["server_port"] = int(port)
        if hasattr(self, "system_entry"):
            self.config_data["system_prompt"] = self.system_entry.get().strip()
        self._save_conversations()

        save_config(self.config_data)
        if self.roulette:
            self.roulette.refresh()
        if not quiet:
            self._append_log("Configuración guardada")

    def _reset_exhausted(self):
        if self.roulette:
            self.roulette.reset_exhausted()
            self._append_log("Proveedores agotados reseteados")
        else:
            messagebox.showinfo("Info", "El servidor no está activo.")

    def _reset_all_stats(self):
        reset_stats(self.config_data)
        save_config(self.config_data)
        self._update_status()
        self._append_log("Estadísticas reseteadas")

    def _sync_models(self, provider_id):
        """Fetch real models from the provider API and update the dropdown."""
        widgets = self.provider_widgets.get(provider_id)
        if not widgets:
            return

        api_key = widgets["key_entry"].get().strip()
        if not api_key:
            self._append_log(f"⚠ {PROVIDERS[provider_id]['name']}: ingresa una API key primero")
            return

        prov = PROVIDERS[provider_id]
        widgets["sync_btn"].configure(text="...", state="disabled")
        self._append_log(f"⟳ Sincronizando modelos de {prov['name']}...")

        def do_fetch():
            try:
                url = f"{prov['base_url']}/models"
                headers = {
                    prov["api_key_header"]: f"{prov['api_key_prefix']}{api_key}",
                    "Content-Type": "application/json",
                }
                headers.update(prov.get("extra_headers", {}))

                resp = http_requests.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    model_list = data.get("data", data.get("models", []))
                    model_ids = []
                    for m in model_list:
                        if isinstance(m, dict):
                            model_ids.append(m.get("id", m.get("name", "")))
                        elif isinstance(m, str):
                            model_ids.append(m)
                    model_ids = [mid for mid in model_ids if mid]

                    if model_ids:
                        # Sort and limit
                        model_ids.sort()
                        if len(model_ids) > 50:
                            model_ids = model_ids[:50]

                        # Keep current selection if still valid
                        current = widgets["model_var"].get()

                        def update_ui():
                            widgets["model_menu"].configure(values=model_ids)
                            if current not in model_ids:
                                widgets["model_var"].set(model_ids[0])
                            widgets["sync_btn"].configure(text="⟳", state="normal")
                            self._append_log(
                                f"✓ {prov['name']}: {len(model_ids)} modelos encontrados"
                            )
                        if not self._closing:
                            self.after(0, update_ui)
                        return

                if not self._closing:
                    self.after(0, lambda: (
                        widgets["sync_btn"].configure(text="⟳", state="normal"),
                        self._append_log(
                            f"✗ {prov['name']}: HTTP {resp.status_code} al obtener modelos"
                        )
                    ))
            except Exception as e:
                if not self._closing:
                    self.after(0, lambda: (
                        widgets["sync_btn"].configure(text="⟳", state="normal"),
                    self._append_log(f"✗ {prov['name']}: {e}")
                ))

        threading.Thread(target=do_fetch, daemon=True).start()

    def on_closing(self):
        self._closing = True
        try:
            self._save_all(quiet=True)
        except Exception:
            pass
        try:
            if self.gadget_window and self.gadget_window.winfo_exists():
                self.gadget_window.destroy()
        except Exception:
            pass
        try:
            if self.api_server:
                self.api_server.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
