# main.py
"""
Main script to run a telegram bot which acts as a shopping list which can be used by one or more people."
"""
# ### IMPORTS ###

# Standard Libraries
import os
import logging
import re

# Third-party libraries
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler,  MessageHandler, filters

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

# ### KEYBOARD SETUP ###
def get_main_keyboard():
    """Creates an inline keyboard with buttons to control the bot."""
    keyboard = [
        [InlineKeyboardButton("➕ Artikel hinzufügen", switch_inline_query_current_chat='/add ')],
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data='show_list')],
        [InlineKeyboardButton("🗑️ Liste leeren", callback_data='clear_list')],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard():
    """Creates an inline keyboard with 'Yes' and 'No' for a confirmation prompt"""
    keyboard = [
        [InlineKeyboardButton("✅ Ja, Liste löschen", callback_data='confirm_clear')],
        [InlineKeyboardButton("❌ Nein, Liste behalten", callback_data='cancel_clear')],
    ]
    return InlineKeyboardMarkup(keyboard)

# ### BOT FUNCTIONS (HANDLERS) ###

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the main keyboard."""
    await update.message.reply_text(
        "Hallo! Hier kannst du deine Einkaufsliste verwalten:",
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles all button clicks and routes them to the correct action."""
    query = update.callback_query
    await query.answer()

    # Show ist
    if query.data == 'show_list':
        await show_list(update, context)
    
    # Clear list
    elif query.data == 'clear_list':
        # Ask for confirmation
        await query.edit_message_text(
            text="Bist du sicher, dass du die gesamte Liste löschen möchtest?",
            reply_markup=get_confirmation_keyboard()
        )
    # Confirmation for Clear list    
    elif query.data == 'confirm_clear':
        # User confirmed, execute the deletion
        await clear_list_action(update, context)
        
    # Abortion for Clear list    
    elif query.data == 'cancel_clear':
        # User cancelled, go back to the main list view
        await show_list(update, context)

    # Add item
    elif query.data == 'add_item':
        await add_item(update, context)

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds one or more comma-separated items to the shopping list using a list of dictionaries."""
    
    # Determine the source of the message
    if update.message:
        msg = update.message
    elif update.edited_message:
        msg = update.edited_message
    else:
        logging.warning("add_item: Update contains neither message nor edited_message: %s", update)
        return

    chat_id = msg.chat_id
    message_text = msg.text or ""
    logging.info("add_item called — chat_id=%s text=%s", chat_id, repr(message_text))

    # Find /add in the message, allowing for variations and whitespace
    m = re.search(r"/add(?:@\w+)?\s*(.*)", message_text, flags=re.IGNORECASE | re.DOTALL)
    if m:
        full_input_string = m.group(1).strip()
    else:
        # Fallback: manually search for /add in case of unexpected formatting
        if "/add" in message_text:
            idx = message_text.find("/add")
            full_input_string = message_text[idx + len("/add"):].strip()
        else:
            await msg.reply_text("Please specify what to add. Example: /add 2x milk, 1L juice, bread")
            return

    if not full_input_string:
        await msg.reply_text("Please specify what to add. Example: /add 2x milk, 1L juice, bread")
        return

    # Split into individual items by commas
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

    # Insert items into the database
    added_items_list_for_user = []
    for item in parsed_items:
        success = db.add_item(
            chat_id=chat_id,
            item_quantity=item['item_quantity'],
            item_name=item['item_name']
        )
        if not success:
            logging.error("DB insert failed for chat_id=%s item=%s", chat_id, item)
        else:
            logging.info("DB inserted chat_id=%s item=%s", chat_id, item)

        full_item_display = f"{item['item_quantity']} {item['item_name']}".strip() if item['item_quantity'] else item['item_name']
        added_items_list_for_user.append(full_item_display)

    # Refresh the list instead of sending a separate confirmation
    await show_list(update, context)


async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the shopping list. Can be triggered by a command or a button."""
    # Determine the chat_id from either a command or a button press
    if update.callback_query:
        chat_id = update.callback_query.message.chat_id
    else:
        chat_id = update.message.chat_id
    
    items = db.get_items(chat_id)

    if not items:
        message_text = "Die Einkaufsliste ist leer! 🎉"
    else:
        message_text = "Das müssen wir einkaufen:\n"
        # Each 'item' is now a tuple (item_id, item_quantity, item_name)
        for i, (item_id, item_quantity, item_name) in enumerate(items, 1):
            full_item = f"{item_quantity} {item_name}".strip() if item_quantity else item_name
            message_text += f"{i}. {full_item}\n"
    
    # Send the message. If it was a button click, edit the original message.
    try:
        if update.callback_query:
            await update.callback_query.edit_message_text(text=message_text, reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(message_text, reply_markup=get_main_keyboard())
    except BadRequest as e:
        # Ignore the error if the message is not modified
        if "Message is not modified" in str(e):
            pass
        else:
            # Log other potential errors
            logging.error(f"An error occurred while updating the message: {e}")


async def done_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if not context.args:
        await update.message.reply_text("Bitte gib die Nummer des Artikels an, der entfernt werden soll. Z.B.: /done 2")
        return

    try:
        item_number_to_delete = int(context.args[0])
        items = db.get_items(chat_id)

        if 0 < item_number_to_delete <= len(items):
            # Find the item to delete by its number
            item_to_delete = items[item_number_to_delete - 1]
            item_id = item_to_delete[0] # We need the item_id for deletion

            success = db.delete_item(item_id)
            
            if success:
                await update.message.reply_text("Super! Artikel wurde von der Liste entfernt.")
            else:
                await update.message.reply_text("Ein Fehler ist aufgetreten.")
        else:
            await update.message.reply_text("Ungültige Nummer. Schau mit /list nach der richtigen Nummer.")

    except ValueError:
        await update.message.reply_text("Das ist keine gültige Nummer.")

async def clear_list_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear list of items after confirmation."""
    chat_id = update.callback_query.message.chat_id
    success = db.clear_list(chat_id)

    if success:
        message_text = "✅ Die gesamte Einkaufsliste wurde gelöscht."
    else:
        # If list was already empty
        message_text = "Die Liste war bereits leer."

    # Edit the current message with the result and show the main keyboard again
    await update.callback_query.edit_message_text(
        text=message_text,
        reply_markup=get_main_keyboard()
    )

def main():
    """Starts the bot."""
    # Security check for the token
    if not TOKEN:
        logging.error("Error: API_KEY not found in .env file or is empty.")
        return

    # Initialize the database
    db.setup_database()

    application = Application.builder().token(TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("list", show_list)) 
    application.add_handler(CommandHandler("done", done_item))
    application.add_handler(CallbackQueryHandler(button_handler)) 
    application.add_handler(MessageHandler(
    filters.TEXT & filters.Regex(r"(^| )/add(@\w+)?\b"),
    add_item
    ))

    # Start the bot
    logging.info("Starting bot...")
    application.run_polling()


if __name__ == '__main__':
    main()
