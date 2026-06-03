import discord
from discord.ext import commands
import os
import subprocess
import tempfile
from pathlib import Path
import shutil
import time

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Configuration
VALID_EXTENSIONS = ['.lua', '.txt']
OBFUSCATOR_PATH = "./unveilr/main.luau"
TEMP_DIR = "./temp_obfuscate"

# REMOVE DEFAULT HELP COMMAND TO ALLOW YOUR CUSTOM !help
bot.remove_command('help')

# Create temp directory
os.makedirs(TEMP_DIR, exist_ok=True)

def is_lua_file(content):
    """Check if content looks like Lua/Luau code"""
    content_lower = content.lower()
    
    lua_keywords = [
        'function', 'local', 'return', 'if', 'then', 'end', 'for', 'while',
        'do', 'elseif', 'else', 'require', 'script', 'game', 'workspace',
        'class', 'export', 'type', 'interface'
    ]
    
    keyword_count = sum(1 for keyword in lua_keywords if keyword in content_lower)
    
    if keyword_count >= 2:
        return True
    
    if any(pattern in content for pattern in ['function', 'local', '--[[', '--']):
        return True
    
    return False

def detect_file_type(filename):
    """Detect if file is .lua or .txt"""
    ext = Path(filename).suffix.lower()
    if ext not in VALID_EXTENSIONS:
        return None
    return ext

