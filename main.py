import os
import json
import discord
import random
import uuid
import datetime
from discord import app_commands
from tls_client import Session

# ---------------- CLIENT ---------------- #
class AClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.synced = False

    async def on_ready(self):
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f"Logged in as {self.user}")

client = AClient()
tree = app_commands.CommandTree(client)

# ---------------- SESSION ---------------- #
session = Session(client_identifier="ios_15_5")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X)"
})

# ---------------- TOKEN STORAGE ---------------- #
def get_tokens():
    try:
        with open('token.json', 'r') as file:
            return json.load(file)
    except:
        return {}

# ---------------- FAST GRID GENERATOR ---------------- #
async def generate_grid(safe_amount):
    spots = random.sample(range(25), min(safe_amount, 24))
    return '\n'.join(
        ''.join(['✅' if (i * 5 + j) in spots else '❌' for j in range(5)])
        for i in range(5)
    )

# ---------------- UNRIG ---------------- #
def unrig(token):
    try:
        response = session.get(
            "https://bloxflip.com/api/provably-fair",
            headers={"x-auth-token": token}
        ).json()

        old_seed = response.get("clientSeed", "Unknown")
        new_seed = str(uuid.uuid4())

        session.post(
            "https://bloxflip.com/api/provably-fair/clientSeed",
            headers={"x-auth-token": token},
            json={"clientSeed": new_seed}
        )

        return discord.Embed(
            title="Unrigged Successfully 🎲",
            color=0x1E90FF,
            description=f"Old Seed: ```{old_seed}```\nNew Seed: ```{new_seed}```"
        )

    except:
        return discord.Embed(
            title='Error',
            color=0xff0000,
            description="Failed to unrig."
        )

# ---------------- CHANNEL CHECK ---------------- #
async def check_channel(interaction):
    if interaction.channel.id != 1492892833105973421:
        await interaction.response.send_message(
            embed=discord.Embed(
                title='🚫 Error',
                color=0xff0000,
                description="Wrong channel."
            ),
            ephemeral=True
        )
        return False
    return True

# ---------------- COMMANDS ---------------- #
@tree.command(name='freemines', description='Mines predictor')
async def mines(interaction: discord.Interaction, tile_amt: int):
    await interaction.response.defer()

    if not await check_channel(interaction):
        return

    auth = get_tokens().get(str(interaction.user.id))

    if not auth:
        await interaction.followup.send(
            embed=discord.Embed(
                title='🚫 Error',
                color=0xff0000,
                description="No token linked."
            )
        )
        return

    try:
        gamebase = session.get(
            "https://bloxflip.com/api/games/mines",
            headers={"x-auth-token": auth}
        ).json()

        if not gamebase.get("hasGame", False):
            await interaction.followup.send(
                embed=discord.Embed(
                    title='🚫 Error',
                    color=0xff0000,
                    description="No active game."
                )
            )
            return

        data = gamebase.get('game', {})
        grid = await generate_grid(tile_amt)

        em = discord.Embed(
            title="Free Predictor 🎲",
            color=0x1E90FF
        )

        em.add_field(name='Grid:', value=f"```\n{grid}\n```")
        em.add_field(name='Safe Clicks:', value=str(tile_amt))
        em.add_field(name='Mines:', value=str(data.get('minesAmount', 'Unknown')))
        em.add_field(name='Bet:', value=str(data.get('betAmount', 'Unknown')))
        em.add_field(name='Round ID:', value=data.get('uuid', 'Unknown'))
        em.add_field(name='User:', value=f"<@{interaction.user.id}>")
        em.set_footer(text=datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p"))

        await interaction.followup.send(embed=em)

    except Exception as e:
        await interaction.followup.send(
            embed=discord.Embed(
                title='🚫 Error',
                color=0xff0000,
                description="Something went wrong."
            )
        )

# ---------------- LINK ---------------- #
@tree.command(name='freelink', description='Link account')
async def link(interaction: discord.Interaction, token: str):
    tokens = get_tokens()
    user_id = str(interaction.user.id)

    tokens[user_id] = token

    with open('token.json', 'w') as file:
        json.dump(tokens, file, indent=4)

    await interaction.response.send_message(
        "✅ Account linked (check DMs)",
        ephemeral=True
    )

# ---------------- UNLINK ---------------- #
@tree.command(name='freeunlink', description='Unlink account')
async def unlink(interaction: discord.Interaction):
    tokens = get_tokens()
    user_id = str(interaction.user.id)

    if user_id in tokens:
        tokens.pop(user_id)

        with open('token.json', 'w') as file:
            json.dump(tokens, file, indent=4)

        await interaction.response.send_message("✅ Unlinked", ephemeral=True)
    else:
        await interaction.response.send_message("No account linked", ephemeral=True)

# ---------------- UNRIG COMMAND ---------------- #
@tree.command(name='freeunrig', description='Unrig seed')
async def unrig_command(interaction: discord.Interaction):
    await interaction.response.defer()

    token = get_tokens().get(str(interaction.user.id))

    if token:
        await interaction.followup.send(embed=unrig(token))
    else:
        await interaction.followup.send("No token linked.")

# ---------------- RUN ---------------- #
import threading
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is running"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()
client.run(os.environ['discordToken'])
