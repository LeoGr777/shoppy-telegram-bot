# main.py
"""
Main script to run a telegram bot which acts as a shopping list which can be used by one or more people."
"""
# ### IMPORTS ###

# Standard Libraries
import os
import logging
import re
from typing import Optional

# Third-party libraries
from dotenv import load_dotenv
from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Local application modules
import database as db

# ### CONFIGURATION ###
# Set up logging 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
load_dotenv()
TOKEN = os.getenv("API_KEY") # The variable name in the .env file is API_KEY

# ### HELPER FUNCTIONS ###
def get_message_from_update(update: Update, action_name: str) -> Optional[Message]:
    """
    Helper function that extracts the message object from an update,
    handling both new and edited messages. Returns None if no message is found.
    """
    if update.message:
        return update.message
    if update.edited_message:
        return update.edited_message
    
    logging.warning(f"{action_name}: Update contains no message: %s", update)
    return None

def get_command_args(message_text: str, command: str) -> Optional[str]:
    """
    Extracts arguments from a message text following a specific command,
    handling commands with and without a bot name mention.
    """
    pattern = rf"/{command}(?:@\w+)?\s*(.*)"
    match = re.search(pattern, message_text, flags=re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

# ### KEYBOARD SETUP ###
def get_main_keyboard():
    """Creates an inline keyboard with buttons to control the bot."""
    keyboard = [
        [InlineKeyboardButton("➕ Add item", switch_inline_query_current_chat='/add ')],
        # [InlineKeyboardButton("📋 Liste anzeigen", callback_data='show_list')],
        [InlineKeyboardButton("⛔ Remove item", switch_inline_query_current_chat='/done ')],
        [InlineKeyboardButton("🗑️ Clear list", callback_data='clear_list')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard():
    """Creates an inline keyboard with 'Yes' and 'No' for a confirmation prompt"""
    keyboard = [
        [InlineKeyboardButton("✅ Yes, delete everything", callback_data='confirm_clear')],
        [InlineKeyboardButton("📝 No, please keep ...", switch_inline_query_current_chat='/clearexcept ')],
        [InlineKeyboardButton("❌ Abort", callback_data='cancel_clear')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ### BOT FUNCTIONS (HANDLERS) ###

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message, then shows the list in a separate, editable message."""
    # Send a simple, non-editable welcome message.
    await update.message.reply_text(
        "Hi, I am Shoppy 🤖 I'll help you shop."
    )
    
    # Force show_list to create a new menu message by clearing any old message ID.
    context.chat_data.pop('menu_message_id', None)
    await show_list(update, context)

async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the shopping list by editing the main menu message."""
    chat_id = update.effective_chat.id
    items = db.get_items(chat_id)

    if not items:
        message_text = "The shopping list is empty! 🎉"
    else:
        message_text = "Shopping list:\n"
        for i, (item_id, item_quantity, item_name) in enumerate(items, 1):
            full_item = f"{item_quantity} {item_name}".strip() if item_quantity else item_name
            message_text += f"{i}. {full_item}\n"
    
    menu_message_id = context.chat_data.get('menu_message_id')
    
    try:
        if menu_message_id:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=menu_message_id,
                text=message_text,
                reply_markup=get_main_keyboard()
            )
        else: 
            message = await context.bot.send_message(chat_id=chat_id, text=message_text, reply_markup=get_main_keyboard())
            context.chat_data['menu_message_id'] = message.message_id
            
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            logging.error(f"An error occurred while updating the message: {e}")

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds one or more comma-separated items to the shopping list."""
    msg = get_message_from_update(update, "add_item")
    if not msg:
        return

    chat_id = msg.chat_id
    message_text = msg.text or ""
    
    full_input_string = get_command_args(message_text, "add")

    if full_input_string is None:
        logging.warning("Could not parse /add command from message: %s", message_text)
        return

    if not full_input_string:
        await msg.reply_text("Please let me know what should be added. E.g.: /add 2x milk, 1L juice, bread")
        return

    item_strings = [item.strip() for item in full_input_string.split(',')]
    parsed_items = []

    for item_string in item_strings:
        if not item_string:
            continue
        tokens = item_string.split()
        item_dict = {'item_quantity': None, 'item_name': ''}
        if len(tokens) > 1:
            item_dict['item_quantity'] = tokens[0]
            item_dict['item_name'] = ' '.join(tokens[1:])
        else:
            item_dict['item_name'] = item_string
        parsed_items.append(item_dict)

    for item in parsed_items:
        db.add_item(
            chat_id=chat_id,
            item_quantity=item['item_quantity'],
            item_name=item['item_name']
        )
    
    try:
        await msg.delete()
    except BadRequest as e:
        if "Message can't be deleted" in str(e):
            logging.info("Could not delete user message, probably not an admin.")
        else:
            raise  # Re-raise other unexpected errors
            
    await show_list(update, context)

async def done_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes one or more items from the list by their numbers and cleans up messages."""
    msg = get_message_from_update(update, "done_item")
    if not msg:
        return
        
    chat_id = msg.chat_id
    message_text = msg.text or ""

    args_string = get_command_args(message_text, "done")
    
    if args_string is None:
        logging.warning("Could not parse /done command from message: %s", message_text)
        return

    async def handle_error(text):
        """Helper to send an error and store message IDs of both error and command."""
        context.chat_data.setdefault('last_command_message_ids', []).append(msg.message_id)
        error_message = await msg.reply_text(text)
        context.chat_data.setdefault('last_error_message_ids', []).append(error_message.message_id)

    if not args_string:
        await handle_error("Please type in the numbers of items which should be removed. E.g.: /done 1, 2 5")
        return

    number_strings = re.findall(r'\d+', args_string)

    if not number_strings:
        await handle_error("I could not find valid numbers in your message. Please try again.")
        return

    numbers_to_delete = {int(n) for n in number_strings}
    items = db.get_items(chat_id)
    max_item_number = len(items)
    
    ids_to_delete = []
    invalid_numbers = []

    for num in numbers_to_delete:
        if 0 < num <= max_item_number:
            item_id = items[num - 1][0]
            ids_to_delete.append(item_id)
        else:
            invalid_numbers.append(str(num))

    if invalid_numbers:
        await handle_error(f"The numbers {', '.join(invalid_numbers)} are invalid and will be ignored.")

    if ids_to_delete:
        # Clean up all previous temporary messages (errors and commands)
        messages_to_delete = context.chat_data.pop('last_error_message_ids', []) + \
                             context.chat_data.pop('last_command_message_ids', [])
        
        for msg_id in messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except BadRequest:
                pass # Ignore if already deleted

        for item_id in ids_to_delete:
            db.delete_item(item_id)
        
        try:
            await msg.delete()
        except BadRequest:
            logging.info("Could not delete user message, probably not an admin.")

        await show_list(update, context)

async def clear_except(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes all items from the list except for the ones specified by their numbers."""
    msg = get_message_from_update(update, "clear_except")
    if not msg:
        return
        
    chat_id = msg.chat_id
    message_text = msg.text or ""

    args_string = get_command_args(message_text, "clearexcept")

    if not args_string:
        await msg.reply_text("Please type the numbers of items which should be kept. E.g.: /clearexcept 1,3")
        return

    numbers_to_keep_str = re.findall(r'\d+', args_string)
    if not numbers_to_keep_str:
        await msg.reply_text("I could not find valid numbers in your message. Please try again..")
        return

    numbers_to_keep = {int(n) for n in numbers_to_keep_str}
    items = db.get_items(chat_id)
    
    ids_to_delete = []
    for i, (item_id, _, _) in enumerate(items, 1):
        if i not in numbers_to_keep:
            ids_to_delete.append(item_id)

    for item_id in ids_to_delete:
        db.delete_item(item_id)

    try:
        await msg.delete()
    except BadRequest:
        logging.info("Could not delete user command message.")

    await show_list(update, context)

async def clear_list_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear list of items after confirmation."""
    chat_id = update.callback_query.message.chat_id
    db.clear_list(chat_id)
    await show_list(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all button clicks and routes them to the correct action."""
    query = update.callback_query
    await query.answer()

    # if query.data == 'show_list':
    #     await show_list(update, context)
    
    if query.data == 'clear_list':
        await query.edit_message_text(
            text="Are you sure you want to delete the full list?",
            reply_markup=get_confirmation_keyboard()
        )
        
    elif query.data == 'confirm_clear':
        await clear_list_action(update, context)
        
    elif query.data == 'cancel_clear':
        await show_list(update, context)

def main():
    """Starts the bot."""
    if not TOKEN:
        logging.error("Error: API_KEY not found in .env file or is empty.")
        return

    db.setup_database()
    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(MessageHandler(filters.Regex(r'/add'), add_item))
    application.add_handler(MessageHandler(filters.Regex(r'/done'), done_item))
    application.add_handler(MessageHandler(filters.Regex(r'/clearexcept'), clear_except))
    application.add_handler(CommandHandler("list", show_list)) 
    application.add_handler(CallbackQueryHandler(button_handler)) 

    logging.info("Starting bot...")
    application.run_polling()


if __name__ == '__main__':
    main()
