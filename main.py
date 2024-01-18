from telegram import (Update, 
                    ReplyKeyboardMarkup,
                    ReplyKeyboardRemove)

from telegram.ext import (ApplicationBuilder,
                        CommandHandler, 
                        MessageHandler, 
                        ContextTypes, 
                        filters, 
                        ConversationHandler,
                        )

from database import DatabaseHandler
import re
from unidecode import unidecode
from llama import request_llama, parse_request


TOKEN = ""
CHOOSING, FIRST, SECOND, LAST = range(4)

# If the user response could be conerted to the float...
# also chack for persian numbers.
def is_number(response):
    try:
        response = unidecode(response)
        number = float(response)
        return True
    except ValueError:
        return False

#  check the range of size. 
# the second number should be greater than the first one. 
# and the should be separated by space
def is_valid_response(response):
    if re.match(r'^\d+\s\d+$', response):
        first_number, second_number = map(int, response.split())
        return second_number > first_number
    return False
    
    
# Command
# user should enter "شروع جستجو" 
# and questions are started.
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ما اینجا در پیدا کردن اقامتگاه به شما کمک می کنیم.", 
                                    reply_markup=ReplyKeyboardMarkup( [["شروع جستجو"]], one_time_keyboard=True)
                                    )
    return CHOOSING
    
    
# Questions
async def first_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("اقامتگاه شما باید چند نفر ظرفیت داشته باشد؟",
                                    reply_markup=ReplyKeyboardRemove(),
                                    )
    return FIRST

    
async def second_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # if the user response is valid, continue. 
    # else, repeat your question until the user responds properly. 
    if is_number(update.message.text):
        context.user_data['capacity'] = int(update.message.text)
        await update.message.reply_text("امتیاز اقامتگاه از چند به بالا باشد مناسب است؟")
        return SECOND
    
    else:
        await update.message.reply_text("پاسخ شما باید به صورت عدد باشد. دوباره امتحان کنید.")
        return FIRST

    
async def third_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    if is_number(update.message.text):
        context.user_data['score'] = float(update.message.text) 
        await update.message.reply_text("خانه بین چند متر باید باشد؟")
        return LAST
    
    else:
        await update.message.reply_text("پاسخ شما باید به صورت عدد باشد. دوباره امتحان کنید.")
    return SECOND


async def last_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_valid_response(update.message.text):
        range_of_area = [int(i) for i in update.message.text.split()]
        context.user_data['area_size'] = range_of_area
        
        # print all parameter for debuging
        print(f""" Capacity: {context.user_data['capacity']}, 
        Score: {context.user_data['score']}, 
        Size Range: {context.user_data['area_size']}""")
    
        db_handler = DatabaseHandler('Mori', 'postgres', '', 'localhost')
        db_handler.connect()
        values = [context.user_data['capacity'], context.user_data['score'], context.user_data['area_size']]
        results = db_handler.query(tabel='tehran_data_jabama', values=values)
        print(results)
        db_handler.close()
        
        if results:
            await update.message.reply_text(f"""کد اقامتگاه های پیشنهادی شما به همراه متراژ و امتیاز و ظرفیت:
                                    {results}
                                    """)  
        else:
            await update.message.reply_text("""اقامتگاهی با این مشخصات پیدا نشد.""") 
    
        return ConversationHandler.END
    
    
    else:
        await update.message.reply_text("پاسخ شما باید به صورت دو عدد با فاصله باشد. دوباره امتحان کنید.")
    return LAST

# Cancel 
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('شما مکالمه را تمام کردید.')
    return ConversationHandler.END


async def start_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مواردی که می‌خواهی در پیدا کردن اقامتگاهت رعایت شود را به زبان انگلیسی بنویس.")
    
    
async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = update.message.text
    llama_response = request_llama(user_query)
    llama_response = parse_request(llama_response)
    # print(llamama_response)
    
    # find data in db
    db_handler = DatabaseHandler('Mori', 'postgres', 'hana2641378', 'localhost')
    db_handler.connect()
    results = db_handler.llama_query(tabel='tehran_data_jabama', parameters=llama_response)
    print(results)
    db_handler.close()
    
    if results:
        await update.message.reply_text(f"""کد اقامتگاه های پیشنهادی شما به همراه متراژ و امتیاز و ظرفیت :
                                    {results}
                                    """)  
    else:
        await update.message.reply_text("""اقامتگاهی با این مشخصات پیدا نشد.""") 
        

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")


if __name__=="__main__":
    
    print('Starting bot...')
    app = ApplicationBuilder().token(TOKEN).build()
    
    # STEP 1
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            CHOOSING: [MessageHandler(filters.Regex('^شروع جستجو$') & ~filters.COMMAND, first_question)],
            FIRST: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_question)],
            SECOND: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_question)],
            LAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, last_question)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    app.add_handler(conv_handler)    
    
    
    # STEP 3, LLAMA 
    app.add_handler(CommandHandler('start_prompt', start_prompt))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))
    
    
    # Errors
    app.add_error_handler(handle_error)
    
    print("Polling...")
    app.run_polling(poll_interval=3)
