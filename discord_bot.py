import pickle
import random
import sys
import traceback
from os import getenv

from discord.ext import commands


class Player:

    def __init__(self, member_id):
        self.member_id = member_id
        self.participation_count = 0
        self.win_count = 0

    def add_participation(self, win=False):
        self.participation_count += 1
        if win:
            self.win_count += 1

    def get_member(self, bot):
        return bot.get_user(self.member_id)


class Bet(commands.Cog):
    DATA_FILE_PATH = 'data.bin'
    CHOICES_KEY = '__CHOICES'
    VOTES_KEY = '__VOTES'
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
        self.players = {}
        self.current_bets = {}
        self._load_data()

    def _load_data(self):
        try:
            with open(self.DATA_FILE_PATH, 'br') as data_file:
                (
                    self.players,
                    self.current_bets
                ) = pickle.load(data_file)
        except FileNotFoundError:
            pass

    def _save_data(self):
        with open(self.DATA_FILE_PATH, 'bw') as data_file:
             pickle.dump((
                 self.players,
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
        if reaction.emoji not in self.current_bets[message.id][self.CHOICES_KEY].keys():
            await message.remove_reaction(reaction.emoji, user)
            return
        if user.id in self.current_bets[message.id][self.VOTES_KEY]:
            if reaction.emoji != self.current_bets[message.id][self.VOTES_KEY][user.id]:
                await message.remove_reaction(reaction.emoji, user)
                return
        self.current_bets[message.id][self.VOTES_KEY][user.id] = reaction.emoji
        self._save_data()

    @commands.command()
    @commands.cooldown(1, 10)
    async def leaderboard(self, ctx):
        message = 'Leaderboard\n===========\nNom              Score\n'
        for player in sorted(self.players.values(), key=lambda x: x.win_count, reverse=True):
            member = player.get_member(self.bot)
            if member is not None:
                message += '\n{:16}{} / {}'.format(member.display_name, player.win_count, player.participation_count)
        await ctx.send(message)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def clear_leaderboard(self, ctx):
        self.players = {}
        self._save_data()
        await ctx.send("RIP leaderboard :ghost:")

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
        choices = dict(zip(emojies, args))
        for emoji, choice in choices.items():
            message += '\n\t{} {}'.format(emoji, choice)
        message = await ctx.send(message)
        # Send reactions
        for emoji in emojies:
            await message.add_reaction(emoji)
        self.current_bets[message.id] = {
            self.CHOICES_KEY: choices,
            self.VOTES_KEY: {},
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
        if not self.current_bets:
            return
        # TODO add a way to choose the bet concerned
        message_id, bet = list(self.current_bets.items())[-1]
        await self.endbet_message(ctx, message_id, bet, winning_choice)

    async def endbet_message(self, ctx, message_id, bet, winning_choice):
        del self.current_bets[message_id]
        winners = []
        # Set message and points in leaderboard
        for member_id, choice in bet[self.VOTES_KEY].items():
            # Initialize player if it is his first participation
            if member_id not in self.players:
                self.players[member_id] = Player(member_id=member_id)
            # Winning choice can be the emoji or the value
            if choice == winning_choice or bet[self.CHOICES_KEY][choice].lower() == winning_choice.lower():
                self.players[member_id].add_participation(win=True)
                winners.append(self.players[member_id].get_member(self.bot))
            else:
                self.players[member_id].add_participation(win=False)

        if winners:
            if len(winners) == 1:
                await ctx.send(
                    'Un seul mec intelligent ici, bravo à {}'.format(winners[0].mention)
                )
            else:
                await ctx.send(
                    'Bravo à {}'.format(', '.join([member.mention for member in winners]))
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
