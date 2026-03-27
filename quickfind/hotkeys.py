"""Register global hotkeys on Windows using ctypes."""

import ctypes
import ctypes.wintypes
import threading

# Windows modifier flags
MOD_ALT = 0x0001
MOD_CTRL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

# Virtual key codes
VK_MAP: dict[str, int] = {}

# A-Z
for _c in range(ord("A"), ord("Z") + 1):
    VK_MAP[chr(_c)] = _c

# 0-9
for _n in range(10):
    VK_MAP[str(_n)] = 0x30 + _n

# F1-F12
for _f in range(1, 13):
    VK_MAP[f"F{_f}"] = 0x70 + _f - 1

VK_MAP["SPACE"] = 0x20

MODIFIER_MAP: dict[str, int] = {
    "WIN": MOD_WIN,
    "ALT": MOD_ALT,
    "CTRL": MOD_CTRL,
    "SHIFT": MOD_SHIFT,
}

WM_HOTKEY = 0x0312


def _parse_combo(key_combo: str) -> tuple[int, int]:
    """Parse a key combo string like 'Win+Alt+F' into (modifiers, vk_code).

    Raises ValueError if the combo is invalid.
    """
    parts = [p.strip().upper() for p in key_combo.split("+")]
    if len(parts) < 2:
        raise ValueError(f"Invalid key combo (need modifier+key): {key_combo}")

    modifiers = 0
    vk_code = 0

    key_part = parts[-1]
    mod_parts = parts[:-1]

    for mod in mod_parts:
        if mod not in MODIFIER_MAP:
            raise ValueError(f"Unknown modifier: {mod}")
        modifiers |= MODIFIER_MAP[mod]

    if key_part not in VK_MAP:
        raise ValueError(f"Unknown key: {key_part}")
    vk_code = VK_MAP[key_part]

    return modifiers, vk_code


class GlobalHotkey:
    """Register and listen for a global hotkey on Windows."""

    def __init__(self, key_combo: str, callback: callable) -> None:
        self._key_combo = key_combo
        self._callback = callback
        self._modifiers, self._vk_code = _parse_combo(key_combo)
        self._registered = False
        self._thread: threading.Thread | None = None
        self._hotkey_id = hash(key_combo) & 0xFFFF  # Unique ID for this hotkey
        self._stop_event = threading.Event()

    def register(self) -> bool:
        """Register the global hotkey and start the listener thread.

        Returns True if registration succeeded.
        """
        if self._registered:
            return True

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listener, daemon=True)
        self._thread.start()

        # Wait briefly for the thread to register the hotkey
        self._stop_event.wait(timeout=1.0)

        return self._registered

    def _listener(self) -> None:
        """Background thread: register hotkey, pump messages, call callback."""
        try:
            user32 = ctypes.windll.user32
            result = user32.RegisterHotKey(
                None, self._hotkey_id, self._modifiers, self._vk_code
            )
            self._registered = bool(result)
            self._stop_event.set()  # Signal that registration attempt is done

            if not self._registered:
                return

            msg = ctypes.wintypes.MSG()
            while not self._stop_event.is_set():
                # GetMessageW blocks until a message arrives; timeout via PeekMessage
                ret = user32.PeekMessageW(
                    ctypes.byref(msg), None, 0, 0, 0x0001  # PM_REMOVE
                )
                if ret and msg.message == WM_HOTKEY:
                    try:
                        self._callback()
                    except Exception:
                        pass
                else:
                    # Avoid busy loop — use MsgWaitForMultipleObjectsEx
                    user32.MsgWaitForMultipleObjectsEx(
                        0, None, 100, 0x04FF, 0x0004  # QS_ALLINPUT, MWMO_INPUTAVAILABLE
                    )
        except Exception:
            self._registered = False
            self._stop_event.set()

    def unregister(self) -> None:
        """Unregister the global hotkey and stop the listener."""
        if not self._registered:
            return

        self._stop_event.set()

        try:
            ctypes.windll.user32.UnregisterHotKey(None, self._hotkey_id)
        except Exception:
            pass

        self._registered = False
        self._thread = None

    def is_registered(self) -> bool:
        """Return whether the hotkey is currently registered."""
        return self._registered
