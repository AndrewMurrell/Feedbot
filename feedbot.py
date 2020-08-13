#!/usr/bin/python

### ---- Credit ----

# Feedbot written by Andrew Murrell <'ImFromNASA@gmail.com'> ['@NASA#1968'] on Discord

### ---- License ----

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Afferoo General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/agpl-3.0.en.html>.

### ---- Setup ----
# python3 -m pip install -U discord.py
# echo "export FEEDBOT_TOKEN='<YOUR DISCORD API KEY HERE>'; python 'feedbot.py'" > run.sh
# chmod +x run.sh

### ---- Running ----
# ./run.sh

### ---- Notes ----
# This program was designed for the Discord of Many Things to function
# as a tool for enabling users to send suggestions to the mods.

### ---- Design Notes ----
# The Feedbot class contains:
#   - update_config(key, value) -> saves the changed bot config
#   - send_suggestion(author, message) [ASYNC] -> sends a suggestion to the configured output channel
#   - on_message(message) [ASYNC] -> handles incoming message traffic from all channels Feedbot can see (including direct messages)
#   - on_ready() [ASYNC] -> initializes bot from previous stored channel values

import discord
import configparser
import os

help_message = "Thank you for requesting suggestion help!\n To send a suggestion, simply send a message in the designated suggestion input channel on your desired server. To send an anonymous suggestion, simply reply to me here.\n\n**Other Commands Below:**\n - **setprefix** *<character prefix>*\n\tEx: $setprefix @\n - **setinput** *<channel>*\n\t EX: $setinput #suggestion-box\n - **setoutput** *<channel>*\n\t Ex: $setoutput #suggestion-log\n - **help**\n\t Receive this message.\n\n "

class Feedbot(discord.Client):

    # Default prefix is '$', this can be changed with $setprefix <character>
    prefix = '$'

    # Default empty channel is 0, set with $setinput and $setoutput
    input_channel = 0
    output_channel = 0

    # Saves the changed bot config
    def update_config(self, key, value):
        config = configparser.ConfigParser()
        config.read('FEEDBOT.INI')
        config.set('FEEDBOT', key, value)
        with open('./FEEDBOT.INI', 'w') as feedbot:
            config.write(feedbot)

    # Sends a suggestion to the configured output channel.
    # Handles both Direct Messages (anonymous) and those from the configured input channel.
    async def send_suggestion(self, author, message):

        # Build the Embed to display in the output_channel from the user's message
        auth = "**Suggestion Message** sent by "
        auth += "Anonymous" if author == "" else author.display_name + " (@" + str(author) + ")"
        desc = "Message received from "
        desc += "Private Message" if author == "" else "#" + message.channel.name
        colr = 0xc0c0c0 if author == "" else 0x00ff00

        suggestion = discord.Embed(title=auth, description=desc, color=colr)

        if message.content != "":
            suggestion.add_field(name="Suggestion", value=message.content)
        if message.attachments != []:
            attach_message = "User included " + str(len(message.attachments)) + " attachment(s):\n"
            for a in message.attachments:
                attach_message += a.filename + " " + a.proxy_url + "\n"
            suggestion.add_field(name="Attachements", value=attach_message)
        if author != "":
            suggestion.set_thumbnail(url=author.avatar_url)

        # Attempt to send message to the output channel, DM the user in the case of a failure
        try:
            await client.get_channel(self.output_channel).send(embed=suggestion)
            if author != "":
                await message.delete()
            else:
                await message.add_reaction(u"\u2705")
                await message.channel.send("Thank you for your anonymous suggestion!")
        # Sending Failed: 400 - Forbidden
        except discord.errors.Forbidden as e:
            await message.channel.send("**Permissions Error** I'm sorry, I can't do that. I don't have permission. I require the \"Manage Messages\" permission here and the the \"Send Messages\" permission in the output channel.")
        # Sending Failed: 400 - HTTPException
        except discord.errors.HTTPException as e:
            msg = message.content if message.content != "" else ""
            for a in message.attachments:
                msg += a.proxy_url + "\n"
            await message.author.send(msg)
            if author != "":
                await message.delete()
            else:
                await message.add_reaction(u"\U0001F6AB")
            await message.channel.send("Suggestions must remain below 1024 characters.")

    # Handle incoming message traffic from all channels Feedbot can see (including direct messages)
    async def on_message(self, message):
        if message.author == client.user:
            return

        msg = message.content.lower()

        if msg.startswith(self.prefix + "set"):
            if message.guild != None:
                if message.author.guild_permissions.administrator == False:
                    await message.channel.send("**Permissions Error** I'm sorry, only an administrator can do that.")
                    await message.add_reaction(u"\U0001F6AB")
                    return
            else:
                await message.channel.send("**Permissions Error** I'm sorry, only an administrator can do this, and must do so from within the desired server.")
                await message.add_reaction(u"\U0001F6AB")
                return
        if msg.startswith(self.prefix + "setprefix"):
            self.prefix = message.content.split(' ', 2)[1]
            self.update_config('PREFIX', self.prefix)
            await message.add_reaction(u"\u2705")
            return
        if msg.startswith(self.prefix + "setinput"):
            self.input_channel = int(message.content.split(' ', 2)[1][2:-1])
            self.update_config('INPUT_CHANNEL', str(self.input_channel))
            await message.add_reaction(u"\u2705")
            return
        if msg.startswith(self.prefix + "setoutput"):
            self.output_channel = int(message.content.split(' ', 2)[1][2:-1])
            self.update_config('OUTPUT_CHANNEL', str(self.output_channel))
            await message.add_reaction(u"\u2705")
            return
        if msg.startswith(self.prefix + "help"):
            await message.author.send(help_message)
            await message.add_reaction(u"\u2705")
            return
        if (self.input_channel == 0 or self.output_channel == 0):
            return
        if (message.guild == None):
            await self.send_suggestion("", message)
            return
        if (message.channel.id == self.input_channel):
            await self.send_suggestion(message.author, message)
            return

    # Initialize the bot from the previous stored channel values (from 'FEEDBOT.ini')
    async def on_ready(self):
        print('I am')
        print(self.user.name)
        print(self.user.id)
        print('------')

        # Check for existing config file. If it doesn't exist, create it with the defaults.
        config = configparser.ConfigParser()
        if config.read('FEEDBOT.INI') == []:
            print("no ini")
            config.add_section('FEEDBOT')
            config.set('FEEDBOT', 'PREFIX', '$')
            config.set('FEEDBOT', 'INPUT_CHANNEL', '0')
            config.set('FEEDBOT', 'OUTPUT_CHANNEL', '0')
            with open('./FEEDBOT.INI', 'w') as feedbot:
                config.write(feedbot)
        # If the config does exist, then populate from its values.
        else:
            print("ini exists")
            self.prefix = config.get('FEEDBOT', 'PREFIX')
            self.input_channel = int(config.get('FEEDBOT', 'INPUT_CHANNEL'))
            self.output_channel = int(config.get('FEEDBOT', 'OUTPUT_CHANNEL'))
        print ("defaults: " + self.prefix + ", " + str(self.input_channel) + ", " + str(self.output_channel))
        print ('------')

client = Feedbot()
client.run(os.environ['FEEDBOT_TOKEN'])
