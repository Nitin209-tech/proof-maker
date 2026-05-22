import discord
from discord import app_commands
import datetime, random, traceback, json, os, base64
from html2image import Html2Image

current_directory = os.path.abspath(os.path.dirname(__file__))

# ── Token: Railway env variable takes priority, fallback to config file ──
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DEFAULT_AVATAR = os.environ.get("DEFAULT_AVATAR", "https://archive.org/download/discordprofilepictures/discordred.png")

if not BOT_TOKEN:
    try:
        config = json.load(open("config/config.json"))
        BOT_TOKEN = config.get("bot_token", "")
        DEFAULT_AVATAR = config.get("default_avatar", DEFAULT_AVATAR)
    except Exception:
        pass

# ── html2image: use system Chromium on Linux (Railway), else auto-detect ──
chromium_path = "/run/current-system/sw/bin/chromium"
if not os.path.exists(chromium_path):
    chromium_path = "/usr/bin/chromium"
if not os.path.exists(chromium_path):
    chromium_path = "/usr/bin/chromium-browser"
if not os.path.exists(chromium_path):
    chromium_path = None   # let html2image auto-detect on Windows

hti_flags = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--default-background-color=ffffff",
]
if chromium_path:
    hti = Html2Image(browser_executable=chromium_path, custom_flags=hti_flags)
else:
    hti = Html2Image(custom_flags=["--default-background-color=ffffff"])

# ── Fonts (base64-encoded so they work anywhere) ──
def encode_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

font_b64        = encode_file(f"{current_directory}/assets/fonts/ggsans-regular.ttf")
fontmed_base64  = encode_file(f"{current_directory}/assets/fonts/ggsans-medium.ttf")

# ── Nitro preset images (base64-encoded so file:// paths are not needed) ──
nitro_classic_b64 = encode_file(f"{current_directory}/assets/nitro_presets/nitro_classic_preset.png")
nitro_promo_b64   = encode_file(f"{current_directory}/assets/nitro_presets/nitro_promo_preset.png")
nitro_boost_b64   = encode_file(f"{current_directory}/assets/nitro_presets/nitro_boost_preset.png")


