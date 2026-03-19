from datetime import datetime, timedelta

from croniter import croniter

from keep_alive.config import CRON_PRESETS


class CronSchedule:
    """Determina quando o simulador deve estar ativo com base em cron."""

    def __init__(self, expression: str):
        resolved = CRON_PRESETS.get(expression.lower().strip(), expression)
        self.expression = resolved
        self.original = expression

        if not croniter.is_valid(self.expression):
            raise ValueError(
                f"Cron expression inválida: '{expression}'\n"
                f"Formato: MIN HORA DIA MÊS DIA_SEMANA\n"
                f"Exemplos: '* 8-18 * * 1-5', '*/5 9-17 * * *'\n"
                f"Presets: {', '.join(sorted(CRON_PRESETS.keys()))}"
            )

    def is_active_now(self) -> bool:
        return croniter.match(self.expression, datetime.now())

    def seconds_until_next_active(self) -> float:
        now = datetime.now()
        next_match = croniter(self.expression, now).get_next(datetime)
        return max(0, (next_match - now).total_seconds())

    def next_active_datetime(self) -> datetime:
        return croniter(self.expression, datetime.now()).get_next(datetime)

    def seconds_until_inactive(self) -> float:
        now = datetime.now()
        check = now
        for _ in range(1440):
            check = check + timedelta(minutes=1)
            if not croniter.match(self.expression, check):
                return (check - now).total_seconds()
        return float("inf")

    def format_status(self) -> str:
        label = self.expression
        if self.original.lower().strip() in CRON_PRESETS:
            label = f"{self.expression} (preset: {self.original})"
        return label

    def format_next_window(self) -> str:
        if self.is_active_now():
            return "agora (ativo)"

        secs = self.seconds_until_next_active()
        next_dt = self.next_active_datetime()
        hours, remainder = divmod(int(secs), 3600)
        minutes, _ = divmod(remainder, 60)

        if hours >= 24:
            return f"em {hours // 24}d{hours % 24}h (~{next_dt.strftime('%d/%m %H:%M')})"
        if hours > 0:
            return f"em {hours}h{minutes:02d}m (~{next_dt.strftime('%H:%M')})"
        return f"em {minutes}min (~{next_dt.strftime('%H:%M')})"
