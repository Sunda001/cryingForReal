import shutil, psutil
import signal
import os
import asyncio
import time
import pytz


from pyrogram import idle
from sys import executable

from telegram import ParseMode, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from telegraph import Telegraph
from wserver import start_server_async
from bot import bot, app, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, IS_VPS, PORT, alive, nox, web, OWNER_ID, AUTHORIZED_CHATS, telegraph_token, LOGGER
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper import button_build
from .modules import authorize, mirror_status, mirror, watch, shell, eval, leech_settings, cancel_mirror
from datetime import date, datetime

today = date.today()
kek = datetime.now(pytz.timezone(f'Asia/Kolkata'))
vro = kek.strftime('\n 𝗗𝗮𝘁𝗲 : %d/%m/%Y\n 𝗧𝗶𝗺𝗲: %I:%M%P')

def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    d1 = today.strftime("%d/%m/%Y")
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    disk = psutil.disk_usage('/').percent
    p_core = psutil.cpu_count(logical=False)
    t_core = psutil.cpu_count(logical=True)
    swap = psutil.swap_memory()
    swap_p = swap.percent
    swap_t = get_readable_file_size(swap.total)
    swap_u = get_readable_file_size(swap.used)
    memory = psutil.virtual_memory()
    mem_p = memory.percent
    mem_t = get_readable_file_size(memory.total)
    mem_a = get_readable_file_size(memory.available)
    mem_u = get_readable_file_size(memory.used)
    stats = f'<b>Bot Uptime:</b> {currentTime}\n\n'\
            f'<b>Date:</b> <code>{d1}</code>\n' \
            f'<b>Total Disk Space:</b> {total}\n'\
            f'<b>Used:</b> {used} | <b>Free:</b> {free}\n\n'\
            f'<b>Upload:</b> {sent}\n'\
            f'<b>Download:</b> {recv}\n\n'\
            f'<b>CPU:</b> {cpuUsage}%\n'\
            f'<b>RAM:</b> {mem_p}%\n'\
            f'<b>DISK:</b> {disk}%\n\n'\
            f'<b>Physical cores:</b> {p_core}\n'\
            f'<b>Total cores:</b> {t_core}\n\n'\
            f'<b>SWAP:</b> {swap_t} - {swap_u} <b>Used</b> {swap_p}%\n'\
            f'<b>Memory Total:</b> {mem_t}\n'\
            f'<b>Memory Free:</b> {mem_a}\n'\
            f'<b>Memory Used:</b> {mem_u}\n'
    sendMessage(stats, context.bot, update)


def restart(update, context):
    restart_message = sendMessage("Restarting...", context.bot, update)
    # Save restart message object in order to reply to it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    alive.kill()
    process = psutil.Process(web.pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()
    nox.kill()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)

help_string_telegraph = f'''<br>
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b> Leech through youtube-dl and zip before uploading 
<br><br>
<b>/{BotCommands.LeechSetCommand}</b> Leech Settings 
<br><br>
<b>/{BotCommands.SetThumbCommand}</b> Reply to photo to set it as thumbnail for next uploads 
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Cancel all running tasks [OWNER-ONLY]
<br><br>
<b>/{BotCommands.StatusCommand}</b>: Shows a status of all the downloads
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Show Stats of the machine the bot is hosted on
'''
help = Telegraph(access_token=telegraph_token).create_page(
        title='PubliLeech Help',
        html_content=help_string_telegraph,
    )["path"]

help_string = f'''
/{BotCommands.LeechCommand}: Leech Torrent/Direct link


/{BotCommands.ZipLeechCommand}: Leech Torrent/Direct link and upload as .zip


/{BotCommands.UnzipLeechCommand}: Leech Torrent/Direct link and extract


/{BotCommands.QbLeechCommand}: Leech  Torrent/Magnet using qBittorrent


/{BotCommands.QbZipLeechCommand}: Leech Torrent/Magnet and upload as .zip using qb


/{BotCommands.QbUnzipLeechCommand}: Leech Torrent/Direct link and extract


/{BotCommands.LeechWatchCommand}: Leech through Youtube-dl supported link and Upload to Telegram


/{BotCommands.CancelMirror}: Reply to the message by which the download was initiated and that download will be cancelled
'''

def bot_help(update, context):
    button = button_build.ButtonMaker()
    button.buildbutton("Click Here For Other Commands", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update, reply_markup)

'''
botcmds = [
        (f'{BotCommands.StatusCommand}','Get Mirror Status message'),
        (f'{BotCommands.StatsCommand}','Bot Usage Stats'),
        (f'{BotCommands.PingCommand}','Ping the Bot'),
        (f'{BotCommands.RestartCommand}','Restart the bot [owner/sudo only]'),
        (f'{BotCommands.LogCommand}','Get the Bot Log [owner/sudo only]'),
    ]
'''

def main():
    fs_utils.start_cleanup()
    if IS_VPS:
        asyncio.new_event_loop().run_until_complete(start_server_async(PORT))
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    elif OWNER_ID:
        try:
            text = "𝐁𝐎𝐓 𝐑𝐄𝐒𝐓𝐀𝐑𝐓𝐄𝐃 \n{vro}\n\n 𝗧𝗶𝗺𝗲 𝗭𝗼𝗻𝗲 : {Asia/Kolkata}\n\nρℓєαѕє ѕтαят уσυя ∂σωиℓσα∂ѕ αgαιи!\n\n#Restarted"
            bot.sendMessage(chat_id=OWNER_ID, text=text, parse_mode=ParseMode.HTML)
            if AUTHORIZED_CHATS:
                for i in AUTHORIZED_CHATS:
                    bot.sendMessage(chat_id=i, text=text, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.warning(e)
    # bot.set_my_commands(botcmds)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
