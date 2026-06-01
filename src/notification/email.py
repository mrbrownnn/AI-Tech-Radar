class EmailNotifier:
    """Future email delivery adapter."""

    async def send_digest(self, subject: str, body: str) -> None:
        raise NotImplementedError("Email delivery is planned for a later phase")

