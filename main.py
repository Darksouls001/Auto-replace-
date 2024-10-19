import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import logging

# Enable logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace this placeholder with your bot token
BOT_TOKEN = 'YOUR_BOT_TOKEN'

# State definitions for the conversation
ASK_TEXT_TO_REPLACE, ASK_REPLACEMENT_TEXT, ASK_MORE_REPLACEMENTS = range(3)

# Dictionary to store text replacements
text_replacements = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command to initiate the text replacement setup."""
    await update.message.reply_text("Welcome! Please enter the text you want to replace:")
    return ASK_TEXT_TO_REPLACE

async def ask_text_to_replace(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the text to be replaced and ask for the replacement text."""
    context.user_data['current_text_to_replace'] = update.message.text
    await update.message.reply_text(f"You want to replace: '{update.message.text}'. Now, enter the replacement text:")
    return ASK_REPLACEMENT_TEXT

async def ask_replacement_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store the replacement text and ask if the user wants to add more replacements."""
    text_to_replace = context.user_data.get('current_text_to_replace')
    replacement_text = update.message.text

    # Store the replacement pair in the dictionary
    text_replacements[text_to_replace] = replacement_text

    await update.message.reply_text(f"Replacement setup: '{text_to_replace}' will be replaced with '{replacement_text}'.\nDo you want to add another replacement? (yes/no)")
    return ASK_MORE_REPLACEMENTS

async def ask_more_replacements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's response to adding more replacements."""
    if update.message.text.lower() == 'yes':
        await update.message.reply_text("Please enter the next text you want to replace:")
        return ASK_TEXT_TO_REPLACE
    else:
        await update.message.reply_text("Replacement setup is complete! Your bot is now ready to replace text.")
        return ConversationHandler.END

async def replace_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Function to replace specified text in the channel post and captions."""
    global text_replacements
    message_text = None

    # Check if the channel post has text or caption
    if update.channel_post:
        if update.channel_post.text:  # If it's a text message
            message_text = update.channel_post.text
        elif update.channel_post.caption:  # If it's a media caption
            message_text = update.channel_post.caption

        # If message_text is found, perform the replacements
        if message_text:
            new_message_text = message_text
            for text_to_replace, replacement_text in text_replacements.items():
                new_message_text = new_message_text.replace(text_to_replace, replacement_text)

            try:
                # Edit the message or caption with the new text
                if update.channel_post.caption:  # Edit caption if it's a media message
                    await context.bot.edit_message_caption(chat_id=update.channel_post.chat_id,
                                                           message_id=update.channel_post.message_id,
                                                           caption=new_message_text)
                else:  # Edit text if it's a regular text message
                    await context.bot.edit_message_text(chat_id=update.channel_post.chat_id,
                                                        message_id=update.channel_post.message_id,
                                                        text=new_message_text)
            except Exception as e:
                logger.error(f"Error editing message: {e}")

            # Introduce a delay to respect rate limits
            await asyncio.sleep(2)  # Adjust this delay if necessary

    else:
        logger.info("The message does not contain text or a caption, skipping replacement.")

def main():
    """Start the bot and set up the conversation handler."""
    # Create the Application and pass in your bot's token
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Set up the conversation handler for text replacement setup
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_TEXT_TO_REPLACE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_text_to_replace)],
            ASK_REPLACEMENT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_replacement_text)],
            ASK_MORE_REPLACEMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_more_replacements)],
        },
        fallbacks=[],
    )

    # Add the conversation handler and the channel message handler to the application
    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, replace_text))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
  
