from aiogram.utils.chat_action import ChatActionSender


def typing_action(bot, chat_id):
    return ChatActionSender.typing(bot=bot, chat_id=chat_id)
