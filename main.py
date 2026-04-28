import os
import json
import discord
import random
import uuid
import datetime
import threading
from flask import Flask
from discord import app_commands
from tls_client import Session

# ---------------- KEEP ALIVE (RENDER FIX) ---------------- #
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    thread = threading.Thread(target=run_web)
    thread.start()

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

# ---------------- TOKEN STORAGE ---------------- #
def get_tokens():
    try:
        with open('token.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def save_tokens(data):
    with open('token.json', 'w') as f:
        json.dump(data, f, indent=4)

# ---------------- FAST "PREDICTOR" ---------------- #
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
            title="Error",
            color=0xff0000,
            description="Failed to unrig"
        )

# ---------------- CHANNEL CHECK ---------------- #
async def check_channel(interaction):
    if interaction.channel.id != 1234573327675166781:
        await interaction.response.send_message(
            "Wrong channel",
            ephemeral=True
        )
        return False
    return True

# ---------------- COMMANDS ---------------- #
@tree.command(name='freemines')
async def mines(interaction: discord.Interaction, tile_amt: int):
    await interaction.response.defer()

    if not await check_channel(interaction):
        return

    auth = get_tokens().get(str(interaction.user.id))

    if not auth:
        await interaction.followup.send("No token linked.")
        return

    try:
        game = session.get(
            "https://bloxflip.com/api/games/mines",
            headers={"x-auth-token": auth}
        ).json()

        if not game.get("hasGame", False):
            await interaction.followup.send("No active game.")
            return

        grid = await generate_grid(tile_amt)

        em = discord.Embed(
            title="Santiel's Predictor 🎲",
            color=0x1E90FF
        )

        em.add_field(name='Grid', value=f"```\n{grid}\n```")
        em.add_field(name='Safe', value=str(tile_amt))
        em.set_footer(text=datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p"))

        await interaction.followup.send(embed=em)

    except Exception as e:
        await interaction.followup.send("Error occurred.")

# ---------------- LINK ---------------- #
@tree.command(name='freelink')
async def link(interaction: discord.Interaction, token: str):
    tokens = get_tokens()
    tokens[str(interaction.user.id)] = token
    save_tokens(tokens)

    await interaction.response.send_message("Linked ✅", ephemeral=True)

# ---------------- UNLINK ---------------- #
@tree.command(name='freeunlink')
async def unlink(interaction: discord.Interaction):
    tokens = get_tokens()
    user_id = str(interaction.user.id)

    if user_id in tokens:
        tokens.pop(user_id)
        save_tokens(tokens)
        await interaction.response.send_message("Unlinked ✅", ephemeral=True)
    else:
        await interaction.response.send_message("No token", ephemeral=True)

# ---------------- UNRIG COMMAND ---------------- #
@tree.command(name='freeunrig')
async def unrig_command(interaction: discord.Interaction):
    await interaction.response.defer()

    token = get_tokens().get(str(interaction.user.id))

    if token:
        await interaction.followup.send(embed=unrig(token))
    else:
        await interaction.followup.send("No token linked.")

# ---------------- RUN ---------------- #
keep_alive()
client.run(os.environ['discordToken'])