class BoostPage:
    def __init__(self, nitro_type, authorname, authoravatar, authortext, receiveravatar, receivername, receivertext, requestmsg=None, show_request=False):
        self.actual_datetime = datetime.datetime.now()
        self.proof = ""

        self.nitro_type = nitro_type

        self.authorname = authorname
        self.authoravatar = authoravatar
        self.authortext = authortext
        
        self.sender_message_datetime = self.actual_datetime - datetime.timedelta(minutes=random.randint(10, 300))
        self.request_message_datetime = self.sender_message_datetime - datetime.timedelta(minutes=random.randint(2, 10))
        
        self.request_message_datetime_str = self.request_message_datetime.strftime('Today at %I:%M %p')
        self.sender_message_datetime_str = self.sender_message_datetime.strftime('Today at %I:%M %p')

        self.receivername = receivername
        self.receiveravatar = receiveravatar
        self.receivertext = receivertext
        self.receiver_message_datetime = self.actual_datetime + datetime.timedelta(minutes=random.randint(1, 120))
        self.receiver_message_datetime_str = self.receiver_message_datetime.strftime('Today at %I:%M %p')
        
        self.show_request = show_request
        self.requestmsg = requestmsg
        if self.show_request and not self.requestmsg:
            self.requestmsg = random.choice([
                "give it to me brother please give it, I did so many invites!",
                "bro plss give me nitro, I completed all the invites!",
                "please give me nitro brother, I invited so many people!",
                "can i get my nitro now? i completed all the invite requirements",
                "bro i invited all my friends, please give me the nitro proof now"
            ])
    
    def get_proof(self):
        if self.nitro_type == "classic":
            nitro_link = "https://discord.gift/"
            nitro_image = f"data:image/png;base64,{nitro_classic_b64}"
        elif self.nitro_type == "promo":
            nitro_link = "https://discord.com/billing/promotions/"
            nitro_image = f"data:image/png;base64,{nitro_promo_b64}"
        else:
            nitro_link = "https://discord.gift/"
            nitro_image = f"data:image/png;base64,{nitro_boost_b64}"

        request_html = ""
        if self.show_request:
            request_html = f"""
    <div style="display: flex; margin-bottom: 20px">
        <img src="{self.receiveravatar}" id="user_request_avatar" alt="author icon" width="40" height="40" style="border-radius: 50%; image-rendering: -webkit-optimize-contrast">
        <div>
            <p id="user_request_name" style="margin-top: 0; margin-left: 15px; font-size: 1rem; font-weight: 500; vertical-align: baseline; font-family: GGSansMedium; color: #fff">
                {self.receivername}
                <span id="user_request_datetime" style="font-size: 12px; color: #a3a6aa; margin-left: 5px; font-family: GGSansRegular">{self.request_message_datetime_str}</span>
            </p>
            <p id="user_request_text" style="margin-left: 15px; margin-top: 3px; color: #fff; font-family: GGSansRegular; font-size: 16px; white-space: pre-wrap;">{self.requestmsg}</p>
        </div>
    </div>
            """

        with open("assets/index.html", 'r') as boost_page:
            self.proof = boost_page.read() \
                .replace('GGSANSFONT', f"data:font/ttf;base64,{font_b64}") \
                .replace('GGSANSMEDIUMFONT', f"data:font/ttf;base64,{fontmed_base64}") \
                .replace('REQUESTBLOCK', request_html) \
                .replace('AUTHORNAME', self.authorname) \
                .replace('AUTHORAVATAR', self.authoravatar) \
                .replace('AUTHORDATETIME', self.sender_message_datetime_str) \
                .replace('AUTHORTEXT', self.authortext) \
                .replace('USERNAME', self.receivername) \
                .replace('USERAVATAR', self.receiveravatar) \
                .replace('USERDATETIME', self.receiver_message_datetime_str) \
                .replace('USERTEXT', self.receivertext) \
                .replace('NITROLINK', nitro_link) \
                .replace('NITROCODE', ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(16))) \
                .replace('NITROIMAGESRC', nitro_image)

        return self.proof

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tree.remove_command('help')

    async def setup_hook(self):
        await self.tree.sync()


intents = discord.Intents.all()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/proof"))
    print(f"[CONNEXION] {client.user} ({client.user.id})")


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith(client.user.mention):
        await message.channel.send(f"{message.author.mention}, do /proof to get a Proof!")


