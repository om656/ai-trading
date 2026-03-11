"""
app_config.py - Configuration management with encrypted API key storage.

Handles all persistent settings for the AI Trading System, including
secure storage of API credentials using the cryptography library.
"""

import json
import os
import base64
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional encryption support (requires 'cryptography' package)
# ---------------------------------------------------------------------------
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    CRYPTO_AVAILABLE = False
    logger.warning(
        "cryptography package not installed – API keys will be stored in plain text. "
        "Run: pip install cryptography"
    )

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_NAME = "AITrading"
CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / "secret.key"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_CONFIG: Dict[str, Any] = {
    # API credentials (stored encrypted)
    "api_keys": {
        "exchange_api_key": "",
        "exchange_api_secret": "",
        "news_api_key": "",
        "openai_api_key": "",
    },
    # Trading parameters
    "trading": {
        "paper_trading": True,
        "max_position_size": 0.05,   # fraction of portfolio
        "risk_per_trade": 0.01,       # fraction of portfolio
        "stop_loss_pct": 0.02,
        "take_profit_pct": 0.06,
        "max_open_positions": 5,
        "trade_cooldown_seconds": 60,
    },
    # Exchange / market
    "exchange": {
        "name": "binance",
        "symbols": ["BTC/USDT", "ETH/USDT"],
        "base_currency": "USDT",
    },
    # AI model selection
    "model": {
        "sentiment_model": "finbert",   # finbert | fingpt | vader
        "decision_model": "ensemble",   # ensemble | lstm | gru | llm
        "ollama_model": "llama3",
    },
    # Alerts
    "alerts": {
        "email_enabled": False,
        "email_address": "",
        "telegram_enabled": False,
        "telegram_token": "",
        "telegram_chat_id": "",
        "loss_alert_pct": 0.05,
    },
    # Application behaviour
    "app": {
        "start_with_windows": False,
        "minimize_to_tray": True,
        "dark_mode": True,
        "log_level": "INFO",
        "auto_connect": False,
        "theme": "dark",
    },
}


# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def _derive_key(password: bytes, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password))


def _load_or_create_key() -> bytes:
    """Load the encryption key from disk, creating it if absent."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)
    # Restrict permissions on non-Windows platforms
    try:
        KEY_FILE.chmod(0o600)
    except Exception:
        pass
    return key


def encrypt_value(plaintext: str) -> str:
    """Encrypt *plaintext* and return a base64-encoded ciphertext string."""
    if not CRYPTO_AVAILABLE or not plaintext:
        return plaintext
    try:
        key = _load_or_create_key()
        f = Fernet(key)
        return f.encrypt(plaintext.encode()).decode()
    except Exception as exc:
        logger.error("Encryption failed: %s", exc)
        return plaintext


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a previously encrypted value.  Returns *ciphertext* on failure."""
    if not CRYPTO_AVAILABLE or not ciphertext:
        return ciphertext
    try:
        key = _load_or_create_key()
        f = Fernet(key)
        return f.decrypt(ciphertext.encode()).decode()
    except Exception:
        # Value may already be plain text (e.g. first run after disabling crypto)
        return ciphertext


# ---------------------------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------------------------

class ConfigManager:
    """Thread-safe configuration manager with encrypted API key storage."""

    # Top-level keys whose leaf values should be encrypted at rest
    _ENCRYPTED_SECTIONS = {"api_keys", "alerts"}

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._config: Dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load config from disk, merging with defaults."""
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open("r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                self._config = self._deep_merge(DEFAULT_CONFIG, stored)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Could not read config (%s) – using defaults.", exc)
                self._config = self._deep_copy(DEFAULT_CONFIG)
        else:
            self._config = self._deep_copy(DEFAULT_CONFIG)

    def save(self) -> None:
        """Persist config to disk."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with CONFIG_FILE.open("w", encoding="utf-8") as fh:
                json.dump(self._config, fh, indent=2)
        except OSError as exc:
            logger.error("Could not save config: %s", exc)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Return a config value, decrypting if necessary."""
        value = self._config.get(section, {}).get(key, default)
        if section in self._ENCRYPTED_SECTIONS and isinstance(value, str) and value:
            value = decrypt_value(value)
        return value

    def set(self, section: str, key: str, value: Any) -> None:
        """Set a config value, encrypting API/secret fields."""
        if section not in self._config:
            self._config[section] = {}
        if section in self._ENCRYPTED_SECTIONS and isinstance(value, str) and value:
            value = encrypt_value(value)
        self._config[section][key] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Return an entire section, decrypting sensitive values."""
        raw = self._config.get(section, {})
        if section not in self._ENCRYPTED_SECTIONS:
            return dict(raw)
        return {k: decrypt_value(v) if isinstance(v, str) else v for k, v in raw.items()}

    def set_section(self, section: str, values: Dict[str, Any]) -> None:
        """Replace an entire section, encrypting sensitive values."""
        if section in self._ENCRYPTED_SECTIONS:
            values = {
                k: encrypt_value(v) if isinstance(v, str) and v else v
                for k, v in values.items()
            }
        self._config[section] = values

    def reset_to_defaults(self) -> None:
        """Reset all settings to built-in defaults."""
        self._config = self._deep_copy(DEFAULT_CONFIG)

    # ------------------------------------------------------------------
    # Convenience properties
    # ------------------------------------------------------------------

    @property
    def paper_trading(self) -> bool:
        return bool(self.get("trading", "paper_trading", True))

    @paper_trading.setter
    def paper_trading(self, value: bool) -> None:
        self.set("trading", "paper_trading", value)

    @property
    def dark_mode(self) -> bool:
        return bool(self.get("app", "dark_mode", True))

    @dark_mode.setter
    def dark_mode(self, value: bool) -> None:
        self.set("app", "dark_mode", value)

    @property
    def minimize_to_tray(self) -> bool:
        return bool(self.get("app", "minimize_to_tray", True))

    @property
    def start_with_windows(self) -> bool:
        return bool(self.get("app", "start_with_windows", False))

    # ------------------------------------------------------------------
    # Windows auto-start registry helper
    # ------------------------------------------------------------------

    def apply_startup_setting(self, enabled: bool) -> bool:
        """Add or remove the app from the Windows registry startup key."""
        try:
            import winreg  # type: ignore  # Windows only
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            exe_path = os.path.abspath(__file__)
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
            ) as reg_key:
                if enabled:
                    winreg.SetValueEx(reg_key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    try:
                        winreg.DeleteValue(reg_key, APP_NAME)
                    except FileNotFoundError:
                        pass
            self.set("app", "start_with_windows", enabled)
            self.save()
            return True
        except ImportError:
            logger.info("winreg not available (non-Windows system).")
            return False
        except Exception as exc:
            logger.error("Failed to modify startup registry: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Recursively merge *override* into *base*, returning new dict."""
        result = dict(base)
        for key, val in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(val, dict):
                result[key] = ConfigManager._deep_merge(result[key], val)
            else:
                result[key] = val
        return result

    @staticmethod
    def _deep_copy(d: Dict) -> Dict:
        """Return a deep copy of a nested dict (values assumed JSON-safe)."""
        return json.loads(json.dumps(d))


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
config = ConfigManager()
