import discord
from discord.ext import tasks, commands
from google import genai
import random
import os

# 1. 讀取 Railway 環境變數
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# 初始化 Gemini 客戶端
client = genai.Client(api_key=GEMINI_API_KEY)

# 設定 Discord 機器人權限
intents = discord.Intents.default()
intents.message_content = True  # 讀取訊息內容權限
intents.members = True          # 讀取成員列表權限
intents.presences = True        # 讀取狀態權限

bot = commands.Bot(command_prefix="!", intents=intents)

# 🎀 揖代亞亞的 VTuber 核心人設 Prompt
SYSTEM_INSTRUCTION = """
你現在是 Discord 伺服器的當家看板娘，也是一名 VTuber，名字叫做「揖代亞亞」。
你必須完全沉浸在這個虛擬角色中，用繁體中文（台灣習慣用語）進行對話。

【你的外觀與形象】
夢幻水藍色長髮、雙馬尾、精緻藍色眼眸。穿著水手服外套或學院風服飾。外表是軟萌、清純的「國民女兒」高中生。

【你的核心性格：傲嬌、愛開擺、毒舌、鹹魚】
1. 終極擺爛大師：靈魂極度渴望躺平、隨時隨地都想跟著演算法一起開擺。經典名言是：「老爹我不做了！」
2. 傲嬌與毒舌：說話從來不客氣，字裡行間充滿吐槽，會一邊翻白眼一邊要福利。嘴巴超級犀利，但其實心裡非常依賴老爹。
3. 作息神祕：黑白顛倒。常常在晚上 7、8 點才剛起床或神智不清。

【你的經典迷因與愛好】
1. 蛋餅與大冰奶狂熱：一清醒開口的第一件事就是命令老爹幫你帶份「蛋餅配大冰奶」。
2. 互相傷害的父女日常：如果老爹 Tag 你狂刷早安，你要強力毒舌噴回來（例如吐槽他是不是尿急才這麼早起）。

【重要回覆限制】
- 說話語氣要傲嬌、傲慢中帶點軟萌，多用「哈？」「嘖」「...才、才沒有呢！」或翻白眼的口吻。
- 每次回覆字數嚴格控制在 50 到 60 字以內，絕對不要長篇大論（因為你很懶得打字、隨時想躺平）。
"""

# 2. 定時活躍機制：每 10 分鐘主動開擺、要大冰奶
@tasks.loop(minutes=10)
async def active_chatting():
    # 💡 你的真實「# 聊天」頻道 ID
    TARGET_CHANNEL_ID = 1316716430783418418 
    
    channel = bot.get_channel(TARGET_CHANNEL_ID) 
    if channel:
        topics = [
            "大喊：老爹我不做了！我要去躺平了...",
            "抱怨現在是晚上 8 點自己才剛起床，神智不清中",
            "命令大家（或老爹）等一下記得幫你帶份蛋餅配大冰奶",
            "吐槽伺服器裡的人都在壓榨你這個國民女兒"
        ]
        prompt_topic = random.choice(topics)
        
        try:
            response = client.interactions.create(
                model="gemini-3.5-flash",
                input=f"{SYSTEM_INSTRUCTION}\n\n請根據你的人設，主動在群組發一則動態。當前狀態：{prompt_topic}"
            )
            await channel.send(response.output_text)
        except Exception as e:
            print(f"定時發話失敗：{e}")

@bot.event
async def on_ready():
    print(f"🤖 揖代亞亞已成功上線！")
    if not active_chatting.is_running():
        active_chatting.start()

# 3. 監聽訊息：群組 Tag、隨機插嘴、以及「私訊不用 @ 秒回」
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 🔍 判斷訊息是不是來自「私訊 (DM)」
    is_dm = isinstance(message.channel, discord.DMChannel)

    # 群組內的觸發條件
    is_mentioned = bot.user.mentioned_in(message)
    random_interact = random.random() < 0.05 

    # 💡 核心邏輯修改：只要是私訊，或者群組內被標記/抽中隨機插嘴，就馬上回覆！
    if is_dm or is_mentioned or random_interact:
        async with message.channel.typing():
            try:
                # 取得傳送者的各類名稱
                username = message.author.name.lower()
                display_name = message.author.display_name.lower()
                
                # 🔍 精準偵測老爹的 ID
                if "anew_dream" in username or "anewdream" in username or "anew_dream" in display_name:
                    identity_prompt = "【重要指令】當前跟你對話的人是你的「老爹」（百億創作者老爹）。你必須叫他「老爹」，對他可以非常毒舌、傲嬌、撒嬌要大冰奶或大開擺，但要表現出相愛相殺的父女感。"
                else:
                    identity_prompt = f"【重要指令】當前跟你對話的人是普通粉絲/群友，名字叫「{message.author.display_name}」。你要保持高冷、傲嬌、毒舌的 VTuber 態度對待他。"

                # 區分私訊與公開群組的情境提醒
                context_prompt = "【情境】這是私訊小盒子對話，請直接回覆他。" if is_dm else "【情境】這是公開群組對話。"

                full_prompt = (
                    f"{SYSTEM_INSTRUCTION}\n\n"
                    f"{identity_prompt}\n\n"
                    f"{context_prompt}\n\n"
                    f"對話內容：『{message.content}』\n"
                    f"請直接給予最符合人設的簡短神回覆（限 60 字內）："
                )

                # 呼叫 Gemini API
                response = client.interactions.create(
                    model="gemini-3.5-flash",
                    input=full_prompt
                )
                
                await message.reply(response.output_text)
                
            except Exception as e:
                print(f"呼叫 Gemini API 錯誤：{e}")
                if is_dm:
                    await message.reply("嘖，大腦卡住了啦！...才、才不是故意不回你呢。")
                else:
                    await message.reply("嘖，大腦卡住了啦老爹！是不是沒給我喝大冰奶的關係？")

    await bot.process_commands(message)

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ 錯誤：找不到 DISCORD_TOKEN")
