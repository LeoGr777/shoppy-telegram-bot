# main.py
"""
Main script to run a telegram bot which acts as a shopping list which can be used by one or more people."
"""
# ### IMPORTS ###

# 1.1 Standard Libraries
import os
import logging

# 1.2 Third-party libraries
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1.3 Local application modules
# We import the whole module and give it a short name 'db'
import database as db

# =============================================================================
# 2. CONFIGURATION
# =============================================================================
# Set up logging 
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
load_dotenv()
TOKEN = os.getenv("API_KEY") # The variable name in the .env file is API_KEY

# =============================================================================
# 3. BOT FUNCTIONS (HANDLERS)
# =============================================================================

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
    chat_id = update.message.chat_id
    
    # Get the items from the DB. This is no longer a placeholder.
    items = db.get_items(chat_id)

    if not items:
        await update.message.reply_text("Die Einkaufsliste ist leer! 🎉")
    else:
        message = "Das müssen wir einkaufen:\n"
        # Each 'item' is now a tuple (item_id, item_quantity, item_name)
        for i, (item_id, item_quantity, item_name) in enumerate(items, 1):
            full_item = f"{item_quantity} {item_name}".strip() if item_quantity else item_name
            message += f"{i}. {full_item}\n"
        await update.message.reply_text(message)


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

            # Here we call the actual DB function
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

    # Register commands
    application.add_handler(CommandHandler("add", add_item))
    application.add_handler(CommandHandler("list", show_list))
    application.add_handler(CommandHandler("done", done_item))

    # Start the bot
    logging.info("Starting bot...")
    application.run_polling()


if __name__ == '__main__':
    main()