async def obfuscate_code(lua_content):
    """Obfuscate Lua code"""
    try:
        input_file = os.path.join(TEMP_DIR, f"input_{os.urandom(8).hex()}.lua")
        output_file = os.path.join(TEMP_DIR, f"output_{os.urandom(8).hex()}.lua")
        
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(lua_content)
        
        # Try to run with lua
        cmd = ["lua", OBFUSCATOR_PATH, "--input", input_file, "--output", output_file, "--preset", "Strong"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None, f"Obfuscation error: {result.stderr}"
        
        if os.path.exists(output_file):
            with open(output_file, 'r', encoding='utf-8') as f:
                obfuscated = f.read()
            
            os.remove(input_file)
            os.remove(output_file)
            
            return obfuscated, None
        else:
            return None, "Output file not generated"
            
    except subprocess.TimeoutExpired:
        return None, "Obfuscation timed out (30s limit)"
    except Exception as e:
        return None, f"Error: {str(e)}"

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is ready in {len(bot.guilds)} guild(s)')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="!help"))

@bot.command(name='help')
async def help_command(ctx):
    """Display help information about the bot"""
    embed = discord.Embed(
        title="🤖 Lua Obfuscator Bot - Help",
        description="A Discord bot that obfuscates Lua/Luau code with the Unveilr obfuscator",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📝 **!obfuscate** - Obfuscate Lua Code",
        value="Obfuscates your Lua/Luau code with strong preset encryption\n"
              "**Usage:** `!obfuscate` (then attach a `.lua` or `.txt` file)\n"
              "**Supported Files:** `.lua`, `.txt`\n"
              "**Max File Size:** 10MB\n"
              "**Requirements:** Code must contain Lua keywords (function, local, etc.)",
        inline=False
    )
    
    embed.add_field(
        name="📊 **!status** - Bot Status",
        value="Shows bot latency/ping and connection status\n"
              "**Usage:** `!status`",
        inline=False
    )
    
    embed.add_field(
        name="❓ **!help** - Show This Message",
        value="Shows all available commands and how to use them\n"
              "**Usage:** `!help`",
        inline=False
    )
    
    embed.add_field(
        name="🔍 **How to Use:**",
        value="1️⃣ Type `!obfuscate`\n"
              "2️⃣ Attach a `.lua` or `.txt` file with Lua code\n"
              "3️⃣ Bot will validate and obfuscate the code\n"
              "4️⃣ Download the obfuscated file",
        inline=False
    )
    
    embed.add_field(
        name="⚠️ **Requirements for Files:**",
        value="• File must be valid Lua/Luau code\n"
              "• Must contain at least 2 Lua keywords\n"
              "• UTF-8 encoding required\n"
              "• Max 10MB file size",
        inline=False
    )
    
    embed.add_field(
        name="✨ **Lua Keywords Detected:**",
        value="function, local, return, if, then, end, for, while, do, "
              "elseif, else, require, script, game, workspace, class, export, type, interface",
        inline=False
    )
    
    embed.add_field(
        name="📁 **Output File:**",
        value="Obfuscated file is returned as `obfuscated_[filename].lua`",
        inline=False
    )
    
    embed.set_footer(text="Made with ❤️ | Powered by Unveilr Obfuscator")
    embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
    
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status(ctx):
    """Show bot status and latency"""
    
    # Get latency
    latency = round(bot.latency * 1000)
    
    # Create status embed
    embed = discord.Embed(
        title="🟢 Bot Status",
        description="Lua Obfuscator Bot is Online",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="📡 **Ping/Latency**",
        value=f"`{latency}ms`",
        inline=True
    )
    
    embed.add_field(
        name="🌐 **Servers**",
        value=f"`{len(bot.guilds)} guild(s)`",
        inline=True
    )
    
    embed.add_field(
        name="👥 **Total Users**",
        value=f"`{sum(guild.member_count for guild in bot.guilds)} user(s)`",
        inline=True
    )
    
    embed.add_field(
        name="💬 **Prefix**",
        value="`!`",
        inline=True
    )
    
    embed.add_field(
        name="⌚ **Uptime**",
        value=f"Since: <t:{int((bot.user.id >> 22) / 1000 + 1420070400000 / 1000)}:R>",
        inline=True
    )
    
    # Connection status
    if bot.user.status == discord.Status.online:
        status_text = "🟢 **Online**"
    elif bot.user.status == discord.Status.idle:
        status_text = "🟡 **Idle**"
    else:
        status_text = "🔴 **Offline**"
    
    embed.add_field(
        name="🔌 **Connection Status**",
        value=status_text,
        inline=True
    )
    
    embed.add_field(
        name="✅ **Available Commands**",
        value="`!obfuscate` `!status` `!help`",
        inline=False
    )
    
    # Latency indicator
    if latency < 100:
        indicator = "🟢 Excellent"
    elif latency < 200:
        indicator = "🟡 Good"
    elif latency < 300:
        indicator = "🟠 Fair"
    else:
        indicator = "🔴 Poor"
    
    embed.add_field(
        name="📊 **Connection Quality**",
        value=indicator,
        inline=False
    )
    
    embed.set_footer(text=f"Bot version: 1.0 | Last updated: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    await ctx.send(embed=embed)

@bot.command(name='obfuscate')
async def obfuscate(ctx):
    """Obfuscate Lua code from attached file"""
    
    if not ctx.message.attachments:
        embed = discord.Embed(
            title="❌ No File Attached",
            description="Please attach a `.lua` or `.txt` file containing Lua code\n\n"
                        "Use `!help` for more information",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    attachment = ctx.message.attachments[0]
    
    file_type = detect_file_type(attachment.filename)
    if not file_type:
        embed = discord.Embed(
            title="❌ Invalid File Type",
            description=f"Please upload a `.lua` or `.txt` file\n"
                        f"Provided: `{Path(attachment.filename).suffix}`\n\n"
                        f"Use `!help` for more information",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    if attachment.size > 10 * 1024 * 1024:
        embed = discord.Embed(
            title="❌ File Too Large",
            description="File size exceeds 10MB limit",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    
    async with ctx.typing():
        try:
            file_content = await attachment.read()
            lua_content = file_content.decode('utf-8')
            
            if not is_lua_file(lua_content):
                embed = discord.Embed(
                    title="❌ Not Valid Lua Code",
                    description="The file doesn't appear to contain valid Lua/Luau code\n\n"
                                "Required: At least 2 Lua keywords (function, local, etc.)\n"
                                "Use `!help` for valid keywords",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            obfuscated, error = await obfuscate_code(lua_content)
            
            if error:
                embed = discord.Embed(
                    title="❌ Obfuscation Failed",
                    description=error,
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            output_filename = f"obfuscated_{Path(attachment.filename).stem}.lua"
            temp_output = os.path.join(TEMP_DIR, output_filename)
            
            with open(temp_output, 'w', encoding='utf-8') as f:
                f.write(obfuscated)
            
            # Calculate compression ratio
            original_size = len(lua_content)
            obfuscated_size = len(obfuscated)
            ratio = ((original_size - obfuscated_size) / original_size * 100) if original_size > 0 else 0
            
            embed = discord.Embed(
                title="✅ Obfuscation Complete",
                description="Your Lua code has been successfully obfuscated!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📊 File Statistics",
                value=f"Original: `{original_size:,}` bytes\n"
                      f"Obfuscated: `{obfuscated_size:,}` bytes\n"
                      f"Change: `{ratio:.1f}%`",
                inline=False
            )
            
            embed.add_field(
                name="📁 Output File",
                value=f"`{output_filename}`",
                inline=False
            )
            
            embed.set_footer(text="Preset: Strong | Obfuscator: Unveilr")
            
            try:
                with open(temp_output, 'rb') as f:
                    await ctx.send(embed=embed, file=discord.File(f, filename=output_filename))
            finally:
                if os.path.exists(temp_output):
                    os.remove(temp_output)
        
        except UnicodeDecodeError:
            embed = discord.Embed(
                title="❌ File Encoding Error",
                description="Could not decode file. Make sure it's UTF-8 encoded",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="❌ Command Not Found",
            description=f"The command `{ctx.message.content}` does not exist\n\n"
                        f"Use `!help` to see available commands",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Get token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')

if __name__ == "__main__":
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN environment variable not set!")
    else:
        bot.run(TOKEN)