class NitroProofCustom(discord.ui.Modal):
    nitrotype = discord.ui.TextInput(
        label='Type of Nitro code:',
        style=discord.TextStyle.short,
        placeholder='Example: classic or boost or promo',
        required=True,
        max_length=7,
    )

    authortext = discord.ui.TextInput(
        label='Text presumed to be sent by you:',
        placeholder='Example: Congratulation! Here is ur code ',
        style=discord.TextStyle.long,
        required=False,
    )

    receivername = discord.ui.TextInput(
        label='Name of the receiver:',
        style=discord.TextStyle.short,
        placeholder='Example: Astraa',
        required=True,
        max_length=32,
    )

    receiveravatar = discord.ui.TextInput(
        label='Avatar link of the receiver:',
        style=discord.TextStyle.short,
        placeholder='Example: https://image.com/XXXXXXX.png',
        required=False,
    )

    receivertext = discord.ui.TextInput(
        label='Text presumed to be sent by the receiver:',
        style=discord.TextStyle.paragraph,
        placeholder='Example: OMG thx it\'s a real giveaway!',
        required=True,
    )

    def __init__(self, requestmsg: str = None, show_request: bool = True):
        super().__init__(title='Fake Nitro Proof System')
        self.requestmsg = requestmsg
        self.show_request = show_request

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            self.receiveravatar_value = self.receiveravatar.value if self.receiveravatar.value else DEFAULT_AVATAR
            author_avatar = interaction.user.display_avatar.url if interaction.user.avatar else DEFAULT_AVATAR
            proof = BoostPage(
                self.nitrotype.value, 
                interaction.user.display_name, 
                author_avatar, 
                self.authortext.value, 
                self.receiveravatar_value, 
                self.receivername.value, 
                self.receivertext.value,
                requestmsg=self.requestmsg,
                show_request=self.show_request
            ).get_proof()
            
            height = random.randint(530, 560) if self.show_request else random.randint(450, 470)
            hti.screenshot(html_str=proof, size=(random.randint(730, 1100), height), save_as='proof.png')
            
            await interaction.user.send(file=discord.File('proof.png'))
            await interaction.followup.send(f"Proof generated! Check your DMs.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'Oops! Proof cannot be generated due to the following error: {e}', ephemeral=True)
            return

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong. Please try again.', ephemeral=True)
        traceback.print_tb(error.__traceback__)


class NitroProofId(discord.ui.Modal):
    nitrotype = discord.ui.TextInput(
        label='Type of Nitro code:',
        style=discord.TextStyle.short,
        placeholder='Example: classic or boost or promo',
        required=True,
        max_length=7,
    )

    authortext = discord.ui.TextInput(
        label='Text presumed to be sent by you:',
        placeholder='Example: Congratulation! Here is ur code ',
        style=discord.TextStyle.long,
        required=False,
    )

    receiverid = discord.ui.TextInput(
        label='ID of the receiver:',
        style=discord.TextStyle.short,
        placeholder='Example: 464457105521508354',
        required=True,
        max_length=25,
    )

    receivertext = discord.ui.TextInput(
        label='Text presumed to be sent by the receiver:',
        style=discord.TextStyle.paragraph,
        placeholder='Example: OMG thx it\'s a real giveaway!',
        required=True,
    )

    def __init__(self, requestmsg: str = None, show_request: bool = True):
        super().__init__(title='Fake Nitro Proof System')
        self.requestmsg = requestmsg
        self.show_request = show_request

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            self.user = await client.fetch_user(int(self.receiverid.value))
            self.author_avatar = interaction.user.display_avatar.url if interaction.user.avatar else DEFAULT_AVATAR
            self.receiver_avatar = self.user.display_avatar.url if self.user.avatar else DEFAULT_AVATAR
            proof = BoostPage(
                self.nitrotype.value, 
                interaction.user.name, 
                self.author_avatar, 
                self.authortext.value, 
                self.receiver_avatar, 
                self.user.name, 
                self.receivertext.value,
                requestmsg=self.requestmsg,
                show_request=self.show_request
            ).get_proof()
            
            height = random.randint(530, 560) if self.show_request else random.randint(450, 470)
            hti.screenshot(html_str=proof, size=(random.randint(730, 1100), height), save_as='proof.png')
            
            await interaction.user.send(file=discord.File('proof.png'))
            await interaction.followup.send(f"Proof generated! Check your DMs.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f'Oops! Proof cannot be generated due to the following error: {e}', ephemeral=True)
            return
        
    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message(f'Oops! Something went wrong. Please try again.', ephemeral=True)
        traceback.print_tb(error.__traceback__)


@client.tree.command(description='Generate a Giveaway Proof.')
@app_commands.describe(
    receiverinfo='Find the name/avatar of an account with an ID or Cutomize it',
    requestmsg='Optional: Custom message from the receiver requesting the Nitro (e.g. "please give nitro")',
    show_request='Whether to include a request message at the top of the proof'
)
@app_commands.choices(receiverinfo=[
    app_commands.Choice(name='Receiver ID', value='id'),
    app_commands.Choice(name='Custom Receiver', value='custom')
])
async def proof(interaction: discord.Interaction, receiverinfo: str, requestmsg: str = None, show_request: bool = True):
    if receiverinfo == 'custom':
        await interaction.response.send_modal(NitroProofCustom(requestmsg=requestmsg, show_request=show_request))
    elif receiverinfo == 'id':
        await interaction.response.send_modal(NitroProofId(requestmsg=requestmsg, show_request=show_request))


if __name__ == '__main__':
    client.run(BOT_TOKEN)
