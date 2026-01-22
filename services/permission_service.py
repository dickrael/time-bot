"""
Permission Service for Time Bot.

Handles admin permission checks for group commands.
"""

import logging
from typing import TYPE_CHECKING
from functools import wraps

from pyrogram.enums import ChatMemberStatus, ChatType

if TYPE_CHECKING:
    from pyrogram import Client
    from pyrogram.types import Message

logger = logging.getLogger(__name__)


class PermissionService:
    """
    Service for checking user permissions in chats.
    """

    # Chat member statuses that have admin privileges
    ADMIN_STATUSES = {
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR
    }

    async def is_admin(
        self,
        client: "Client",
        chat_id: int,
        user_id: int
    ) -> bool:
        """
        Check if a user is an admin in a chat.

        Args:
            client: Pyrogram client
            chat_id: Chat to check
            user_id: User to check

        Returns:
            True if user is owner or admin, False otherwise
        """
        try:
            member = await client.get_chat_member(chat_id, user_id)
            return member.status in self.ADMIN_STATUSES
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            return False

    async def is_private_chat(self, message: "Message") -> bool:
        """Check if message is from a private chat."""
        return message.chat.type == ChatType.PRIVATE

    async def check_admin_or_private(
        self,
        client: "Client",
        message: "Message"
    ) -> bool:
        """
        Check if command should be allowed.

        Returns True if:
        - Chat is private (user is talking directly to bot)
        - User is an admin in the group

        Returns False otherwise.
        """
        # Private chats always allowed
        if await self.is_private_chat(message):
            return True

        # Check admin in groups
        return await self.is_admin(
            client,
            message.chat.id,
            message.from_user.id
        )


def admin_only(func):
    """
    Decorator for admin-only command handlers.

    Usage:
        @admin_only
        async def handle_addtime(client, message, services):
            ...

    The decorated function must accept (client, message, services) as arguments.
    services must have a 'permissions' attribute.
    """
    @wraps(func)
    async def wrapper(client, message, services):
        # Check permissions
        if not await services.permissions.check_admin_or_private(client, message):
            await message.reply(
                "⛔ **Permission Denied**\n\n"
                "This command is only available to group administrators."
            )
            return

        # Call the actual handler
        return await func(client, message, services)

    return wrapper
