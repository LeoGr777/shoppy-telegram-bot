# main.py
"""
Main script to run a telegram bot which acts as a shopping list which can be used by one or more people."
"""
# ### IMPORTS ###

# Standard Libraries
import os
import logging

# Third-party libraries
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

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
    """Creates an inline keyboard with the 'Show List' button."""
    keyboard = [
        [InlineKeyboardButton("📋 Liste anzeigen", callback_data='show_list')],
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
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    if query.data == 'show_list':
        # Call the existing show_list function
        await show_list(update, context)

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Adds one or more comma-separated items to the shopping list using a list of dictionaries."""
    chat_id = update.message.chat_id
    
    if not context.args:
        await update.message.reply_text("Bitte gib an, was ich hinzufügen soll. Z.B.: /add 2x Milch, 1L Saft, Brot")
        return

    # Join all arguments into one single string
    full_input_string = ' '.join(context.args)

    # Split the string by commas to get individual items
    item_strings = [item.strip() for item in full_input_string.split(',')]

    parsed_items = [] 

    # Parse all items into a list of dictionaries
    for item_string in item_strings:
        if not item_string:
            continue

        # Create list of item_quantities and items
        parts = item_string.split() 
        item_dict = {'item_quantity': None, 'item_name': ''}

        if len(parts) > 1:
            # Simple heuristic: Assume the first word is the quantity
            item_dict['item_quantity'] = parts[0]
            item_dict['item_name'] = ' '.join(parts[1:])
        else:
            # Only one word was given
            item_dict['item_name'] = item_string
        
        parsed_items.append(item_dict)

    # Now, process the list of dictionaries
    added_items_list_for_user = []
    for item in parsed_items:
        # Add the item to the database
        db.add_item(
            chat_id=chat_id,
            item_quantity=item['item_quantity'],
            item_name=item['item_name']
        )
        
        # Prepare the string for the confirmation message
        full_item_display = f"{item['item_quantity']} {item['item_name']}".strip() if item['item_quantity'] else item['item_name']
        added_items_list_for_user.append(full_item_display)

    # Send a summary confirmation to the user
    if added_items_list_for_user:
        confirmation_message = "Folgendes wurde zur Liste hinzugefügt:\n- " + "\n- ".join(added_items_list_for_user)
        await update.message.reply_text(confirmation_message)
    else:
        await update.message.reply_text("Ich konnte keine gültigen Artikel in deiner Nachricht finden.")


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
        # If the full list should be cleared
        if context.args[0] == "list":
            
            success = db.clear_list(chat_id)

            if success:
                await update.message.reply_text("Super! Alles eingekauft.")
            else:
                await update.message.reply_text("Ein Fehler ist aufgetreten.")

        # If a single item should be deleted
        else:
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

    # Start the bot
    logging.info("Starting bot...")
    application.run_polling()


if __name__ == '__main__':
    main()
