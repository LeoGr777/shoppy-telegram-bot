"""Telegram handlers, keyboards and application setup."""

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.error import BadRequest
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)

from shoppy.db import Database
from shoppy.parsing import (
    command_pattern,
    get_command_args,
    ids_except,
    parse_numbers,
    resolve_numbers,
    split_items,
)

logger = logging.getLogger(__name__)


def main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("➕ Add item", switch_inline_query_current_chat="/add ")],
            [InlineKeyboardButton("⛔ Remove item", switch_inline_query_current_chat="/done ")],
            [InlineKeyboardButton("🗑️ Clear list", callback_data="clear_list")],
        ]
    )


def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ Yes, delete everything", callback_data="confirm_clear")],
            [
                InlineKeyboardButton(
                    "📝 No, please keep ...",
                    switch_inline_query_current_chat="/clearexcept ",
                )
            ],
            [InlineKeyboardButton("❌ Abort", callback_data="cancel_clear")],
        ]
    )


def get_db(context: ContextTypes.DEFAULT_TYPE) -> Database:
    return context.bot_data["db"]


def format_list(items: list[tuple[int, str]]) -> str:
    if not items:
        return "The shopping list is empty! 🎉"
    lines = [f"{i}. {name}" for i, (_, name) in enumerate(items, 1)]
    return "Shopping list:\n" + "\n".join(lines)


async def show_list(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE, new_message: bool = False
) -> None:
    """Edit the stored menu message, or post a new one if there is none."""
    db = get_db(context)
    text = format_list(db.get_items(chat_id))
    menu_message_id = None if new_message else db.get_menu_message_id(chat_id)

    if menu_message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_message_id,
                text=text,
                reply_markup=main_keyboard(),
            )
            return
        except BadRequest as e:
            if "Message is not modified" in str(e):
                return
            logger.warning("Could not edit menu message, posting a new one: %s", e)

    message = await context.bot.send_message(
        chat_id=chat_id, text=text, reply_markup=main_keyboard()
    )
    db.set_menu_message_id(chat_id, message.message_id)


async def try_delete(message: Message) -> None:
    try:
        await message.delete()
    except BadRequest as e:
        logger.info("Could not delete user message, probably not an admin: %s", e)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Hi, I am Shoppy 🤖 I'll help you shop.")
    await show_list(update.effective_chat.id, context, new_message=True)


async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    args = get_command_args(msg.text or "", "add")
    if args is None:
        return

    items = split_items(args)
    if not items:
        await msg.reply_text(
            "Please let me know what should be added. E.g.: /add 2x milk, 1L juice, bread"
        )
        return

    get_db(context).add_items(msg.chat_id, items)
    await try_delete(msg)
    await show_list(msg.chat_id, context)


async def done_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    args = get_command_args(msg.text or "", "done")
    if args is None:
        return

    async def reply_error(text: str) -> None:
        # Both messages are removed after the next successful /done.
        context.chat_data.setdefault("last_command_message_ids", []).append(msg.message_id)
        error_message = await msg.reply_text(text)
        context.chat_data.setdefault("last_error_message_ids", []).append(error_message.message_id)

    if not args:
        await reply_error(
            "Please type in the numbers of items which should be removed. E.g.: /done 1, 2 5"
        )
        return

    numbers = parse_numbers(args)
    if not numbers:
        await reply_error("I could not find valid numbers in your message. Please try again.")
        return

    db = get_db(context)
    ids_to_delete, invalid = resolve_numbers(db.get_items(msg.chat_id), numbers)

    if invalid:
        await reply_error(
            f"The numbers {', '.join(map(str, invalid))} are invalid and will be ignored."
        )

    if not ids_to_delete:
        return

    stale_ids = context.chat_data.pop("last_error_message_ids", []) + context.chat_data.pop(
        "last_command_message_ids", []
    )
    for message_id in stale_ids:
        try:
            await context.bot.delete_message(chat_id=msg.chat_id, message_id=message_id)
        except BadRequest:
            pass  # already deleted

    db.delete_items(msg.chat_id, ids_to_delete)
    await try_delete(msg)
    await show_list(msg.chat_id, context)


async def clear_except(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    args = get_command_args(msg.text or "", "clearexcept")
    if args is None:
        return

    if not args:
        await msg.reply_text(
            "Please type the numbers of items which should be kept. E.g.: /clearexcept 1,3"
        )
        return

    numbers = parse_numbers(args)
    if not numbers:
        await msg.reply_text("I could not find valid numbers in your message. Please try again.")
        return

    db = get_db(context)
    db.delete_items(msg.chat_id, ids_except(db.get_items(msg.chat_id), numbers))
    await try_delete(msg)
    await show_list(msg.chat_id, context)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat.id

    if query.data == "clear_list":
        await query.edit_message_text(
            text="Are you sure you want to delete the full list?",
            reply_markup=confirmation_keyboard(),
        )
    elif query.data == "confirm_clear":
        get_db(context).clear(chat_id)
        await show_list(chat_id, context)
    elif query.data == "cancel_clear":
        await show_list(chat_id, context)


async def restrict_chats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Drop updates from chats not in the allowlist."""
    chat = update.effective_chat
    if chat and chat.id in context.bot_data["allowed_chat_ids"]:
        return
    if chat:
        logger.warning("Ignoring update from unauthorized chat %s (%s)", chat.id, chat.type)
    raise ApplicationHandlerStop


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Error while handling update %s", update, exc_info=context.error)


def build_application(token: str, db: Database, allowed_chat_ids: set[int]) -> Application:
    application = Application.builder().token(token).build()
    application.bot_data["db"] = db
    application.bot_data["allowed_chat_ids"] = allowed_chat_ids

    # Group -1 runs before all other handlers.
    application.add_handler(TypeHandler(Update, restrict_chats), group=-1)

    application.add_handler(CommandHandler("start", start))
    for command, callback in (
        ("add", add_item),
        ("done", done_item),
        ("clearexcept", clear_except),
    ):
        application.add_handler(MessageHandler(filters.Regex(command_pattern(command)), callback))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_error_handler(error_handler)
    return application
