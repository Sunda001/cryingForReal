from pyrogram import filters
from pyrogram.types import Message


import os
import asyncio

from PIL import Image
from io import BytesIO

from aiohttp import ClientSession

aiohttpsession = ClientSession()

async def make_carbon(code):
    url = "https://carbonara.vercel.app/api/cook"
    async with aiosession.post(url, json={"code": code}) as resp:
        image = BytesIO(await resp.read())
    image.name = "carbon.png"
    return image


from bot import app, telegraph


async def make_carbon(code):
    url = "https://carbonara.vercel.app/api/cook"
    async with aiohttpsession.post(url, json={"code": code}) as resp:
        image = BytesIO(await resp.read())
    image.name = "carbon.png"
    return image





n = "\n"
w = " "


bold = lambda x: f"**{x}:** "
bold_ul = lambda x: f"**--{x}:**-- "

mono = lambda x: f"`{x}`{n}"


def section(
    title: str,
    body: dict,
    indent: int = 2,
    underline: bool = False,
) -> str:

    text = (bold_ul(title) + n) if underline else bold(title) + n

    for key, value in body.items():
        text += (
            indent * w
            + bold(key)
            + ((value[0] + n) if isinstance(value, list) else mono(value))
        )
    return text





@app.on_message(filters.command(['ss']))
async def take_ss(_, message: Message):
    try:
        if len(message.command) != 2:
            return await message.reply_text("Give A Url To Fetch Screenshot.")
        url = message.text.split(None, 1)[1]
        m = await message.reply_text("**Capturing Screenshot**")
        await m.edit("**Uploading**")
        try:
            await message.reply_photo(
                photo=f"https://webshot.amanoteam.com/print?q={url}",
                quote=False,
            )
        except TypeError:
            return await m.edit("No Such Website.")
        await m.delete()
    except Exception as e:
        await message.reply_text(str(e))



@app.on_message(filters.command(['carbon']))
async def carbon_func(_, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "Reply to a text message to make carbon."
        )
    if not message.reply_to_message.text:
        return await message.reply_text(
            "Reply to a text message to make carbon."
        )
    m = await message.reply_text("Preparing Carbon")
    carbon = await make_carbon(message.reply_to_message.text)
    await m.edit("Uploading")
    await app.send_document(message.chat.id, carbon)
    await m.delete()
    carbon.close()


async def get_user_info(user, already=False):
    if not already:
        user = await app.get_users(user)
    if not user.first_name:
        return ["Deleted account", None]
    user_id = user.id
    username = user.username
    first_name = user.first_name
    mention = user.mention("Link")
    dc_id = user.dc_id
    photo_id = user.photo.big_file_id if user.photo else None
    is_gbanned = await is_gbanned_user(user_id)
    is_sudo = user_id in SUDOERS
    karma = await user_global_karma(user_id)
    body = {
        "ID": user_id,
        "DC": dc_id,
        "Name": [first_name],
        "Username": [("@" + username) if username else "Null"],
        "Mention": [mention],
    }
    caption = section("User info", body)
    return [caption, photo_id]

@app.on_message(filters.command(['info']))
async def info_func(_, message: Message):
    if message.reply_to_message:
        user = message.reply_to_message.from_user.id
    elif not message.reply_to_message and len(message.command) == 1:
        user = message.from_user.id
    elif not message.reply_to_message and len(message.command) != 1:
        user = message.text.split(None, 1)[1]

    m = await message.reply_text("Processing")

    try:
        info_caption, photo_id = await get_user_info(user)
    except Exception as e:
        return await m.edit(str(e))

    if not photo_id:
        return await m.edit(info_caption, disable_web_page_preview=True)
    photo = await app.download_media(photo_id)

    await message.reply_photo(photo, caption=info_caption, quote=False)
    await m.delete()
    os.remove(photo)


@app.on_message(filters.command(['cinfo']))
async def cinfo_func(_, message: Message):
    try:
        if len(message.command) > 2:
            return await message.reply_text(
                "**Usage:**/cinfo [USERNAME|ID]"
            )

        if len(message.command) == 1:
            chat = message.chat.id
        elif len(message.command) == 2:
            chat = message.text.split(None, 1)[1]

        m = await message.reply_text("Processing")

        info_caption, photo_id = await get_chat_info(chat)
        if not photo_id:
            return await m.edit(info_caption, disable_web_page_preview=True)

        photo = await app.download_media(photo_id)
        await message.reply_photo(photo, caption=info_caption, quote=False)

        await m.delete()
        os.remove(photo)
    except Exception as e:
        await m.edit(e)


@app.on_message(filters.command(['telegraph']))
async def paste(_, message: Message):
    reply = message.reply_to_message

    if not reply or not reply.text:
        return await message.reply("Reply to a text message")

    if len(message.command) < 2:
        return await message.reply("**Usage:**\n /telegraph [Page name]")

    page_name = message.text.split(None, 1)[1]
    page = telegraph.create_page(
        page_name, html_content=(reply.text.html).replace("\n", "<br>")
    )
    return await message.reply(
        f"**Posted:** {page['url']}",
        disable_web_page_preview=True,
    )



@app.on_message(filters.command(['id']))
async def getid(client, message):
    chat = message.chat
    your_id = message.from_user.id
    message_id = message.message_id
    reply = message.reply_to_message

    text = f"**[Message ID:]({message.link})** `{message_id}`\n"
    text += f"**[Your ID:](tg://user?id={your_id})** `{your_id}`\n"

    if not message.command:
        message.command = message.text.split()

    if len(message.command) == 2:
        try:
            split = message.text.split(None, 1)[1].strip()
            user_id = (await client.get_users(split)).id
            text += f"**[User ID:](tg://user?id={user_id})** `{user_id}`\n"
        except Exception:
            return await eor(message, text="This user doesn't exist.")

    text += f"**[Chat ID:](https://t.me/{chat.username})** `{chat.id}`\n\n"
    if not getattr(reply, "empty", True):
        id_ = reply.from_user.id if reply.from_user else reply.sender_chat.id
        text += (
            f"**[Replied Message ID:]({reply.link})** `{reply.message_id}`\n"
        )
        text += f"**[Replied User ID:](tg://user?id={id_})** `{id_}`"

    await eor(
        message,
        text=text,
        disable_web_page_preview=True,
        parse_mode="md",
    )
