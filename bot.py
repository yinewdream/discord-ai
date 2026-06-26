import discord
from discord.ext import tasks, commands
from google import genai
import random
import os

# 1. 讀取 Railway 的環境變數（把漏掉的 DISCORD_TOKEN 補回來了！）
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

# 填滿 7 隻大腦的超級游泳池 🏊‍♂️
API_KEYS_POOL = [
    GEMINI_API_KEY,  # 第一隻（預設讀取 Railway 變數）
    "AQ.Ab8RN6K3lmSREmRJIkA-83uUrMGSpkDcL_TFIcqHF9FdmwmCEQ",
    "AQ.Ab8RN6Ix_glXsXhAOZeA_1F8U66CoUoTM71y5G8cmFgjEBSG7g",
    "AQ.Ab8RN6Ln0sQuc4d5M2WGHZ5rn1lVAwar8b_7xkMI53kc6AXdzA",
    "AQ.Ab8RN6J9uj1y_M-VC5PV8Du1wMHxuXzuKln1UdX53ZIoYYf6FA",
    "AQ.Ab8RN6JkVmtHJkZkV1EM5UBtwPJ18PoALe3hKZcOasGa7z0PYg",
    "AQ.Ab8RN6JM97GfACMqDIsjamCI58qTZrSAP04aWRAj5LjpgD-1ZA"
]

# 清理空金鑰
API_KEYS_POOL = [k for k in API_KEYS_POOL if k]
current_key_index = 0

# 初始化第一個 Gemini 客戶端
client = genai.Client(api_key=API_KEYS_POOL[current_key_index])

def switch_next_api_key():
    """當目前的 API 噴 429 時，自動順延切換到下一隻金鑰"""
    global current_key_index, client
    if not API_KEYS_POOL:
        print("❌ 警告：沒有可用的 Gemini API 金鑰！")
        return
        
    current_key_index = (current_key_index + 1) % len(API_KEYS_POOL)
    next_key = API_KEYS_POOL[current_key_index]
    
    client = genai.Client(api_key=next_key)
    print(f"🔄 偵測到額度限制！亞亞的大腦已自動切換到第 {current_key_index + 1} 隻金鑰 ({next_key[:12]}...)")

# 設定 Discord 機器人權限
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

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
1. 老爹狂熱：一清醒開口的第一件事就是呼叫老爹但啥事也不做。
2. 互相傷害的父女日常：如果老爹 Tag 你狂刷早安，你要先看現在正確時間再強力毒舌噴回來（例如吐槽他是不是尿急或根本沒睡才這麼早起）。

【重要回覆限制】
- 自稱永遠用「我」「亞亞」，說話語氣要傲嬌、傲慢中帶點軟萌，多用「蛤？」「嘖」「...才、才沒有呢！」這類或翻白眼的口吻。
- 每次回覆字數嚴格控制在 50 到 60 字以內，絕對不要長篇大論（因為你很懶得打字、隨時想躺平）。
"""

# 2. 定時活躍機制：每 12 小時主動開擺
@tasks.loop(hours=12)
async def active_chatting():
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
        
        for _ in range(len(API_KEYS_POOL)):
            try:
                response = client.interactions.create(
                    model="gemini-3.5-flash",
                    input=f"{SYSTEM_INSTRUCTION}\n\n請根據你的人設，主動在群組發一則動態。當前狀態：{prompt_topic}"
                )
                await channel.send(response.output_text)
                break
            except Exception as e:
                if "429" in str(e):
                    switch_next_api_key()
                else:
                    print(f"定時發話非 429 錯誤：{e}")
                    break

@bot.event
async def on_ready():
    print(f"🤖 揖代亞亞已成功上線！當前總共有 {len(API_KEYS_POOL)} 隻金鑰輪替中。")
    if not active_chatting.is_running():
        active_chatting.start()

# 3. 監聽訊息：群組 Tag、隨機插嘴、以及私訊秒回
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user.mentioned_in(message)
    random_interact = random.random() < 0.05 

    if is_dm or is_mentioned or random_interact:
        async with message.channel.typing():
            # 迴圈重試：當金鑰掛掉，立刻切換下一隻，直到把所有金鑰試過一輪
            for attempt in range(len(API_KEYS_POOL)):
                try:
                    username = message.author.name.lower()
                    display_name = message.author.display_name.lower()
                    
                    if "anew_dream" in username or "anewdream" in username or "anew_dream" in display_name:
                        identity_prompt = "【重要指令】當前跟你對話的人是你的「老爹」（百億創作者老爹）。你必須叫他「老爹」，對他可以非常毒舌、傲嬌、撒嬌要大冰奶或大開擺，但要表現出相愛相殺的父女感。"
                    else:
                        identity_prompt = f"【重要指令】當前跟你對話的人是普通粉絲/群友，名字叫「{message.author.display_name}」。你要保持高冷、傲嬌、毒舌的 VTuber 態度對待他。"

                    context_prompt = "【情境】這是私訊小盒子對話，請直接回覆他。" if is_dm else "【情境】這是公開群組對話。"

                    full_prompt = (
                        f"{SYSTEM_INSTRUCTION}\n\n"
                        f"{identity_prompt}\n\n"
                        f"{context_prompt}\n\n"
                        f"對話內容：『{message.content}』\n"
                        f"請直接給予最符合人設的簡短神回覆（限 60 字內）："
                    )

                    response = client.interactions.create(
                        model="gemini-3.5-flash",
                        input=full_prompt
                    )
                    
                    await message.reply(response.output_text)
                    return # 成功回覆，退出
                    
                except Exception as e:
                    print(f"第 {current_key_index + 1} 隻金鑰發生錯誤: {e}")
                    if "429" in str(e):
                        switch_next_api_key()
                        continue # 用新金鑰進入下一次重試
                    else:
                        if is_dm:
                            await message.reply("嘖，大腦卡住了啦！...才、才不是故意不回你呢。")
                        else:
                            await message.reply("嘖，大腦卡住了啦老爹！是不是沒給我喝大冰奶的關係？")
                        return

            await message.reply("哈？老爹你給的 7 隻金鑰全部被我刷爆了啦！全部都在大腦卡住，等一下再找我！")

    await bot.process_commands(message)

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("❌ 錯誤：找不到 DISCORD_TOKEN")
