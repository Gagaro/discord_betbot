import itertools
import pickle
from copy import copy
from os import getenv

from discord.ext import commands


class Bet(commands.Cog):
    DATA_FILE_PATH = 'data.bin'
    EMOJIES = [
        'zero',
        'one',
        'two',
        'three',
        'four',
        'five',
        'six',
        'seven',
        'height',
        'nine',
        'regional_indicator_a',
        'regional_indicator_b',
        'regional_indicator_c',
        'regional_indicator_d',
        'regional_indicator_e',
        'regional_indicator_f',
        'regional_indicator_g',
        'regional_indicator_h',
        'regional_indicator_i',
        'regional_indicator_j',
        'regional_indicator_k',
        'regional_indicator_l',
        'regional_indicator_m',
        'regional_indicator_n',
        'regional_indicator_o',
        'regional_indicator_p',
        'regional_indicator_q',
        'regional_indicator_r',
        'regional_indicator_s',
        'regional_indicator_t',
        'regional_indicator_u',
        'regional_indicator_v',
        'regional_indicator_w',
        'regional_indicator_x',
        'regional_indicator_y',
        'regional_indicator_z',
    ]

    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = {}
        self.current_bets_messages = []
        self._load_data()

    def _load_data(self):
        try:
            with open(self.DATA_FILE_PATH, 'br') as data_file:
                self.leaderboard, self.current_bets_messages = pickle.load(data_file)
        except FileNotFoundError:
            pass

    def _save_data(self):
        with open(self.DATA_FILE_PATH, 'bw') as data_file:
             pickle.dump((self.leaderboard, self.current_bets_messages), data_file)

    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")

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
        if len(args) > len(self.EMOJIES):
            await ctx.send("Oups, max {} pour le moment.".format(len(self.EMOJIES)))
            return
        message = 'Bet en cours !\n'
        for index, choice in enumerate(args):
            message += '\n\t:{}: {}'.format(self.EMOJIES[index], choice)
        message = await ctx.send(message)
        for i in range(len(args)):
            await message.add_reaction(self.EMOJIES[i])
        self.current_bets_messages.append(message)

    @startbet.error
    async def startbet_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Non mais tu te prends pour qui ?')

    async def endbet(self, ctx, winning_choice: int):
        message = 'Les paris étaient :'
        winners = []
        # Set message and points in leaderboard
        for choice, members in self.current_bet.items():
            members = [self.bot.get_user(member_id) for member_id in members]
            message += '\n\t[{}] {}'.format(
                choice, ', '.join((member.display_name for member in members))
            )
            if choice == winning_choice:
                winners = members
                for member in members:
                    self.leaderboard[member.id] = self.leaderboard.setdefault(member.id, 0) + 1
            else:
                for member in members:
                    self.leaderboard.setdefault(member.id, 0)
        await ctx.send(message)

        if winners:
            if len(winners) == 1:
                await ctx.send(
                    'Un seul mec intelligent ici, bravo à {}'.format(winners[0].display_name)
                )
            else:
                await ctx.send(
                    'Les gagnants sont {}'.format(', '.format((member.display_name for member in winners)))
                )
        else:
            await ctx.send("C'est vraiment un serveur de looser ici :face_with_hand_over_mouth: .")
        self.current_choices = []
        self.current_bet = {}
        self._save_data()


print("Starting...")
bot = commands.Bot(command_prefix='!')
bot.add_cog(Bet(bot))
bot.run(getenv('DISCORD_BOT_TOKEN'))
