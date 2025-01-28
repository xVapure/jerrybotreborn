import discord
from discord.ext import commands
import random
import asyncio
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import re
import string
import math

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

AUTHORIZED_USERS = ["1027407264191107112", "679943533460717588","834288163940728851"]

# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="j!", intents=intents)
bot.remove_command("help")

# Tracks users who are in the middle an interaction.
ongoing_interactions = {}

@bot.event
async def on_command(ctx):
    # Notify users who attempt to use other commands while in an interaction
    if ctx.author.id in ongoing_interactions:
        channel_id = ongoing_interactions[ctx.author.id]
        await ctx.reply(
            f"You have an ongoing action that requires your confirmation inside of <#{channel_id}>. "
            "Please complete or cancel it before using other commands."
        )
        return

# Load or create the user database
data_file = "users.json"
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

with open(data_file, "r") as f:
    users = json.load(f)

# Helper functions
def save_users():
    with open(data_file, "w") as f:
        json.dump(users, f, indent=4)

def get_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "balance": 40,
            "job_level": 0,
            "inventory": {}
        }
        # Add exclusive items to the dev user's inventory
        if str(user_id) == "1027407264191107112":
            users[str(user_id)]["inventory"]["10"] = 1  # Unicorn
            users[str(user_id)]["inventory"]["18"] = 1  # Poseidon
        save_users()
    return users[str(user_id)]

def add_item(user_id, item_id, amount):
    user = get_user(user_id)
    if item_id in user["inventory"]:
        user["inventory"][item_id] += amount
    else:
        user["inventory"][item_id] = amount
    save_users()

def remove_item(user_id, item_id, amount):
    user = get_user(user_id)
    if item_id in user["inventory"] and user["inventory"][item_id] >= amount:
        user["inventory"][item_id] -= amount
        if user["inventory"][item_id] == 0:
            del user["inventory"][item_id]
        save_users()
        return True
    return False

# Hunting and fishing probabilities and items
hunting_animals = {
    "3": {"name": "Deer", "probability": 0.5, "price":"Not for sale", "sell_price": 4, "usable":"no"},
    "4": {"name": "Wild Boar", "probability": 0.25, "price":"Not for sale", "sell_price": 8, "usable":"no"},
    "5": {"name": "Elk", "probability": 0.0625, "price":"Not for sale", "sell_price": 16, "usable":"no"},
    "6": {"name": "Mountain Lion", "probability": 0.01, "price":"Not for sale", "sell_price": 50, "usable":"no"},
    "7": {"name": "Eagle", "probability": 0.002, "price":"Not for sale", "sell_price": 10000, "usable":"no"},
    "8": {"name": "Snow Leopard", "probability": 0.001, "price":"Not for sale", "sell_price": 15000, "usable":"no"},
    "9": {"name": "The Dragon", "probability": 0.00001, "price":"Not for sale", "sell_price": 100000, "usable":"no"},
    "10": {"name": "Unicorn", "probability": 0.0, "price":"Not for sale", "sell_price": 9e+19489293432984329342, "usable":"no"},
}

fishing_fish = {
    "11": {"name": "Bluegill Fish", "probability": 0.5, "price":"Not for sale", "sell_price": 4, "usable":"no"},
    "12": {"name": "Salmon", "probability": 0.25, "price":"Not for sale", "sell_price": 8, "usable":"no"},
    "13": {"name": "Tuna", "probability": 0.0625, "price":"Not for sale", "sell_price": 16, "usable":"no"},
    "14": {"name": "Shark", "probability": 0.01, "price":"Not for sale", "sell_price": 50, "usable":"no"},
    "15": {"name": "Whales", "probability": 0.002, "price":"Not for sale", "sell_price": 10000, "usable":"no"},
    "16": {"name": "Orca", "probability": 0.001, "price":"Not for sale", "sell_price": 15000, "usable":"no"},
    "17": {"name": "The Leviathan", "probability": 0.00001, "price":"Not for sale", "sell_price": 100000, "usable":"no"},
    "18": {"name": "Poseidon", "probability": 0.0, "price":"Not for sale", "sell_price": 9e+19489293432984329342, "usable":"no"},
}

market_items = {
    "1": {"name": "Fishing Rod", "price": 150, "sell_price": 20, "usable":"no"},
    "2": {"name": "Hunting Rifle", "price": 150, "sell_price": 20, "usable":"no"},
    "23": {"name": "Dragon's Lure", "price": 10000000, "sell_price": 30000, "usable":"yes"},
    "24": {"name": "Leviathan's Charm", "price": 10000000, "sell_price": 30000, "usable":"yes"},
    "25": {"name": "Life-saver", "price": 320, "sell_price": 1, "usable":"yes"}
}

Admin_excl = {
    "0": {"name": "xVapure", "probability": 0.0, "sell_price": -1, "usable":"no"},
    "i": {"name": "Kamui", "probability": 0.0, "sell_price": -1, "usable":"no"},
    "-1": {"name": "Test_placeholder", "probability": 0.0, "sell_price": -1, "usable":"no"},
    "-2": {"name": "NotVentea", "probability": 0.0, "sell_price": -1, "usable":"no"}
    
}

Other_items = {
    "19": {"name": "Leviathan Segment", "probability": 0.0, "sell_price": 70000, "usable":"no"},
    "20": {"name": "Dragon's Body", "probability": 0.0, "sell_price": 70000, "usable":"no"},
    "21": {"name": "Dragon's Tail", "probability": 0.0, "sell_price": 30000, "usable":"no"},
    "22": {"name": "Leviathan's Tail", "probability": 0.0, "sell_price": 30000, "usable":"no"},
}

Mutations = {
    "3.5": {"name": "Deer [MUTATED]", "probability": 0.0, "sell_price": 4, "usable":"no"},
    "4.5": {"name": "Wild Boar [MUTATED]", "probability": 0.0, "sell_price": 8, "usable":"no"},
    "5.5": {"name": "Elk [MUTATED]", "probability": 0.0, "sell_price": 16, "usable":"no"},
    "6.5": {"name": "Mountain Lion [MUTATED]", "probability": 0.0, "sell_price": 50, "usable":"no"},
    "7.5": {"name": "Eagle [MUTATED]", "probability": 0.0, "sell_price": 10000, "usable":"no"},
    "8.5": {"name": "Snow Leopard [MUTATED]", "probability": 0.0, "sell_price": 15000, "usable":"no"},
    "9.5": {"name": "The Dragon [MUTATED]", "probability": 0.0, "sell_price": 100000, "usable":"no"},
    "10.5": {"name": "Unicorn [MUTATED]", "probability": 0.0, "sell_price": 9e+19489293432984329342, "usable":"no"},
    "11.5": {"name": "Bluegill Fish [MUTATED]", "probability": 0.0, "sell_price": 4, "usable":"no"},
    "12.5": {"name": "Salmon [MUTATED]", "probability": 0.0, "sell_price": 8, "usable":"no"},
    "13.5": {"name": "Tuna [MUTATED]", "probability": 0.0, "sell_price": 16, "usable":"no"},
    "14.5": {"name": "Shark [MUTATED]", "probability": 0.0, "sell_price": 50, "usable":"no"},
    "15.5": {"name": "Whales [MUTATED]", "probability": 0.0, "sell_price": 10000, "usable":"no"},
    "16.5": {"name": "Orca [MUTATED]", "probability": 0.0, "sell_price": 15000, "usable":"no"},
    "17.5": {"name": "The Leviathan [MUTATED]", "probability": 0.00001, "sell_price": 100000, "usable":"no"},
    "18.5": {"name": "Poseidon [MUTATED]", "probability": 0.0, "sell_price": 9e+19489293432984329342, "usable":"no"},
}

