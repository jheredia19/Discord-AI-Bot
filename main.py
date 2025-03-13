# Imports
import json, discord, openai
from datetime import datetime

# Loading config variables
with open('Config.json') as config_file:
    config = json.load(config_file)
TOKEN = config['discord_token']
AI_API_KEY = config['openai_api_key']
TARGET_CHANNELS = config['target_channels']
RESPONSE_INTERVAL = config['response_interval']
MAIN_PROMPT = config['main_prompt']
MSG_HISTORY_CONTEXT = config['message_history_context']

# Setting up the discord bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Setting up chatgpt
openai_client = openai.OpenAI(api_key=AI_API_KEY)

# Cooldown tracking
channel_last_response_times = {}

async def generate_ai_response(prompt, username):
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"{MAIN_PROMPT} Feel free to use the user's username where needed, the username is: {username}"},
                {"role": "user", "content": prompt}
            ]
        )
        result = completion.choices[0].message.content.lower()
        return result
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "Sorry, I couldn’t think of anything to say."

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')

@client.event
async def on_message(message):

    # So it doesn't respond to its self
    if message.author.bot:
        return

    # so it doesn't respond to images
    if message.content == "":
        return

    if str(message.channel.id) in TARGET_CHANNELS:

        # Checking if time is up
        current_time = datetime.now()
        last_response_time = channel_last_response_times.get(message.channel.id)
        if last_response_time and (current_time - last_response_time).total_seconds() < RESPONSE_INTERVAL:
            return
        channel_last_response_times[message.channel.id] = current_time

        # Generating response with previous messages
        if MSG_HISTORY_CONTEXT:
            last_messages = [message async for message in message.channel.history(limit=MSG_HISTORY_CONTEXT)]
            message_list = [
                {"author": msg.author.name, "content": msg.content}
                for msg in last_messages if not msg.author.bot and msg.id != message.id
            ]
            reply_text = await generate_ai_response(f"{message.content}\n\nLast Messages:\n" + "\n".join(
                [f"{msg['author']}: {msg['content']}" for msg in message_list]), message.author.display_name)
        else:
            reply_text = await generate_ai_response(f"{message.content}", message.author.display_name)

        await message.reply(reply_text)

client.run(TOKEN)
