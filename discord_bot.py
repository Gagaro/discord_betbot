import pickle
import random
import sys
import traceback
from os import getenv

from discord.ext import commands


class Bet(commands.Cog):
    DATA_FILE_PATH = 'data.bin'
    EMOJIES_KEY = '__EMOJIES'
    MAX_CHOICES = 20
    EMOJIES = [
        '🤪',
        '🙀',
        '😂',
        '😭',
        '😱',
        '🦄',
        '🦇',
        '🦂',
        '🦖',
        '🐙',
        '🦈',
        '🦦',
        '🐉',
        '🐀',
        '💀',
        '🎅',
        '🦔',
        '🦥',
        '🦝',
    ]

    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = {}
        self.current_bets = {}
        self._load_data()

    def _load_data(self):
        try:
            with open(self.DATA_FILE_PATH, 'br') as data_file:
                (
                    self.leaderboard,
                    self.current_bets
                ) = pickle.load(data_file)
        except FileNotFoundError:
            pass

    def _save_data(self):
        with open(self.DATA_FILE_PATH, 'bw') as data_file:
             pickle.dump((
                 self.leaderboard,
                 self.current_bets
             ), data_file)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        if user == bot.user:
            return
        if message.id not in self.current_bets:
            return
        if reaction.emoji not in self.current_bets[message.id][self.EMOJIES_KEY]:
            return
        if user.id in self.current_bets[message.id] and reaction.emoji != self.current_bets[message.id][user.id]:
            await message.remove_reaction(reaction.emoji, user)
            return
        self.current_bets[message.id][user.id] = reaction.emoji
        self._save_data()

    @commands.command()
    @commands.cooldown(1, 30)
    async def leaderboard(self, ctx):
        message = 'Leaderboard\n\tNom\tScore'
        for member_id, score in sorted(self.leaderboard.items(), key=lambda x: x[1], reverse=True):
            message += '\n\t{}\t{}'.format(self.bot.get_user(member_id).display_name, score)
        await ctx.send(message)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startbet(self, ctx, *args):
        if not args:
            await ctx.send("Met des choix putain :face_with_symbols_over_mouth:.\n!startbet un deux trois")
            return
        if len(args) > self.MAX_CHOICES:
            await ctx.send("Oups, max {} pour le moment.".format(self.MAX_CHOICES))
            return
        # Pick emojies randomly
        emojies = self.EMOJIES.copy()
        random.shuffle(emojies)
        emojies = emojies[:len(args)]
        # Send message
        message = 'Faites vos jeux :dollar: !\n'
        for emoji, choice in zip(emojies, args):
            message += '\n\t{} {}'.format(emoji, choice)
        message = await ctx.send(message)
        # Send reactions
        for emoji in emojies:
            await message.add_reaction(emoji)
        self.current_bets[message.id] = {
            self.EMOJIES_KEY: emojies,
        }
        self._save_data()

    @startbet.error
    async def startbet_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Non mais tu te prends pour qui ?')
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def endbet(self, ctx, winning_choice):
        # TODO add a way to choose the bet concerned
        message_id, bet = list(self.current_bets.items())[-1]
        await self.endbet_message(ctx, message_id, bet, winning_choice)

    async def endbet_message(self, ctx, message_id, bet, winning_choice):
        del self.current_bets[message_id]
        winners = []
        # Set message and points in leaderboard
        for member, choice in bet.items():
            if choice == winning_choice:
                winners.append(self.bot.get_user(member))
                self.leaderboard[member] = self.leaderboard.setdefault(member, 0) + 1
            else:
                self.leaderboard.setdefault(member, 0)

        if winners:
            if len(winners) == 1:
                await ctx.send(
                    'Un seul mec intelligent ici, bravo à {}'.format(winners[0].display_name)
                )
            else:
                await ctx.send(
                    'Bravo à {}'.format(', '.format((member.display_name for member in winners)))
                )
        else:
            await ctx.send("C'est vraiment un serveur de looser ici :face_with_hand_over_mouth: .")
        self._save_data()

    @endbet.error
    async def endbet_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Non mais tu te prends pour qui ?')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Tu peux pas finir le bet sans résultat :zany_face:.")
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


print("Starting...")
bot = commands.Bot(command_prefix='!')
bot.add_cog(Bet(bot))
bot.run(getenv('DISCORD_BOT_TOKEN'))