#Newest item is 25

# Combine all items for easier inventory and sell logic
all_items = {**market_items, **hunting_animals, **fishing_fish, **Admin_excl, **Other_items, **Mutations}

# Bot events
@bot.event
async def on_ready():
    print("TOKEN/password is correct, logging into {0.user}!".format(bot))
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing,name="j!help"))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply("It looks like you're missing some required arguments for this command. Use `j!help` to learn more.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.reply(f"This command is on cooldown. Please try again in {round(error.retry_after, 2)} seconds.")
    elif isinstance(error, commands.BadArgument):
        await ctx.reply("Invalid argument provided. Please check your input and try again. Use `j!help` to learn more.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.reply("Command not found. Use `j!help` to see the available commands.")
    else:
        await ctx.reply("An unexpected error occurred. Please try again later.")

# Commands
@bot.command(aliases=["reg"])
async def register(ctx):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if str(ctx.author.id) in users:
        await ctx.reply("You are already registered!")
        return

    user = get_user(ctx.author.id)
    await ctx.reply(f"Welcome, <@{ctx.author.id}>! You have been registered with $40.")

@bot.command()
async def help(ctx, page: int = 1):
    commands_list = [
        "- `j!register/j!reg`: Register to start using the bot.",
        "- `j!work`: Earn money by working.\n   - `j!work upgrade`: Upgrade job tiers.",
        "- `j!beg`: Beg for money (50% chance).",
        "- `j!market`: Opens the market menu.\n   - `j!market buy <item id> <amount>`: Self-explanatory.\n   - `j!market sell <item id> <amount>`/`j!market sell <item id> all`: Self-explanatory",
        "- `j!hunt`: Hunt animals for profit (requires a hunting rifle).",
        "- `j!fish`: Fish for profit (requires a fishing rod).",
        "- `j!inventory <page>`: View your or another user's inventory.\n   - `j!inventory check <@user> <page>` to check their inventory.",
        "- `j!balance/j!bal`: Check your balance.",
        "- `j!trade <@user> <your item id> <their item id>`: Trade items with other users.",
        "- `j!gift <@user> <item> <amount>`: To gift items to a user.\n   - `j!gift money <@user> <amount>`: To gift money.",
        "- `j!iteminfo <item id>`: Checks an item's information.",
        "- `j!daily`: Receive a small amount of cash ($5-10) every 24 hours.",
        "- `j!gamble <money amount> <desired multiplier>`: Gamble and cash out at your desired multiplier.",
        "- `j!duel <@user> <money amount>`: Duel a user (50% chance of winning), winner takes it all.",
        "- `j!use <item id> <amount>`: Use an item.",
        "- `j!resetdata`: Reset a user's data (admin only).",
        "- `j!setbal <@user> <amount>`: Set a user's balance (admin only).",
        "- `j!spawn <item id>`: Spawn an item (admin only).",
        "- `j!auction`: Opens the auction help menu.",
        "- `j!itemlist <page>`: Self-explanatory.",
        "- `j!passive <on/off>`: Enabling this will prevent you from being invited to trade/duels.",
        "- `j!crime`: Opens the crime menu, you can earn cash when you complete a crime OR you could die and lose 40% of your balance and a random item inside your inventory."
    ]

    items_per_page = 10
    total_pages = math.ceil(len(commands_list) / items_per_page)

    if page < 1 or page > total_pages:
        await ctx.reply(f"Invalid page number. Please choose a page between 1 and {total_pages}.")
        return

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_commands = commands_list[start_idx:end_idx]

    help_text = (
        "**Jerry Bot Help**\n"
        "Prefix: `j!`\n"
        "Commands (Page {page}/{total_pages}):\n".format(page=page, total_pages=total_pages)
    )
    help_text += "\n".join(page_commands)

    if page < total_pages:
        help_text += f"\n\nUse `j!help {page + 1}` to view the next page."
    elif page > 1:
        help_text += f"\n\nUse `j!help {page - 1}` to view the previous page."

    await ctx.reply(help_text)

@bot.command(aliases=["bal"])
async def balance(ctx, user: discord.User = None):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    user = user or ctx.author
    
    # Fetch the user's data
    user_data = get_user(user.id)
    
    # Reply with the user's balance
    await ctx.reply(f"`{user.name}'s` current balance is ${user_data['balance']}")

@bot.command()
@commands.cooldown(1, 20, commands.BucketType.user)
async def work(ctx, action=None):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for this command
    user = get_user(ctx.author.id)

    job_tiers = [
        {"name": "Newly Employed", "min": 1, "max": 5, "cost": 0},
        {"name": "Employee", "min": 1, "max": 10, "cost": 70},
        {"name": "Manager", "min": 3, "max": 20, "cost": 140},
        {"name": "Boss", "min": 10, "max": 50, "cost": 280},
        {"name": "C.E.O", "min": 70, "max": 400, "cost": 1000},
    ]

    if action == "upgrade":
        if user["job_level"] < len(job_tiers) - 1:
            next_tier = job_tiers[user["job_level"] + 1]
            if user["balance"] >= next_tier["cost"]:
                user["balance"] -= next_tier["cost"]
                user["job_level"] += 1
                save_users()
                await ctx.reply(f"You have upgraded to {next_tier['name']}!")
            else:
                await ctx.reply("You don't have enough money to upgrade.")
        else:
            await ctx.reply("You are already at the highest job tier.")
    else:
        tier = job_tiers[user["job_level"]]
        earnings = random.randint(tier["min"], tier["max"])
        user["balance"] += earnings
        save_users()
        await ctx.reply(f"You worked as a {tier['name']} and earned ${earnings}!")

@bot.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def beg(ctx):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for this command

    user = get_user(ctx.author.id)
    if random.random() < 0.5:
        amount = random.randint(1, 5)
        user["balance"] += amount
        save_users()
        await ctx.reply(f"Someone took pity on you and gave you ${amount}!")
    else:
        await ctx.reply("No one gave you any money. Try again later.")

pending_confirmations = {}

@bot.command(aliases=["shop"])
async def market(ctx, action=None, item_id=None, amount=None):
    if ctx.author.id in ongoing_interactions:
        await ctx.reply("You are already in a pending action. Complete or cancel it before starting a new one.")
        return

    user = get_user(ctx.author.id)

    if action is None:
        # Default action to display market items
        page = int(item_id) if item_id and item_id.isdigit() else 1
        items_per_page = 5
        total_pages = -(-len(market_items) // items_per_page)  # Calculate total pages

        if page < 1 or page > total_pages:
            await ctx.reply(f"Invalid page number. Please choose a page between 1 and {total_pages}.")
            return

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        items_on_page = list(market_items.items())[start_idx:end_idx]

        market_list = "\n".join([
            f"ID: `{item_id}` - {item['name']} (${item['price']})"
            for item_id, item in items_on_page
        ])
        await ctx.reply(f"**Market Items (Page {page}/{total_pages}):**\n{market_list}\n\n-# Use `j!shop <page>` to navigate between shop pages, `j!shop buy <item id> <amount>` to buy items and `j!shop sell <item id> <amount>` to sell")
        return

    if action.lower() == "buy":
        if not item_id or not amount or not amount.isdigit() or item_id not in market_items:
            await ctx.reply("Invalid input. Use `j!market buy <item id> <amount>`.")
            return

        amount = int(amount)
        item = market_items[item_id]
        total_price = item["price"] * amount

        if user["balance"] < total_price:
            await ctx.reply("You don't have enough money to buy this quantity of the item.")
            return

        ongoing_interactions[ctx.author.id] = ctx.channel.id
        pending_confirmations[ctx.author.id] = ("buy", item_id, amount, ctx.channel.id)
        await ctx.reply(
            f"Confirm buying {amount}x {item['name']} for ${total_price}.\n"
            "Type `buy confirm` to confirm or `buy cancel` to cancel."
        )
        return

    if action.lower() == "sell":
        if not item_id or (amount != "all" and not amount.isdigit()):
            await ctx.reply("Invalid input. Use `j!market sell <item id> <amount>` or `j!market sell <item id> all`.")
            return

        if item_id not in user["inventory"]:
            await ctx.reply("You don't have this item in your inventory.")
            return

        if amount == "all":
            amount = user["inventory"][item_id]  # Total amount of the item
        else:
            amount = int(amount)

        if amount <= 0 or user["inventory"].get(item_id, 0) < amount:
            await ctx.reply("Invalid input or insufficient inventory.")
            return

        item = all_items[item_id]
        total_price = item["sell_price"] * amount

        ongoing_interactions[ctx.author.id] = ctx.channel.id
        pending_confirmations[ctx.author.id] = ("sell", item_id, amount, ctx.channel.id)
        await ctx.reply(
            f"Confirm selling {amount}x {item['name']} for ${total_price}.\n"
            "Type `sell confirm` to confirm or `sell cancel` to cancel."
        )
        return

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() in {"buy confirm", "buy cancel", "sell confirm", "sell cancel"}:
        if message.author.id not in pending_confirmations:
            await message.channel.send("You have no pending actions to confirm or cancel.")
            return

        action, item_id, amount, channel_id = pending_confirmations[message.author.id]

        if message.channel.id != channel_id:
            await message.channel.send("Confirm or cancel in the channel where the action was initiated.")
            return

        if message.content.lower().endswith("cancel"):
            del pending_confirmations[message.author.id]
            del ongoing_interactions[message.author.id]
            await message.channel.send("Action canceled.")
            return

        user = get_user(message.author.id)

        if action == "buy" and message.content.lower() == "buy confirm":
            item = market_items[item_id]
            total_price = item["price"] * amount
            user["balance"] -= total_price
            add_item(message.author.id, item_id, amount)
            await message.channel.send(f"You bought {amount}x {item['name']} for ${total_price}.")

        elif action == "sell" and message.content.lower() == "sell confirm":
            item = all_items[item_id]
            total_price = item["sell_price"] * amount
            remove_item(message.author.id, item_id, amount)
            user["balance"] += total_price
            save_users()
            await message.channel.send(f"You sold {amount}x {item['name']} for ${total_price}.")

        del pending_confirmations[message.author.id]
        del ongoing_interactions[message.author.id]
        return

    await bot.process_commands(message)

@bot.command()
async def use(ctx, item_id: str, amount: int):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if amount <= 0:
        await ctx.reply("Invalid amount. Please enter a positive integer.")
        return

    user = get_user(ctx.author.id)
    
    # Validate the item and amount
    if item_id not in ["23", "24"]:
        await ctx.reply("This item cannot be used.")
        return
    
    if item_id not in user["inventory"] or user["inventory"][item_id] < amount:
        await ctx.reply("You don't have enough of this item to use.")
        return

    # Consume the item
    if not remove_item(ctx.author.id, item_id, amount):
        await ctx.reply("Failed to use the item.")
        return

    # Set the flags based on the item used
    if item_id == "23":
        user["next_hunt_dragon"] = user.get("next_hunt_dragon", 0) + amount
        await ctx.reply(f"You used {amount} Dragon's Lure(s)! The next {user['next_hunt_dragon']} hunt(s) will guarantee a Dragon spawn.")
    elif item_id == "24":
        user["next_fish_leviathan"] = user.get("next_fish_leviathan", 0) + amount
        await ctx.reply(f"You used {amount} Leviathan's Charm(s)! The next {user['next_fish_leviathan']} fish(es) will guarantee a Leviathan spawn.")

    save_users()

@bot.command()
@commands.cooldown(1, 35, commands.BucketType.user)
async def hunt(ctx):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)

    user = get_user(ctx.author.id)
    if "2" not in user["inventory"] or user["inventory"]["2"] <= 0:
        await ctx.reply("You need a hunting rifle to hunt.")
        return

    # Determine if Dragon is guaranteed to spawn
    guaranteed_dragon = user.get("next_hunt_dragon", 0) > 0
    loot = []
    dragon_spawned = False

    for animal_id, animal in hunting_animals.items():
        if animal_id == "9":  # "The Dragon"
            if guaranteed_dragon:
                dragon_spawned = True
                user["next_hunt_dragon"] -= 1
                save_users()
            elif random.random() < animal["probability"]:
                dragon_spawned = True
        elif random.random() < animal["probability"]:
            loot.append(animal_id)

    if dragon_spawned:
        await ctx.reply("A Dragon has appeared! Type `shoot the dragon` within 10 seconds to try and claim it!")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            if msg.content.lower() == "shoot the dragon":
                if random.random() < 0.1:  # 10% chance to catch
                    dragon_id = "9.5" if random.random() < 0.01 else "9"  # 1% chance to mutate
                    add_item(ctx.author.id, dragon_id, 1)
                    dragon_name = Mutations[dragon_id]["name"] if ".5" in dragon_id else hunting_animals[dragon_id]["name"]
                    await ctx.reply(f"You successfully captured {dragon_name}! It has been added to your inventory.")
                else:
                    item = "20" if random.random() < 0.3 else "21"  # Body (30%) or Tail (70%)
                    add_item(ctx.author.id, item, 1)
                    await ctx.reply(f"The Dragon escaped! You salvaged its {Other_items[item]['name']}.")
            else:
                await ctx.reply("You failed to type the phrase correctly. The Dragon escaped!")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The Dragon has flown away.")

    if loot:
        loot_with_mutations = []
        for item in loot:
            mutated = f"{item}.5" if random.random() < 0.01 else item
            add_item(ctx.author.id, mutated, 1)
            loot_with_mutations.append(mutated)

        loot_names = ", ".join([Mutations[item]["name"] if ".5" in item else hunting_animals[item]["name"] for item in loot_with_mutations])
        await ctx.reply(f"You went hunting and caught: {loot_names}!")
    else:
        await ctx.reply("You went hunting but found nothing.")

@bot.command()
@commands.cooldown(1, 35, commands.BucketType.user)
async def fish(ctx):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)

    user = get_user(ctx.author.id)
    if "1" not in user["inventory"] or user["inventory"]["1"] <= 0:
        await ctx.reply("You need a fishing rod to fish.")
        return

    # Determine if Leviathan is guaranteed to spawn
    guaranteed_leviathan = user.get("next_fish_leviathan", 0) > 0
    loot = []
    leviathan_spawned = False

    for fish_id, fish in fishing_fish.items():
        if fish_id == "17":  # "The Leviathan"
            if guaranteed_leviathan:
                leviathan_spawned = True
                user["next_fish_leviathan"] -= 1
                save_users()
            elif random.random() < fish["probability"]:
                leviathan_spawned = True
        elif random.random() < fish["probability"]:
            loot.append(fish_id)

    if leviathan_spawned:
        await ctx.reply("A Leviathan has appeared! Type `shoot the leviathan` within 10 seconds to try and claim it!")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            if msg.content.lower() == "shoot the leviathan":
                if random.random() < 0.1:  # 10% chance to catch
                    leviathan_id = "17.5" if random.random() < 0.01 else "17"  # 1% chance to mutate
                    add_item(ctx.author.id, leviathan_id, 1)
                    leviathan_name = Mutations[leviathan_id]["name"] if ".5" in leviathan_id else fishing_fish[leviathan_id]["name"]
                    await ctx.reply(f"You successfully captured {leviathan_name}! It has been added to your inventory.")
                else:
                    item = "19" if random.random() < 0.3 else "22"  # Segment (30%) or Tail (70%)
                    add_item(ctx.author.id, item, 1)
                    await ctx.reply(f"The Leviathan escaped! You salvaged its {Other_items[item]['name']}.")
            else:
                await ctx.reply("You failed to type the phrase correctly. The Leviathan escaped!")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The Leviathan has swum away.")

    if loot:
        loot_with_mutations = []
        for item in loot:
            mutated = f"{item}.5" if random.random() < 0.01 else item
            add_item(ctx.author.id, mutated, 1)
            loot_with_mutations.append(mutated)

        loot_names = ", ".join([Mutations[item]["name"] if ".5" in item else fishing_fish[item]["name"] for item in loot_with_mutations])
        await ctx.reply(f"You went fishing and caught: {loot_names}!")
    else:
        await ctx.reply("You went fishing but caught nothing.")

@bot.command(aliases=["inv"])
async def inventory(ctx, *args):
    if len(args) == 0:
        # Default behavior: User's own inventory, page 1
        user = ctx.author
        page = 1
    elif len(args) == 1:
        # Either page number for user's inventory or "check"
        if args[0].isdigit():
            user = ctx.author
            page = int(args[0])
        elif args[0].lower() == "check":
            await ctx.reply("Please specify a user to check their inventory. Usage: `j!inventory check <@user> <page>`")
            return
        else:
            await ctx.reply("Invalid usage. Use `j!inventory <page>` or `j!inventory check <@user> <page>`.")
            return
    elif len(args) == 2 and args[0].lower() == "check":
        # "check <@user>" - defaults to page 1
        try:
            user = await commands.UserConverter().convert(ctx, args[1])
            page = 1
        except commands.UserNotFound:
            await ctx.reply("Invalid usage. Use `j!inventory <page>` or `j!inventory check <@user> <page>`.")
            return
    elif len(args) == 3 and args[0].lower() == "check":
        # "check <@user> <page>"
        try:
            user = await commands.UserConverter().convert(ctx, args[1])
            if not args[2].isdigit():
                raise ValueError("Invalid page number.")
            page = int(args[2])
        except commands.UserNotFound:
            await ctx.reply("User not found. Please mention a valid user.")
            return
        except ValueError:
            await ctx.reply("Invalid page number. Please enter a valid number.")
            return
    else:
        await ctx.reply("Invalid usage. Use `j!inventory <page>` or `j!inventory check <@user> <page>`.")
        return

    user_data = get_user(user.id)
    inventory = user_data.get("inventory", {})

    if not inventory:
        await ctx.reply(f"`{user.name}'s` inventory is empty.")
        return

    items_per_page = 10
    total_items = len(inventory)
    total_pages = math.ceil(total_items / items_per_page)

    if page < 1 or page > total_pages:
        await ctx.reply(f"Invalid page number. Please choose between 1 and {total_pages}.")
        return

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page

    inventory_slice = list(inventory.items())[start_idx:end_idx]
    items = "\n".join(
        [
            f"ID: `{item}`: ({all_items.get(item, { 'name': 'Unknown' })['name']}): {count}"
            for item, count in inventory_slice
        ]
    )
    await ctx.reply(f"`{user.name}'s` Inventory (Page {page} of {total_pages}):\n{items}\n\n-#    Use `j!inventory <page>` or `<j!inventory check <@user> <page>` to move between pages.")


@bot.command()
async def grant(ctx, target: discord.User, item_id: str, amount: int = 1):
    # Check if the command issuer is an authorized user
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("You do not have permission to use this command.")
        return

    if item_id.lower() == "all":
        # Grant all items with the specified quantity
        for item_key, item in all_items.items():
            add_item(target.id, item_key, amount)
        await ctx.reply(f"Granted {amount} of every item to `{target.name}`.")
        return

    # Validate the specific item ID
    if item_id not in all_items:
        await ctx.reply("Invalid item ID.")
        return

    # Add the item to the target user's inventory
    add_item(target.id, item_id, amount)
    item_name = all_items[item_id]["name"]
    await ctx.reply(f"Granted {amount}x {item_name} to `{target.name}`.")

@bot.command()
async def gift(ctx, target: discord.User, gift_type: str, amount: int):
    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    # Ensure the user is not gifting to themselves
    if target.id == ctx.author.id:
        await ctx.reply("You cannot gift to yourself.")
        return

    # Fetch the giver's and recipient's data
    giver = get_user(ctx.author.id)
    recipient = get_user(target.id)

    if gift_type.lower() == "money":
        # Validate the giver's balance
        if giver["balance"] < amount:
            await ctx.reply("You don't have enough money to gift.")
            return
        
        # Transfer money
        giver["balance"] -= amount
        recipient["balance"] += amount
        save_users()
        await ctx.reply(f"You gifted ${amount} to `{target.name}`!")
    
    elif gift_type.lower() in all_items:
        item_id = gift_type.lower()
        
        # Validate the giver's inventory
        if item_id not in giver["inventory"] or giver["inventory"][item_id] < amount:
            await ctx.reply("You don't have enough of that item to gift.")
            return
        
        # Transfer items
        remove_item(ctx.author.id, item_id, amount)
        add_item(target.id, item_id, amount)
        item_name = all_items[item_id]["name"]
        await ctx.reply(f"You gifted {amount}x {item_name} to `{target.name}`!")
    else:
        await ctx.reply("Invalid gift type. Use `money` or a valid item ID.")

@bot.command(aliases = ["resetdata"])
async def reset(ctx, target: discord.User):
    # Ensure the command issuer is the authorized admin
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("You do not have permission to use this command.")
        return

    # Reset the target user's data
    user_id = str(target.id)
    users[user_id] = {
        "balance": 40,
        "job_level": 0,
        "inventory": {}
    }
    save_users()
    await ctx.reply(f"`{target.name}'s` data has been reset.")

@bot.command(aliases = ["setbal"])
async def setbalance(ctx, target: discord.User, amount: int):
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("You do not have permission to use this command.")
        return

    # Set the target user's balance
    user = get_user(target.id)
    user["balance"] = amount
    save_users()
    await ctx.reply(f"`{target.name}'s` balance has been set to ${amount}.")

@bot.command()
async def stats(ctx, target: discord.User):
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("You do not have permission to use this command.")
        return

    user_data = get_user(target.id)
    inventory = "\n".join([f"{all_items[item]['name']}: {count}" for item, count in user_data["inventory"].items()]) or "Empty"
    await ctx.reply(
        f"**{target.name}'s Stats:**\n"
        f"- Balance: ${user_data['balance']}\n"
        f"- Job Level: {user_data['job_level']}\n"
        f"- Inventory:\n{inventory}"
    )

@bot.command()
async def itemlist(ctx, page: int = 1):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve.")
        return
    
    # Exclude admin-exclusive items
    user_items = {key: value for key, value in all_items.items() if key not in Admin_excl}
    
    items_per_page = 5
    total_items = len(user_items)
    total_pages = -(-total_items // items_per_page)  # Calculate total pages using ceiling division
    
    if page < 1 or page > total_pages:
        await ctx.reply(f"Invalid page number. Please choose a page between 1 and {total_pages}.")
        return

    # Get the items for the current page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    items_on_page = list(user_items.items())[start_idx:end_idx]
    
    # Format the item list for display
    item_list = "\n".join([
        f"ID: `{item_id}` - {item['name']} (${item.get('sell_price', 0)})"
        for item_id, item in items_on_page
    ])
    
    if item_list:
        await ctx.reply(f"**Item List (Page {page}/{total_pages}):**\n{item_list}\n\n-# Use `j!itemlist <page>` to navigate between pages.")
    else:
        await ctx.reply("No items available.")

@bot.command()
async def daily(ctx):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    user = get_user(ctx.author.id)
    last_claimed_key = "last_daily"
    now = datetime.utcnow()

    # Check if the user has a 'last_daily' timestamp
    if last_claimed_key in user:
        last_claimed = datetime.fromisoformat(user[last_claimed_key])
        if now - last_claimed < timedelta(days=1):
            remaining_time = timedelta(days=1) - (now - last_claimed)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.reply(
                f"You've already claimed your daily reward. Try again in {hours}h {minutes}m {seconds}s."
            )
            return

    # Grant the reward and update the timestamp
    reward = random.randint(5, 10)
    user["balance"] += reward
    user[last_claimed_key] = now.isoformat()
    save_users()

    await ctx.reply(f"You've claimed your daily reward of ${reward}!")

@bot.command()
async def iteminfo(ctx, item_id: str):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return

    # Check if the item exists in the all_items dictionary
    if item_id not in all_items:
        await ctx.reply("Invalid item ID. Please check the item list and try again.")
        return

    # Fetch item details
    item = all_items[item_id]
    name = item["name"]
    sell_price = item.get("price", "Not for sale")
    resell_price = item.get("sell_price", "N/A")
    probability = item.get("probability", "Cannot be dropped")
    usable = item.get("usable", "no")

    # Get user inventory to display the number of copies owned
    user_data = get_user(ctx.author.id)
    owned = user_data["inventory"].get(item_id, 0)

    # Add a description for each item
    descriptions = {
        "1": "A basic fishing rod for catching fish. Not usable directly.",
        "2": "A hunting rifle used for hunting animals. Not usable directly.",
        "3": "A deer that you hunted. No specific use.",
        "4": "A wild boar that you hunted. No specific use.",
        "5": "An elk that you hunted. No specific use.",
        "6": "A mountain lion that you hunted. No specific use.",
        "7": "An eagle that you hunted. No specific use.",
        "8": "A rare snow leopard. No specific use.",
        "9": "The legendary Dragon. No specific use.",
        "10": "A mystical Unicorn. No specific use.",
        "11": "A common bluegill fish. No specific use.",
        "12": "A fresh salmon. No specific use.",
        "13": "A large tuna. No specific use.",
        "14": "A dangerous shark. No specific use.",
        "15": "A massive whale. No specific use.",
        "16": "An intelligent orca. No specific use.",
        "17": "The mythical Leviathan. No specific use.",
        "18": "Poseidon, god of the seas. No specific use.",
        "19": "A segment of the Leviathan. No specific use.",
        "20": "The body of a Dragon. No specific use.",
        "21": "The tail of a Dragon. No specific use.",
        "22": "The tail of a Leviathan. No specific use.",
        "23": "A lure that guarantees a Dragon spawn in your next hunt. Usable, comsumes on usage.",
        "24": "A charm that guarantees a Leviathan spawn in your next fishing attempt. Usable, comsumes on usage.",
        "25": "An item that saves you when you die if you have one inside your inventory. Not usable directly",
        "-1": "An item used for testing purposes."
    }

    for key, value in Mutations.items():
        descriptions[key] = f"A mutated version of {value['name']}. No specific use."

    description = descriptions.get(item_id, "No description available.")

    # Send item information to the user
    await ctx.reply(
        f"**Item Information**\n"
        f"- **Name**: {name}\n"
        f"- **Sell Price**: ${sell_price}\n"
        f"- **Resell Price**: ${resell_price}\n"
        f"- **Usable?**: {usable}\n"
        f"- **Owned**: {owned} copies\n"
        f"- **Description**: {description}\n"
    )


@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def gamble(ctx, amount: int, multiplier: int):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for this command

    user = get_user(ctx.author.id)

    # Validate inputs
    if amount <= 0:
        await ctx.reply("The bet amount must be greater than 0.")
        return

    if multiplier <= 1:
        await ctx.reply("The multiplier must be greater than 1.")
        return

    # Ensure amount and multiplier are integers
    if not isinstance(amount, int) or not isinstance(multiplier, int):
        await ctx.reply("Both the bet amount and multiplier must be whole numbers (integers).")
        return

    if user["balance"] < amount:
        await ctx.reply("You don't have enough money to place this bet.")
        return

    # Calculate winning odds
    winning_probability = 1 / multiplier

    # Determine outcome
    if random.random() < winning_probability:
        # User wins
        winnings = int(amount * multiplier)
        user["balance"] += winnings
        save_users()
        await ctx.reply(f"Congratulations! You won ${winnings}! Your new balance is ${user['balance']}.")
    else:
        # User loses
        user["balance"] -= amount
        save_users()
        await ctx.reply(f"You lost the bet and lost ${amount}. Your new balance is ${user['balance']}.")

@bot.command()
async def duel(ctx, target: discord.User, amount: int):
    # Check if either user is already in another interaction
    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    
    if challenger.get("passive_mode", False):
        await ctx.reply("You cannot start a duel while in passive mode.")
        return

    if opponent.get("passive_mode", False):
        await ctx.reply(f"`{target.name}` is in passive mode and cannot be invited to a duel.")
        return

    # Validate the duel amount
    if amount <= 0:
        await ctx.reply("The amount must be greater than 0.")
        return

    challenger = get_user(ctx.author.id)
    opponent = get_user(target.id)

    # Ensure both users have enough balance
    if challenger["balance"] < amount:
        await ctx.reply("You don't have enough money for this duel.")
        return

    if opponent["balance"] < amount:
        await ctx.reply(f"`{target.name}` does not have enough money for this duel.")
        return

    # Add users to ongoing interactions (store channel ID)
    ongoing_interactions[ctx.author.id] = ctx.channel.id
    ongoing_interactions[target.id] = ctx.channel.id

    # Notify the participants about the duel
    await ctx.reply(
        f"<@{ctx.author.id}> has challenged <@{target.id}> to a duel for ${amount}!\n"
        "Both participants must type `duel accept` in this channel to proceed, "
        "or either can type `duel cancel` to decline."
    )

    confirmations = set()

    def check(m):
        return (
            m.channel == ctx.channel and  # Must be in the same channel
            m.author in {ctx.author, target} and  # Must be one of the participants
            m.content.lower() in {"duel accept", "duel cancel"}  # Must type 'duel accept' or 'duel cancel'
        )

    try:
        while len(confirmations) < 2:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.content.lower() == "duel cancel":
                await ctx.reply(f"The duel was canceled by <@{msg.author.id}>.")
                ongoing_interactions.pop(ctx.author.id, None)
                ongoing_interactions.pop(target.id, None)
                return
            confirmations.add(msg.author.id)
    except asyncio.TimeoutError:
        await ctx.reply("Duel timed out. Both participants did not confirm in time.")
        ongoing_interactions.pop(ctx.author.id, None)
        ongoing_interactions.pop(target.id, None)
        return

    # Perform the duel
    winner, loser = (ctx.author, target) if random.random() < 0.5 else (target, ctx.author)
    winner_data = get_user(winner.id)
    loser_data = get_user(loser.id)

    # Update balances
    winner_data["balance"] += amount
    loser_data["balance"] -= amount
    save_users()

    # Remove users from ongoing interactions
    ongoing_interactions.pop(ctx.author.id, None)
    ongoing_interactions.pop(target.id, None)

    # Announce the result
    await ctx.reply(
        f"The duel is over! <@{winner.id}> wins ${amount} from <@{loser.id}>!\n"
        f"New balances:\n"
        f"- `{winner.name}`: ${winner_data['balance']}\n"
        f"- `{loser.name}`: ${loser_data['balance']}"
    )

@bot.command()
async def trade(ctx, target: discord.User, your_item_id: str, their_item_id: str):
    # Check if either user is already in another interaction
    if ctx.author.id in ongoing_interactions or target.id in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    
    trader = get_user(ctx.author.id)
    target_user = get_user(target.id)

    # Check if either user has passive mode enabled
    if trader.get("passive_mode", False):
        await ctx.reply("You cannot initiate a trade while in passive mode.")
        return

    if target_user.get("passive_mode", False):
        await ctx.reply(f"`{target.name}` is in passive mode and cannot be invited to trade.")
        return

    # Fetch user data
    user = get_user(ctx.author.id)
    target_user = get_user(target.id)

    # Check if both users have the required items
    if your_item_id not in user["inventory"] or user["inventory"][your_item_id] <= 0:
        await ctx.reply("You don't have that item to trade.")
        return

    if their_item_id not in target_user["inventory"] or target_user["inventory"][their_item_id] <= 0:
        await ctx.reply(f"{target.name} doesn't have that item to trade.")
        return

    # Add users to ongoing interactions (store channel ID)
    ongoing_interactions[ctx.author.id] = ctx.channel.id
    ongoing_interactions[target.id] = ctx.channel.id

    # Notify both users of the trade request
    await ctx.reply(
        f"<@{ctx.author.id}> wants to trade `{your_item_id}` for `{their_item_id}` with <@{target.id}>.\n"
        "Both parties, type `trade confirm` to accept or `trade cancel` to decline."
    )

    # Function to validate confirmations
    def check(m):
        return (
            m.channel == ctx.channel and  # Message must be in the same channel
            m.author in {ctx.author, target} and  # Message must be from either the command author or the target user
            m.content.lower() in {"trade confirm", "trade cancel"}  # Message must be 'trade confirm' or 'trade cancel'
        )

    confirmations = set()
    try:
        while len(confirmations) < 2:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.content.lower() == "trade cancel":
                await ctx.reply(f"The trade was canceled by <@{msg.author.id}>.")
                ongoing_interactions.pop(ctx.author.id, None)
                ongoing_interactions.pop(target.id, None)
                return
            confirmations.add(msg.author.id)
    except asyncio.TimeoutError:
        await ctx.reply("Trade timed out.")
        ongoing_interactions.pop(ctx.author.id, None)
        ongoing_interactions.pop(target.id, None)
        return

    # Perform the trade if both users confirm
    remove_item(ctx.author.id, your_item_id, 1)
    add_item(ctx.author.id, their_item_id, 1)
    remove_item(target.id, their_item_id, 1)
    add_item(target.id, your_item_id, 1)

    # Remove users from ongoing interactions
    ongoing_interactions.pop(ctx.author.id, None)
    ongoing_interactions.pop(target.id, None)

    # Notify success
    await ctx.reply("Trade successful!")

@bot.command()
async def spawn(ctx, item_id: str):
    # Check if the user is authorized
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("You do not have permission to use this command.")
        return

    # Validate the item ID
    if item_id not in all_items:
        await ctx.reply("Invalid item ID. Please check the item list and try again.")
        return

    item_name = all_items[item_id]["name"]

    # Special handling for Dragon and Leviathan
    if item_id == "9":
        await ctx.reply("A Dragon has appeared! Type `shoot the dragon` within 10 seconds to try and claim it!")

        def check(m):
            return (
                m.channel == ctx.channel and
                m.content.lower() == "shoot the dragon"
            )

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            add_item(msg.author.id, item_id, 1)
            await ctx.reply(f"<@{msg.author.id}> has successfully captured the Dragon! It has been added to their inventory.")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The Dragon has flown away.")
        return

    elif item_id == "17":
        await ctx.reply("A Leviathan has appeared! Type `shoot the leviathan` within 10 seconds to try and claim it!")

        def check(m):
            return (
                m.channel == ctx.channel and
                m.content.lower() == "shoot the leviathan"
            )

        try:
            msg = await bot.wait_for("message", check=check, timeout=10)
            add_item(msg.author.id, item_id, 1)
            await ctx.reply(f"<@{msg.author.id}> has successfully captured the Leviathan! It has been added to their inventory.")
        except asyncio.TimeoutError:
            await ctx.reply("Time's up! The Leviathan has swum away.")
        return
    # Generic item spawn
    await ctx.reply(f"{item_name} (ID: `{item_id}`) has been summoned from the divine heavens! Type `i wanna claim {item_id}` to claim the item.")

    def check(m):
        return (
            m.channel == ctx.channel and
            m.content.lower() == f"i wanna claim {item_id}" and
            m.author.id != ctx.author.id  # Ensure the summoner cannot claim their own item
        )

    try:
        msg = await bot.wait_for("message", check=check, timeout=10)
        add_item(msg.author.id, item_id, 1)
        await ctx.reply(f"<@{msg.author.id}> has claimed the item {item_name}! It has been added to their inventory.")
    except asyncio.TimeoutError:
        await ctx.reply(f"Time's up! The item {item_name} has disappeared back into the divine heavens.")

@bot.command()
async def whitelist(ctx, user: discord.User):
    # Check if the user is authorized
    if str(ctx.author.id) not in AUTHORIZED_USERS:
        await ctx.reply("You do not have permission to use this command.")
        return

    # Add the user to the authorized list
    user_id = str(user.id)
    if user_id in AUTHORIZED_USERS:
        await ctx.reply(f"<@{user.id}> is already an authorized user.")
        return

    AUTHORIZED_USERS.append(user_id)
    await ctx.reply(f"<@{user.id}> has been added to the list of authorized temporarily.")

auction_file = "auction_list.json"
if not os.path.exists(auction_file):
    with open(auction_file, "w") as f:
        json.dump([], f)

def load_auctions():
    with open(auction_file, "r") as f:
        return json.load(f)

def save_auctions(auctions):
    with open(auction_file, "w") as f:
        json.dump(auctions, f, indent=4)

def generate_market_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

auctions = load_auctions()

@bot.command()
async def auction(ctx, action=None, *args):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    user_id = str(ctx.author.id)

    if action is None:
        await ctx.reply("Available commands: \n"
                        "- `j!auction`: Show this help menu.\n"
                        "- **`j!auction show <page>`: View auction listings.**\n"
                        "- `j!auction sell <item id> <price>`: Start an auction.\n"
                        "- `j!auction buy <market code>`: Buy an item.\n"
                        "- `j!auction pending <page>`: View your auctions.\n"
                        "- `j!auction takedown <market code>`: Remove your auction.\n"
                        "- `j!auction view <item id> <page>`: View listings for an item.")
        return

    if action == "sell":
        if len(args) != 2 or not args[1].isdigit():
            await ctx.reply("Usage: `j!auction sell <item id> <price>`.")
            return

        item_id, price = args
        price = int(price)
        user_data = get_user(user_id)

        if item_id not in user_data["inventory"] or user_data["inventory"][item_id] <= 0:
            await ctx.reply("You don't have this item in your inventory.")
            return

        market_code = generate_market_code()

        ongoing_interactions[ctx.author.id] = ctx.channel.id
        await ctx.reply(f"Confirm selling item `{item_id}` for ${price} as auction `{market_code}`.\n"
                        "Type `auction sell confirm` to proceed or `auction sell cancel` to cancel.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in {"auction sell confirm", "auction sell cancel"}

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.content.lower() == "auction sell confirm":
                auctions.append({
                    "seller_id": user_id,
                    "item_id": item_id,
                    "price": price,
                    "market_code": market_code,
                    "buyer_id": None
                })
                save_auctions(auctions)
                remove_item(user_id, item_id, 1)
                await ctx.reply(f"Item `{item_id}` is now on auction with code `{market_code}`.")
            else:
                await ctx.reply("Auction canceled.")
        except asyncio.TimeoutError:
            await ctx.reply("Auction timed out. Please try again.")
        finally:
            ongoing_interactions.pop(ctx.author.id, None)

    elif action == "buy":
        if len(args) != 1:
            await ctx.reply("Usage: `j!auction buy <market code>`.")
            return

        market_code = args[0]
        auction = next((a for a in auctions if a["market_code"] == market_code), None)
        if not auction:
            await ctx.reply("Invalid market code.")
            return

        if auction["seller_id"] == user_id:
            await ctx.reply("You cannot buy your own auction.")
            return

        user_data = get_user(user_id)
        if user_data["balance"] < auction["price"]:
            await ctx.reply("You don't have enough money to buy this item.")
            return

        auction["buyer_id"] = user_id
        save_auctions(auctions)

        seller_data = get_user(auction["seller_id"])
        seller_data["balance"] += auction["price"]
        user_data["balance"] -= auction["price"]
        add_item(user_id, auction["item_id"], 1)

        await ctx.reply(f"You bought `{auction['item_id']}` for ${auction['price']}.")
        seller_user = await bot.fetch_user(int(auction["seller_id"]))
        await seller_user.send(f"Your auction `{market_code}` has been sold to <@{user_id}>.", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    elif action == "show":
        page = int(args[0]) if args and args[0].isdigit() else 1
        items_per_page = 5
        total_pages = (len(auctions) + items_per_page - 1) // items_per_page

        if page < 1 or page > total_pages:
            await ctx.reply(f"There are no auctioned items.")
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        listings = auctions[start:end]

        if not listings:
            await ctx.reply("No auctions available on this page.")
            return

        auction_list = "\n".join([
            f"Market Code: `{a['market_code']}`, Item: `{a['item_id']}`, Price: ${a['price']}, Seller: <@{a['seller_id']}>"
            for a in listings if a["buyer_id"] is None
        ])
        await ctx.reply(f"**Auction Listings (Page {page}/{total_pages}):**\n{auction_list}", allowed_mentions=discord.AllowedMentions(everyone=False, users=False, roles=False))

    elif action == "pending":
        page = int(args[0]) if args and args[0].isdigit() else 1
        user_auctions = [a for a in auctions if a["seller_id"] == user_id and a["buyer_id"] is None]
        items_per_page = 5
        total_pages = (len(user_auctions) + items_per_page - 1) // items_per_page

        if page < 1 or page > total_pages:
            await ctx.reply(f"Invalid page. Choose a page between 1 and {total_pages}.")
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        listings = user_auctions[start:end]

        if not listings:
            await ctx.reply("You have no pending auctions on this page.")
            return

        auction_list = "\n".join([
            f"Market Code: `{a['market_code']}`, Item: `{a['item_id']}`, Price: ${a['price']}"
            for a in listings
        ])
        await ctx.reply(f"**Your Pending Auctions (Page {page}/{total_pages}):**\n{auction_list}")

    elif action == "takedown":
        if len(args) != 1:
            await ctx.reply("Usage: `j!auction takedown <market code>`.")
            return

        market_code = args[0]
        auction = next((a for a in auctions if a["market_code"] == market_code), None)

        if not auction:
            await ctx.reply("Invalid market code.")
            return

        if auction["seller_id"] != user_id:
            await ctx.reply("You can only take down your own auctions.")
            return

        if auction["buyer_id"] is not None:
            await ctx.reply("This auction has already been sold and cannot be taken down.")
            return

        ongoing_interactions[ctx.author.id] = ctx.channel.id
        await ctx.reply(f"Confirm takedown of auction `{market_code}`.\n"
                        "Type `auction takedown confirm` to proceed or `auction takedown cancel` to cancel.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in {"auction takedown confirm", "auction takedown cancel"}

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            if msg.content.lower() == "auction takedown confirm":
                auctions.remove(auction)
                save_auctions(auctions)
                add_item(user_id, auction["item_id"], 1)
                await ctx.reply(f"Auction `{market_code}` has been taken down and item returned to your inventory.")
            else:
                await ctx.reply("Takedown canceled.")
        except asyncio.TimeoutError:
            await ctx.reply("Takedown timed out. Please try again.")
        finally:
            ongoing_interactions.pop(ctx.author.id, None)

    elif action == "view":
        if len(args) < 1:
            await ctx.reply("Usage: `j!auction view <item id> <page>`.")
            return

        item_id = args[0]
        page = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
        item_auctions = [a for a in auctions if a["item_id"] == item_id and a["buyer_id"] is None]
        items_per_page = 5
        total_pages = (len(item_auctions) + items_per_page - 1) // items_per_page

        if page < 1 or page > total_pages:
            await ctx.reply(f"Invalid page. Choose a page between 1 and {total_pages}.")
            return

        start = (page - 1) * items_per_page
        end = start + items_per_page
        listings = item_auctions[start:end]

        if not listings:
            await ctx.reply("No listings available for this item on this page.")
            return

        auction_list = "\n".join([
            f"Market Code: `{a['market_code']}`, Price: ${a['price']}, Seller: <@{a['seller_id']}>"
            for a in listings
        ])
        await ctx.reply(f"**Listings for Item `{item_id}` (Page {page}/{total_pages}):**\n{auction_list}")

    else:
        await ctx.reply("Invalid auction action. Use `j!auction` to see the available commands.")

@bot.command(aliases=["passive"])
async def passivemode(ctx, mode: str):
    if ctx.author.id in ongoing_interactions or discord.User in ongoing_interactions:
        await ctx.reply("One of the participants has a pending action that they need to resolve")
        return
    user = get_user(ctx.author.id)

    if mode.lower() not in ["on", "off"]:
        await ctx.reply("Invalid usage. Use `j!passive <on/off>`.")
        return

    # Update the passive mode state
    user["passive_mode"] = mode.lower() == "on"
    save_users()

    state = "enabled" if user["passive_mode"] else "disabled"
    await ctx.reply(f"Passive mode has been {state}. You will {'not ' if user['passive_mode'] else ''}be invited to duels or trades.")

import random

# Add the crime command
@bot.command()
@commands.cooldown(1, 30, commands.BucketType.user)
async def crime(ctx):
    user = get_user(ctx.author.id)
    if str(ctx.author.id) in AUTHORIZED_USERS:
        ctx.command.reset_cooldown(ctx)  # Reset cooldown for this command
    if ctx.author.id in ongoing_interactions:
        await ctx.reply("You already have a pending interaction. Complete or cancel it first.")
        return

    # Define crime options
    crimes = [
        {
            "name": "Arson",
            "reward": (20, 30),
            "death_chance": 0.01,
            "success_chance": 0.50,
            "messages": {
                "success": "You set a building on fire, are you proud? You earned ${earnings}.",
                "fail": "The wind blows out the flames before it even started.",
                "death": "You ended up burning yourself, you are dead."
            }
        },
        {
            "name": "Shop-lifting",
            "reward": (10, 20),
            "death_chance": 0.007,
            "success_chance": 0.50,
            "messages": {
                "success": "You got away and stole a piece of grocery. You earned ${earnings}.",
                "fail": "You got caught, RUN.",
                "death": "You got caught and was beaten up to death by security."
            }
        },
        {
            "name": "Robbing",
            "reward": (25, 40),
            "death_chance": 0.014,
            "success_chance": 0.45,
            "messages": {
                "success": "You got away and stole ${earnings}.",
                "fail": "You got caught but you ran away.",
                "death": "You got caught and was beaten up to death."
            }
        },
        {
            "name": "Cyberbullying",
            "reward": (5, 15),
            "death_chance": 0.005,
            "success_chance": 0.55,
            "messages": {
                "success": "The kid sent you ${earnings} for you to stop. Hope that kid grows up richer than you.",
                "fail": "Discord mods banned you after seeing the potential threats, time to make a new account.",
                "death": "You laughed so hard that you choked to death."
            }
        },
        {
            "name": "Hacking",
            "reward": (20, 30),
            "death_chance": 0.01,
            "success_chance": 0.50,
            "messages": {
                "success": "You hacked into Jerry's system and stole ${earnings}, devs gonna have to patch this vulnerability.",
                "fail": "The firewall was too strong and you couldn't bypass it this time.",
                "death": "You hacked into Jerry's system but the FBI noticed your strange behaviour and arrested you, you were sentenced to death for a huge data breach that caused a loss of $1 billion."
            }
        },
        {
            "name": "Vandalism",
            "reward": (5, 15),
            "death_chance": 0.005,
            "success_chance": 0.55,
            "messages": {
                "success": "You wrote 'Jerry' on a wall and xVapure sent you ${earnings}. Thanks for the free promotion.",
                "fail": "You ran out of spray paint.",
                "death": "While painting, you fell from a 10-story building and died."
            }
        }
    ]

    # Select 3 random crimes
    selected_crimes = random.sample(crimes, 3)

    # Notify the user of the choices
    crime_list = "\n".join([f"- {crime['name']}" for crime in selected_crimes])
    await ctx.reply(f"Choose a crime to commit by typing its name or type 'crime cancel' to opt out:\n{crime_list}\n\nKeep in mind that you could die while committing a crime if you don't have a life-saver (id: 25) (resulting in a loss of a random item and 20% of your balance).")

    # Add user to ongoing interactions
    ongoing_interactions[ctx.author.id] = ctx.channel.id

    def check(m):
        return (
            m.author == ctx.author and
            m.channel == ctx.channel and
            (m.content.lower() in [crime['name'].lower() for crime in selected_crimes] or m.content.lower() == 'crime cancel')
        )

    try:
        # Wait for user response
        msg = await bot.wait_for("message", check=check, timeout=30)

        if msg.content.lower() == 'crime cancel':
            await ctx.reply("You decided not to commit any crime.")
        else:
            # Perform the selected crime
            selected_crime = next(crime for crime in selected_crimes if crime['name'].lower() == msg.content.lower())
            outcome = random.random()

            if outcome < selected_crime['death_chance']:
                # User dies
                if "25" in user["inventory"] and user["inventory"]["25"] > 0:
                    remove_item(ctx.author.id, "25", 1)
                    await ctx.reply("You nearly died, but a life-saver saved you!")
                else:
                    user["balance"] = int(user["balance"] * 0.8)
                    if user["inventory"]:
                        random_item = random.choice(list(user["inventory"].keys()))
                        remove_item(ctx.author.id, random_item, 1)
                    save_users()
                    await ctx.reply(selected_crime['messages']['death'])
            elif outcome < selected_crime['death_chance'] + selected_crime['success_chance']:
                # Successful crime
                earnings = random.randint(*selected_crime['reward'])
                user["balance"] += earnings
                save_users()
                await ctx.reply(selected_crime['messages']['success'].replace("{earnings}", f"{earnings}"))
            else:
                # Failed crime
                await ctx.reply(selected_crime['messages']['fail'])

    except asyncio.TimeoutError:
        await ctx.reply("You took too long to decide.")

    # Remove user from ongoing interactions
    ongoing_interactions.pop(ctx.author.id, None)

bot.run(DISCORD_BOT_TOKEN)
