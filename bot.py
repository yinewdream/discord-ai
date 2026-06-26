import discord
from discord.ext import tasks, commands
from google import genai
import random
import os

# 1. 初始化設定
# 雖然不隱藏金鑰，但為了最新 SDK 的相容性，建議直接填入變數或設為環境變數
GEMINI_API_KEY = "你的_AQ._開頭金鑰"
DISCORD_TOKEN = "你的_Discord_Bot_Token"

# 初始化 Gemini 3.5 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

# 設定 Discord 機器人的權限 (一定要開啟 Message Content)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 2. 讓機器人「定時活躍」的機制 (例如每 30 分鐘主動講話)
@tasks.loop(minutes=30)
async def active_chatting():
    # 填入你想讓機器人主動說話的 Discord 頻道 ID
    channel = bot.get_channel(123456789012345678) 
    if channel:
        topics = ["跟大家分享一個有趣的科學冷知識", "講一個冷笑話", "問大家一個今天過得怎樣的問題"]
        prompt = random.choice(topics)
        
        # 叫 Gemini 產生主動開啟話題的內容
        response = client.interactions.create(
            model="gemini-3.5-flash",
            input=f"請用繁體中文（台灣習慣），字數在50字以內，主動在群組聊天。主題：{prompt}"
        )
        await channel.send(response.output_text)

@bot.event
async def on_ready():
    print(f"機器人已上線：{bot.user}")
    active_chatting.start() # 上線時啟動定時活躍任務

# 3. 監聽訊息：被標記(Mention)或隨機插嘴
@bot.event
async def on_message(message):
    # 排除機器人自己的訊息
    if message.author == bot.user:
        return

    # 狀況 A：有人標記(Tag)機器人，或者在私訊聊天
    is_mentioned = bot.user.mentioned_in(message)
    # 狀況 B：隨機插嘴（例如有 5% 的機率在大家聊天時插話）
    random_interact = random.random() < 0.20 

    if is_mentioned or random_interact:
        async with message.channel.typing(): # 顯示「機器人正在輸入中...」
            # 呼叫 Gemini 回應
            response = client.interactions.create(
                model="gemini-3.5-flash",
                input=f"對話上下文：{message.content}。請以朋友的語氣，用繁體中文簡短回應。"
            )
            await message.reply(response.output_text)

    await bot.process_commands(message)

# 啟動機器人
bot.run(DISCORD_TOKEN)
