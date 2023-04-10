from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters,CallbackContext
# The messageHandler is used for all message updates
import configparser
import logging
import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()
import firebase_admin
from firebase_admin import db


cred_obj = firebase_admin.credentials.Certificate({
    "type": os.environ["FIREBASE_TYPE"],
    "project_id": os.environ["FIREBASE_PROJECT_ID"],
    "private_key_id": os.environ["FIREBASE_PRIVATE_KEY_ID"],
    "private_key": os.environ["FIREBASE_PRIVATE_KEY"].replace("\\n", "\n"),
    "client_email": os.environ["FIREBASE_CLIENT_EMAIL"],
    "client_id": os.environ["FIREBASE_CLIENT_ID"],
    "auth_uri": os.environ["FIREBASE_AUTH_URI"],
    "token_uri": os.environ["FIREBASE_TOKEN_URI"],
    "auth_provider_x509_cert_url": os.environ["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
    "client_x509_cert_url": os.environ["FIREBASE_CLIENT_X509_CERT_URL"]
})
firebase_admin.initialize_app(cred_obj, {
    'databaseURL': os.environ['FIREBASE_DATABASE_URL'],
    'storageBucket': os.environ['FIREBASE_STORAGE_BUCKET']
})
db_ref = db.reference('/')

def main():
    # Load your token and create an Updater for your Bot
    #config = configparser.ConfigParser()
    #config.read('config.ini')
   
    updater = Updater(token=(os.environ['TELEGRAM_ACCESS_TOKEN']), use_context=True)
    dispatcher = updater.dispatcher


    # You can set this logging module, so you will know when and why things do not work as expected
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    
    # register a dispatcher to handle message: here we register an echo dispatcher
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("movielist", movielist))
    dispatcher.add_handler(CommandHandler("add", addmovie))
    dispatcher.add_handler(CommandHandler("write", write))
    dispatcher.add_handler(CommandHandler("read", read))

    # To start the bot:
    updater.start_polling()
    updater.idle()
    
def echo(update, context):
    reply_message = 'Use /movielist, /read, /write. or /add'
    logging.info("Update: " + str(update))
    logging.info("context: " + str(context))
    context.bot.send_message(chat_id=update.effective_chat.id, text= reply_message)
    
def movielist(update: Update, context: CallbackContext) -> None:
	"""Send the list of movie when the command /movielist is issued."""
	data = db_ref.child('movies/').get()
	if data:   
		reply = "Here are our list of movies\nYou can choose one to read or write reviews by typing '/read moviename' or '/write moviename'\n"
		reply += showallmovies()
		update.message.reply_text(reply)
	else:
		update.message.reply_text("There is currently no movie. You can add movie by typing '/add moviename'")
  
def showallmovies():
	data = db_ref.child('movies/').get()
	movies = list(data.keys())
	result = ''
	for i in range(len(movies)):
		result += str(i+1)+". "+movies[i]+"\n"
	return result

def read(update: Update, context: CallbackContext) -> None:
	try:
		logging.info(context.args)
		num = int(context.args[0])  # /add keyword <-- this should store the keyword
		data = db_ref.child('movies/').get()
		if num > len(data):
			update.message.reply_text("Invalid index of movie.\nPlease enter a correct one.")
		else:
			key = list(data)[num-1]
			reviews = db_ref.child('movies/'+ key).get()
			if reviews:      
				for r in reviews.values():
					update.message.reply_text(str(r))
			else:
				update.message.reply_text("Sorry, there is currently no review for this movie.\nGo ahead and add one!")
	except (IndexError, ValueError):
		update.message.reply_text('Usage: /add <keyword>')

def write(update: Update, context: CallbackContext) -> None:
	try:
		logging.info(context.args)
		num = int(context.args[0])   # /write keyword <-- this should store the keyword
		data = db_ref.child('movies/').get()
		if num > len(data):
			update.message.reply_text("Invalid index of movie.\nPlease enter a correct one.")
		else:
			review = context.args[1:]
			realreview = ''
			for i in range(len(review)-1):
				realreview += review[i] + ' '
			realreview += review[len(review)-1]
			review = realreview
			
			key = list(data)[num-1]
			db_ref.child('movies/'+ key).push(review)
			
			update.message.reply_text('Thank you for your review!')
	except (IndexError, ValueError):
		update.message.reply_text('Usage: /add <keyword>')

def addmovie(update: Update, context: CallbackContext) -> None:
    try:
        logging.info(context.args)
        moviename = context.args  # /add keyword <-- this should store the keyword
        realname = ''
        for i in range(len(moviename)-1):
            realname += moviename[i] + ' '
        realname += moviename[len(moviename)-1]
        moviename = realname
        db_ref.child("movies/"+moviename).set('')
        reply = "Movie successfully added!\nHere is the latest list of movies\n"
        reply += showallmovies()
        update.message.reply_text(reply)
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /add <keyword>')

if __name__ == '__main__':
    main()