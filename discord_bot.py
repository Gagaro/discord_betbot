import itertools
import pickle
from copy import copy
from os import getenv

from discord.ext import commands


class Bet(commands.Cog):
    DATA_FILE_PATH = 'data.bin'

    def __init__(self, bot):
        self.bot = bot
        self.leaderboard = {}
        self.current_choices = []
        self.current_bet = {}
        self._load_data()

    def _load_data(self):
        try:
            with open(self.DATA_FILE_PATH, 'br') as data_file:
                self.leaderboard = pickle.load(data_file)
        except FileNotFoundError:
            pass

    def _save_data(self):
        with open(self.DATA_FILE_PATH, 'bw') as data_file:
             pickle.dump(self.leaderboard, data_file)

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
        if self.current_choices:
            await ctx.send("Il y a déjà un bet en cours.\n!endbet")
            return
        if not args:
            await ctx.send("Met des choix putain :face_with_symbols_over_mouth:.\n!startbet un deux trois")
            return
        self.current_choices = copy(args)
        self.current_bet = {index + 1: [] for index in range(len(self.current_choices))}
        message = 'Bet en cours !\n'
        for id, choice in enumerate(args, start=1):
            message += '\n\t[{}] {}'.format(id, choice)
        await ctx.send(message)

    @startbet.error
    async def startbet_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Non mais tu te prends pour qui ?')

    @commands.command()
    async def bet(self, ctx, choice: int):
        if not self.current_choices:
            await ctx.send("Il y a pas de bet en cours :person_facepalming: .")
            return
        if ctx.author.id in itertools.chain(*self.current_bet.values()):
            await ctx.send("T'as déjà voté essaye pas de gruger :middle_finger:.")
            return
        if choice > len(self.current_choices) or choice <= 0:
            await ctx.send("Tu sais pas compter en fait :nerd: ?")
            return
        self.current_bet[choice].append(ctx.author.id)

    @bet.error
    async def bet_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Ha ha très drole :clown:.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def endbet(self, ctx, winning_choice: int):
        if not self.current_choices:
            await ctx.send("Il y a pas de bet en cours :person_facepalming: .")
            return
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

    @endbet.error
    async def endbet_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('Non mais tu te prends pour qui ?')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Tu peux pas finir le bet sans résultat :zany_face:.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Ha ha très drole :clown:.")


bot = commands.Bot(command_prefix='!')
bot.add_cog(Bet(bot))
bot.run(getenv('DISCORD_BOT_TOKEN'))
