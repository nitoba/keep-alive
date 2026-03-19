import logging
import platform
import random
import time
from datetime import datetime, timezone

import pyautogui

from keep_alive.schedule import CronSchedule

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

log = logging.getLogger("discord-online")


def is_discord_running() -> bool:
    try:
        import psutil

        discord_names = {"discord", "discord.exe", "discordcanary", "discordptb"}
        for proc in psutil.process_iter(["name"]):
            name = (proc.info["name"] or "").lower()
            if name in discord_names:
                return True
        return False
    except Exception:
        return True


def find_discord_window() -> bool:
    try:
        windows = pyautogui.getWindowsWithTitle("Discord")
        if windows:
            win = windows[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.3)
            log.info(f"🪟 Janela focada: '{win.title}'")
            return True
    except Exception:
        pass
    return False


def simulate_mouse_jiggle() -> str:
    current_x, current_y = pyautogui.position()
    offset_x = random.choice([-1, 1]) * random.randint(1, 4)
    offset_y = random.choice([-1, 1]) * random.randint(1, 4)
    duration = random.uniform(0.1, 0.3)

    pyautogui.moveTo(current_x + offset_x, current_y + offset_y, duration=duration)
    time.sleep(random.uniform(0.05, 0.15))
    pyautogui.moveTo(current_x, current_y, duration=duration)
    return f"mouse jiggle ±{abs(offset_x)}px,±{abs(offset_y)}px"


def simulate_keyboard_activity() -> str:
    ghost_keys = ["shift", "shift", "shift", "capslock"]
    key = random.choice(ghost_keys)

    if key == "capslock":
        pyautogui.press("capslock")
        time.sleep(0.05)
        pyautogui.press("capslock")
        return "keyboard: capslock toggle (neutralizado)"

    pyautogui.keyDown(key)
    time.sleep(random.uniform(0.03, 0.08))
    pyautogui.keyUp(key)
    return f"keyboard: {key} tap"


def simulate_combined() -> str:
    if random.random() < 0.6:
        return simulate_mouse_jiggle()
    return simulate_keyboard_activity()


METHODS = {
    "mouse": simulate_mouse_jiggle,
    "keyboard": simulate_keyboard_activity,
    "combined": simulate_combined,
}


class ActivitySimulator:
    def __init__(self, interval: int, method: str, focus: bool, schedule: CronSchedule):
        self.interval = interval
        self.method = method
        self.focus = focus
        self.schedule = schedule
        self.running = True
        self.start_time = datetime.now(timezone.utc)
        self.tick_count = 0
        self._simulate_fn = METHODS[method]

    def stop(self, *_args):
        log.info("⏹️  Sinal de parada recebido...")
        self.running = False

    def _format_uptime(self) -> str:
        delta = datetime.now(timezone.utc) - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}h{minutes:02d}m{seconds:02d}s"

    def _add_jitter(self) -> float:
        jitter = self.interval * random.uniform(-0.2, 0.2)
        return max(10, self.interval + jitter)

    def _interruptible_sleep(self, seconds: float):
        elapsed = 0.0
        while elapsed < seconds and self.running:
            chunk = min(1.0, seconds - elapsed)
            time.sleep(chunk)
            elapsed += chunk

    def _wait_for_active_window(self):
        wait_secs = self.schedule.seconds_until_next_active()
        if wait_secs <= 0:
            return

        log.info(
            f"😴 Fora do horário ativo (cron: {self.schedule.expression}). "
            f"Próximo: {self.schedule.format_next_window()}"
        )

        log_interval = 300
        waited = 0.0
        while not self.schedule.is_active_now() and self.running:
            sleep_chunk = min(30.0, log_interval - (waited % log_interval))
            self._interruptible_sleep(sleep_chunk)
            waited += sleep_chunk
            if waited % log_interval < 31 and not self.schedule.is_active_now():
                log.info(f"😴 Aguardando... retoma {self.schedule.format_next_window()}")

        if self.running:
            log.info("⏰ Horário ativo! Retomando simulação...")

    def run(self):
        log.info("=" * 60)
        log.info("🟢 Discord Always Online — Input Simulator")
        log.info(f"   SO         : {platform.system()} {platform.release()}")
        log.info(f"   Método     : {self.method}")
        log.info(f"   Intervalo  : ~{self.interval}s (±20% jitter)")
        log.info(f"   Auto-foco  : {'sim' if self.focus else 'não'}")
        log.info(f"   Cron       : {self.schedule.format_status()}")
        log.info("   Parar      : Ctrl+C")
        log.info("=" * 60)

        if self.schedule.expression == "* * * * *":
            log.info("💡 Dica: use --cron 'comercial' para horário comercial (8-18h, seg-sex)")

        if is_discord_running():
            log.info("✅ Discord detectado em execução.")
        else:
            log.warning(
                "⚠️  Discord não detectado! O script vai continuar, "
                "mas certifique-se de que o Discord esteja aberto."
            )

        while self.running:
            try:
                if not self.schedule.is_active_now():
                    self._wait_for_active_window()
                    if not self.running:
                        break
                    continue

                if self.tick_count % 5 == 0 and not is_discord_running():
                    log.warning("⚠️  Discord não detectado. Aguardando...")
                    self._interruptible_sleep(self.interval)
                    continue

                if self.focus:
                    find_discord_window()

                result = self._simulate_fn()
                self.tick_count += 1

                remaining = self.schedule.seconds_until_inactive()
                if remaining < float("inf"):
                    rem_hours, rem_rest = divmod(int(remaining), 3600)
                    rem_minutes, _ = divmod(rem_rest, 60)
                    window_info = f"Restante: {rem_hours:02d}h{rem_minutes:02d}m"
                else:
                    window_info = "24/7"

                log.info(
                    f"💓 #{self.tick_count:04d} │ {result} │ "
                    f"Uptime: {self._format_uptime()} │ "
                    f"{window_info}"
                )
                self._interruptible_sleep(self._add_jitter())
            except KeyboardInterrupt:
                self.stop()
            except Exception as exc:
                log.error(f"❌ Erro: {exc}")
                time.sleep(5)

        log.info(f"👋 Encerrado após {self.tick_count} ciclos ({self._format_uptime()})")
