import discord
import asyncio
import os
import sys  # 再起動に使用
from discord.ext import commands

# ボットのインテント設定（DM送信・メンバーイベントを有効化）
intents = discord.Intents.default()
intents.members = True

# Botオブジェクトの生成
bot = commands.Bot(command_prefix="/", intents=intents)

# 環境変数から設定値を取得
TOKEN = os.getenv("DISCORD_TOKEN")  # Botトークン
ROLE_ID = int(os.getenv("DISCORD_ROLE_ID"))  # ロールID
WELCOME_CHANNEL_ID = int(os.getenv("DISCORD_WELCOME_CHANNEL_ID"))  # チャンネルID
ERROR_REPORT_USER_IDS = list(map(int, os.getenv("ERROR_REPORT_USER_IDS", "").split(",")))  # エラー報告を送るユーザーID（複数対応）
BOT_OWNER_IDS = list(map(int, os.getenv("BOT_OWNER_IDS", "").split(",")))  # ボット所有者のユーザーID（複数対応）

# トークンの存在確認
if not TOKEN:
    print("環境変数 DISCORD_TOKEN が設定されていません。ボットを起動できません。")
    exit(1)

# メッセージ送信管理変数
can_send_message = True  # メッセージを送信可能かどうかを示すフラグ

async def report_status():
    """
    1時間ごとにエラーがなかったことを指定されたユーザーにDMで送信
    """
    await bot.wait_until_ready()  # ボットが準備完了するまで待機
    while not bot.is_closed():
        try:
            for user_id in ERROR_REPORT_USER_IDS:
                user = await bot.fetch_user(user_id)
                await user.send("過去1時間、エラーは発生しませんでした。")
        except Exception as e:
            print(f"エラーレポート送信中のエラー: {e}")
        await asyncio.sleep(3600)  # 1時間（3600秒）待機

def is_owner(user_id):
    """
    ボットの所有者かどうかを判定
    """
    return user_id in BOT_OWNER_IDS

@bot.event
async def on_member_join(member):
    """
    新メンバーがサーバーに参加したときに呼び出される
    """
    global can_send_message

    try:
        # ロールの取得
        role = member.guild.get_role(ROLE_ID)
        # チャンネルの取得
        welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)

        if role and welcome_channel and can_send_message:
            # メッセージを送信
            await welcome_channel.send(
                f"ようこそ {role.mention} の皆さん！\n"
                "「お喋りを始める前に、もういくつかステップがあります。」と出ていると思うので、\n"
                "「了解」を押してルールに同意してください。\n"
                "その後、https://discord.com/channels/1165775639798878288/1165775640918773843 で認証をして、みんなとお喋りをしましょう！"
            )
            # メッセージ送信を60秒間停止
            can_send_message = False
            await asyncio.sleep(60)  # 60秒間待機
            can_send_message = True
    except Exception as e:
        # エラー内容をDMで報告
        error_message = f"エラーが発生しました:\n{e}"
        for user_id in ERROR_REPORT_USER_IDS:
            try:
                user = await bot.fetch_user(user_id)
                await user.send(f"エラー通知:\n{error_message}")
            except Exception as dm_error:
                print(f"DM送信エラー: {dm_error}")

@bot.event
async def on_error(event, *args, **kwargs):
    """
    イベント処理中にエラーが発生した場合に呼び出される
    """
    error_message = f"イベント {event} 中にエラーが発生しました:\n{args}\n{kwargs}"
    print(error_message)
    for user_id in ERROR_REPORT_USER_IDS:
        try:
            user = await bot.fetch_user(user_id)
            await user.send(f"エラー通知:\n{error_message}")
        except Exception as dm_error:
            print(f"DM送信エラー: {dm_error}")

@bot.event
async def on_ready():
    """
    ボットが起動し、準備が整ったときに呼び出される
    """
    print(f"ボットが起動しました: {bot.user}")

@bot.event
async def on_disconnect():
    """
    Discordサーバーから切断されたときに呼び出される
    """
    print("Discordサーバーから切断されました。再接続を試みます。")

@bot.event
async def on_resumed():
    """
    Discordサーバーへの接続が再開されたときに呼び出される
    """
    print("Discordサーバーへの接続が再開されました。")

@bot.command()
async def restart(ctx):
    """
    /restart コマンドでボットを再起動
    """
    if ctx.author.id not in BOT_OWNER_IDS:
        await ctx.send("このコマンドを実行する権限がありません。")
        return

    await ctx.send("ボットを再起動しています...")
    print("ボットの再起動をトリガーします。")
    await bot.close()  # ボットを停止
    sys.exit(0)  # プロセスを終了（Railwayの再起動をトリガー）

# 定期タスクとしてエラーレポートを送る
bot.loop.create_task(report_status())

# 非同期的にボットを実行する
async def main():
    try:
        await bot.start(TOKEN)  # 非同期起動
    except Exception as e:
        print(f"ボットの起動中にエラーが発生しました: {e}")

if __name__ == "__main__":
    asyncio.run(main())
