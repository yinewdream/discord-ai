import discord
from discord.ext import tasks, commands
from google import genai
import random
import os

# 1. 讀取 Railway 環境變數（會自動讀取你填寫的 AQ. 金鑰與 Discord Token）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# 初始化 Gemini 3.5 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

# 設定 Discord 機器人的權限（必須與你在 Developer Portal 開啟的特權意圖一致）
intents = discord.Intents.default()
intents.message_content = True  # 讀取訊息內容權限
intents.members = True          # 讀取成員列表權限
intents.presences = True        # 讀取狀態權限

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. 定時活躍機制：每 30 分鐘主動在指定頻道開啟話題
@tasks.loop(minutes=30)
async def active_chatting():
    # 💡 記得把這裡的 123456789012345678 改成你想讓 AI 主動說話的「Discord 頻道 ID」
    # 在 Discord 頻道上按右鍵複製 ID 即可
    TARGET_CHANNEL_ID = 1316716430783418418
    
    channel = bot.get_channel(TARGET_CHANNEL_ID) 
    if channel:
        topics = [
            "跟大家分享一個有趣的科學冷知識", 
            "講一個跟程式或科技有關的冷笑話", 
            "問大家一個今天過得怎樣的問題",
            "分享一個關於 Minecraft 或遊戲的趣味話題"
        ]
        prompt = random.choice(topics)
        
        try:
            # 呼叫 Gemini 3.5 產生主動對話內容
            response = client.interactions.create(
                model="gemini-3.5-flash",
                input=f"請用繁體中文（台灣習慣語氣），字數在 50 字以內，主動在群組裡開頭聊天。主題：{prompt}"
            )
            await channel.send(response.output_text)
        except Exception as e:
            print(f"定時發話失敗：{e}")

@bot.event
async def on_ready():
    print(f"🤖 機器人已成功上線：{bot.user}")
    # 上線時自動啟動定時活躍任務
    if not active_chatting.is_running():
        active_chatting.start()

# 3. 監聽訊息：被 Tag 標記，或者隨機插嘴聊天
@bot.event
async def on_message(message):
    # 排除機器人自己的訊息，避免無限循環
    if message.author == bot.user:
        return

    # 狀況 A：有人在群組標記(Tag)機器人，或者是私訊
    is_mentioned = bot.user.mentioned_in(message)
    
    # 狀況 B：隨機插嘴（設定 5% 的機率在大家聊天時自動接話）
    random_interact = random.random() < 0.05 

    if is_mentioned or random_interact:
        async with message.channel.typing():  # 讓機器人顯示「正在輸入中...」
            try:
                # 呼叫 Gemini 3.5 進行對話回應
                response = client.interactions.create(
                    model="gemini-3.5-flash",
                    input=f"對話上下文：{message.content}。請以好朋友的幽默語氣，使用繁體中文（台灣習慣）簡短回應，字數控制在 60 字以內。"
                )
                await message.reply(response.output_text)
            except Exception as e:
                print(f"呼叫 Gemini API 錯誤：{e}")
                await message.reply("哎呀，我的大腦剛剛閃退了一下，等我重整一下！")

    # 確保其他指令功能仍可正常運作
    await bot.process_commands(message)

# 啟動機器人
if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ 錯誤：找不到 DISCORD_TOKEN 環境變數，請確認 Railway 設定！")
