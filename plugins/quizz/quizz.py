"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import random
import time
from typing import Optional

import discord
from discord.ext import commands, tasks
from utils import Gunibot, MyContext

from .QuiPyQuizz import QuiPyQuizz


def clean_question(question: str):
    junk_to_remove = ["<p>", "</p>"]
    for junk in junk_to_remove:
        question = question.replace(junk, "")
    return question


def clean_answer(answer: str):
    answer = answer.replace("<p>", "\n")
    answer = answer.replace("</p>", "")
    return answer


class REACTIONS:
    ANSWER_TRUE = "✅"
    ANSWER_FALSE = "❎"
    ANSWER_SEPARATOR = "⬛"
    ANSWER_LEAVE = "⏹️"
    answers_reactions = (ANSWER_TRUE, ANSWER_FALSE, ANSWER_SEPARATOR, ANSWER_LEAVE)
    START_QUIZ = "🆗"
    STOP_QUIZ = "❌"
    JOIN_QUIZ = "✅"
    FORWARD_QUESTION = "⏭"
    PREVIOUS_QUESTION = "⬅️"
    NEXT_QUESTION = "➡️"
    all_reactions = (
        ANSWER_TRUE,
        ANSWER_FALSE,
        ANSWER_SEPARATOR,
        ANSWER_LEAVE,
        START_QUIZ,
        STOP_QUIZ,
        JOIN_QUIZ,
        FORWARD_QUESTION,
        PREVIOUS_QUESTION,
        NEXT_QUESTION,
    )


def sort_dict(leaders: dict) -> list[tuple]:
    """Sort a dict by each value, returning a list of (key, value) couples
    Note that it will sort in lexicographical order
    For mathematical way, change it to float"""
    return sorted(leaders.items(), key=lambda kv: (kv[1], kv[0]))


class Quizz(commands.Cog):
    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "quizz"
        # Voir l'exemple de dict dans _quizz_start(ctx, quizz_id)
        self.parties = {"0": None}
        # Utile pour réduire le nombre de requêtes envoyées, cf:
        # on_aw_reaction_add/remove
        self.quick_quizz_channels = []
        self.quick_quizz_messages = []  # Same
        self.check_if_active.start()  # Démarrage du check des quizz inactifs
        self.QPQ = QuiPyQuizz()

    def update_timestamp(self, party_id):
        self.parties[party_id]["timestamp"] = time.time()

    # Vu que c'est gros et qu'il faut le foutre partout j'en ai fait une
    # fonction
    def ez_set_author(self, embed: discord.Embed, party_id):
        # Récupère l'id du quizz
        quizz_id = self.parties[party_id]["quizz"]["id"]
        embed.set_author(
            name=self.QPQ.get_name(quizz_id),
            url=self.QPQ.get_url(quizz_id),
            icon_url="https://scontent.fcdg1-1.fna.fbcdn.net/v/t1.6435-1/p148x148/48416529_2354370714793494_5893141918379933696_n.png?_nc_cat=110&ccb=1-3&_nc_sid=1eb0c7&_nc_ohc=AI2a2_Vn0c4AX9pPIK8&_nc_ht=scontent.fcdg1-1.fna&tp=30&oh=f8c88dae60c23d52fe81b8264031bf9f&oe=60D6AFB7",
        )
        return embed

    def ez_players_list(self, party_id, waiting=False):
        final_list = []
        for player in self.parties[party_id]["players"]:
            final_list.append(
                f"- <@!{player}>: {self.parties[party_id]['players'][player]['score']}/10{' <a:hourgalss:873200874636337172>' if waiting else ''}"
            )
        return final_list

    # Used to generate question embed lmao
    def ez_question_embed(self, party_id, leaderboard=False, waiting=False):
        curent_question_id = self.parties[party_id]["ids"][
            self.parties[party_id]["quizz"]["current"]
        ]  # Choppe l'id de la question en cours
        raw_question = self.QPQ.get_question(
            self.parties[party_id]["quizz"]["id"], curent_question_id
        )  # Récupère le paquet de la question

        embed = discord.Embed(
            title=f"Question {str(self.parties[party_id]['quizz']['current'] + 1)}/10",
            color=discord.Colour.random(),
            description=clean_question(raw_question["question"]),
        )

        try:
            # Rajoute une thumbnail si il y en a une
            embed.set_thumbnail(url=f"https://quipoquiz.com{raw_question['image']}")
        except KeyError:
            pass
        embed.set_footer(text=party_id)
        embed = self.ez_set_author(embed, party_id)
        if leaderboard:
            players = self.parties[party_id]["players"]
            embed.add_field(
                name=f"{len(players)} joueur{'s' if len(players) > 1 else ''}",
                value="\n".join(self.ez_players_list(party_id, waiting)),
            )
        self.update_timestamp(party_id)
        return embed

    def ez_answer_embed(self, party_id):
        curent_question_id = self.parties[party_id]["ids"][
            self.parties[party_id]["quizz"]["current"]
        ]  # Choppe l'id de la question en cours
        raw_answer = self.QPQ.get_answer(
            self.parties[party_id]["quizz"]["id"], curent_question_id
        )  # Choppe le paquet de la réponse
        raw_question = self.QPQ.get_question(
            self.parties[party_id]["quizz"]["id"], curent_question_id
        )  # Choppe le paquet de la question

        embed = discord.Embed(
            title=f"Question {str(self.parties[party_id]['quizz']['current'] + 1)}/10",
            color=discord.Colour.random(),
            description=f"{clean_answer(raw_question['question'])}\n{clean_answer(raw_answer['explanation'])}",
        )

        try:
            # Rajoute une thumbnail si il y en a une
            embed.set_thumbnail(url=f"https://quipoquiz.com{raw_question['image']}")
        except KeyError:
            pass
        embed.set_footer(text=party_id)
        embed = self.ez_set_author(embed, party_id)

        players = []
        for player in self.parties[party_id]["players"]:
            if (
                self.parties[party_id]["players"][player]["answer"]
                == raw_answer["real_answer"]
            ):
                self.parties[party_id]["players"][player]["score"] += 1
            players.append(
                f"- <@!{player}>: {self.parties[party_id]['players'][player]['score']}/10"
            )

        embed.add_field(
            name=f"{len(players)} joueur{'s' if len(players) > 1 else ''}",
            value="\n".join(players),
        )
        self.update_timestamp(party_id)
        return embed

    def ez_summary_embed(self, party_id):
        embed = discord.Embed(title="Quizz terminé !", color=discord.Colour.gold())
        embed = self.ez_set_author(embed, party_id)
        embed.set_footer(text=party_id)

        players = {}
        for player in self.parties[party_id]["players"]:
            players[player] = self.parties[party_id]["players"][player]["score"]
        players = sort_dict(players)
        players.reverse()

        final_value = ""
        tracker = 0
        for player, score in players:
            places = ["🥇", "🥈", "🥉"]
            final_value += f"- <@!{player}>: {str(score)} {places[tracker] if tracker < 4 else ''}\n"
            tracker += 1
        embed.add_field(name="Leaderboard", value=final_value)
        return embed

    def has_everyone_answered(self, party_id):
        """Test si tout le monde a répondu"""
        verif = True
        for player_id in self.parties[party_id]["players"]:
            if self.parties[party_id]["players"][player_id]["answer"] is None:
                verif = False
        self.update_timestamp(party_id)
        return verif

    async def send_question(self, player_id, party_id):
        # Fetch player
        player: discord.User = await self.bot.fetch_user(player_id)
        embed = self.ez_question_embed(party_id)  # Generate question embed
        msg = await player.send(embed=embed)  # Send it to the player

        emotes = REACTIONS.answers_reactions  # liste des emotes a rajouter
        for emote in emotes:
            await msg.add_reaction(emote)  # Rajoute les emote sur le message
        self.parties[party_id]["players"][player_id]["msg_id"] = msg.id
        # Rajoute le message dans la withelist
        self.quick_quizz_messages.append(msg.id)
        # Rajoute le message dans la withelist
        self.quick_quizz_channels.append(msg.channel.id)

    async def send_party_question(self, party_id):
        """Envoie les question a tout les joueurs"""
        for player_id in self.parties[party_id]["players"]:
            await self.send_question(player_id, party_id)
        self.update_timestamp(party_id)

    async def send_answer(self, party_id):
        for player_id in self.parties[party_id]["players"]:
            # Fetch player
            player: discord.User = await self.bot.fetch_user(player_id)
            msg = await player.fetch_message(
                self.parties[party_id]["players"][player_id]["msg_id"]
            )
            embed = self.ez_question_embed(party_id)  # Generate question embed

            raw_answer = self.QPQ.get_answer(
                self.parties[party_id]["quizz"]["id"],
                self.parties[party_id]["ids"][
                    self.parties[party_id]["quizz"]["current"]
                ],
            )
            embed.add_field(
                name="VRAI :" if raw_answer["real_answer"] else "FAUX :",
                value=clean_answer(raw_answer["explanation"]),
            )
            await msg.edit(embed=embed)  # Send it to the player

            # liste des emotes à rajouter (bordel j'altearn entre le français
            # et l'anglais)
            emotes = REACTIONS.answers_reactions
            for emote in emotes:
                # Rajoute les emote sur le message
                await msg.add_reaction(emote)
        self.update_timestamp(party_id)

    async def update_main_embed(self, embed: discord.Embed, party_id, player_id):
        old_field = embed.fields[0]
        raw_players = old_field.value.split("\n")
        new_field_value = []
        for raw_ligne in raw_players:
            if str(player_id) in raw_ligne:
                raw_ligne = raw_ligne.split(" ")
                del raw_ligne[len(raw_ligne) - 1]
                raw_ligne = " ".join(raw_ligne)
                raw_ligne += "✅"
            new_field_value.append(raw_ligne)
        embed.clear_fields()
        embed.add_field(name=old_field.name, value="\n".join(new_field_value))
        channel: discord.TextChannel = await self.bot.fetch_channel(
            self.parties[party_id]["channel_id"]
        )
        msg: discord.Message = await channel.fetch_message(
            self.parties[party_id]["msg_id"]
        )
        self.update_timestamp(party_id)
        return await msg.edit(embed=embed)

    async def player_leave_update(self, message: discord.Message, party_id, user):
        embed = message.embeds[0]  # Récupère l'embed
        raw_players = embed.fields[0].value.split("\n")  # Split tout les joueurs

        players = []
        for player in raw_players:
            if str(user.id) not in player:
                # Si c'est le joueur qui se barre alors on le remet pas dans la
                # liste
                players.append(player)
        temp = len(players)
        players = "\n".join(players)  # Refait la liste
        embed.clear_fields()  # Cleanup

        embed.add_field(
            name="{} joueur{}".format(temp, "s" if temp > 1 else ""), value=players
        )  # Refait la liste des joueurs
        self.parties[party_id]["players"].pop(user.id)  # remove le joueur de la party
        embed.set_footer(text=party_id)
        embed = self.ez_set_author(embed, party_id)
        self.update_timestamp(party_id)
        return await message.edit(embed=embed)  # Nouvel embed

    async def update_player_choice(self, party_id, player_id):
        channel: discord.TextChannel = await self.bot.fetch_channel(
            self.parties[party_id]["channel_id"]
        )
        msg: discord.Message = await channel.fetch_message(
            self.parties[party_id]["msg_id"]
        )
        embed: discord.Embed = msg.embeds[0]
        field_name = embed.fields[0].name
        field_value = embed.fields[0].value.split("\n")
        new_value = ""
        for line in field_value:
            if str(player_id) in line:
                new_value += "\n{}".format(
                    line.replace("<a:hourgalss:873200874636337172>", "✅")
                )
            else:
                new_value += "\n{}".format(line)
        embed.clear_fields()
        embed.add_field(name=field_name, value=new_value)
        await msg.edit(embed=embed)
        self.update_timestamp(party_id)

    @tasks.loop(minutes=5)
    async def check_if_active(self):
        timestamp = round(time.time())
        partys_to_pop = []
        for party_id in self.parties:
            if party_id != "0":
                if self.parties[party_id]["timestamp"] < timestamp + 60 * 100000:
                    channel: Optional[discord.TextChannel] = await self.bot.get_channel(
                        self.parties[party_id]["channel_id"]
                    )
                    if channel is not None:
                        await channel.send(
                            f"<@{self.parties[party_id]['author_id']}> ton quizz sur {self.QPQ.get_name(self.parties[party_id]['quizz']['id'])} s'est arrêté car inactif !"
                        )
                    partys_to_pop.append(party_id)
                else:
                    self.parties[party_id]["timestamp"] = timestamp

        for party_id in partys_to_pop:
            self.parties.pop(party_id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, pauload: discord.RawReactionActionEvent):
        if pauload.emoji.name not in REACTIONS.all_reactions:
            return  # Si c'est pas les émojis du quizz alors on passe
        elif pauload.user_id == self.bot.user.id:
            return  # Si c'est le bot sa dégage
        elif pauload.channel_id not in self.quick_quizz_channels:
            return  # Permet d'éviter de faire une chiée de requêtes
        elif pauload.message_id not in self.quick_quizz_messages:
            return  # Same

        channel: discord.DMChannel = await self.bot.fetch_channel(pauload.channel_id)
        message: discord.Message = await channel.fetch_message(pauload.message_id)
        if len(message.embeds) == 0:
            return  # Vu que tout passe par embeds, si y'en a pas on passe

        if pauload.emoji.name == REACTIONS.PREVIOUS_QUESTION:
            if "/" in message.embeds[0].footer.text:
                raw_footer = message.embeds[0].footer.text.split("/")
                embed = message.embeds[0]
                embed.clear_fields()
                if raw_footer[0] == "1":
                    param = 1
                else:
                    param = int(raw_footer[0]) - 1

                ids = [quizz_id for quizz_id in self.QPQ.data]
                for n in range(15):
                    embed.add_field(
                        name=self.QPQ.data[ids[n + ((param - 1) * 15)]]["name"],
                        value=f"ID du quizz: `{ids[n + ((param-1) * 15)]}`",
                    )
                embed.set_footer(text=f"{param}/{len(self.QPQ.data) // 15}")
                await message.remove_reaction(
                    REACTIONS.PREVIOUS_QUESTION, pauload.member
                )
                return await message.edit(embed=embed)

        elif pauload.emoji.name == REACTIONS.NEXT_QUESTION:
            if "/" in message.embeds[0].footer.text:
                raw_footer = message.embeds[0].footer.text.split("/")
                embed = message.embeds[0]
                embed.clear_fields()
                if raw_footer[0] == str(len(self.QPQ.data) // 15):
                    param = len(self.QPQ.data) // 15
                else:
                    param = int(raw_footer[0]) + 1

                ids = [quizz_id for quizz_id in self.QPQ.data]
                for n in range(15):
                    embed.add_field(
                        name=self.QPQ.data[ids[n + ((param - 1) * 15)]]["name"],
                        value=f"ID du quizz: `{ids[n + ((param-1) * 15)]}`",
                    )
                embed.set_footer(text=f"{param}/{len(self.QPQ.data) // 15}")
                await message.remove_reaction(REACTIONS.NEXT_QUESTION, pauload.member)
                return await message.edit(embed=embed)

        try:
            # On vérifie que y'est bien l'id de la party dans le footer
            party_id = int(message.embeds[0].footer.text)
        except ValueError:
            return  # Sinon on passe

        party_id = str(party_id)
        self.update_timestamp(party_id)
        if party_id not in self.parties:
            return

        if pauload.guild_id is not None:  # Si la réaction est sur un serveur
            # Si celui qui a réagis est le créateur du quizz
            if pauload.user_id == self.parties[party_id]["author_id"]:
                if (
                    pauload.emoji.name == REACTIONS.START_QUIZ
                ):  # 🆗 => Commencer le quizz

                    # Génération de l'embed de question
                    embed = self.ez_question_embed(party_id)
                    prev_players_markdown = (
                        message.embeds[0].fields[0].value.split("\n")
                    )  # On récupère les joueurs

                    for n, player in enumerate(prev_players_markdown):
                        # On rajoute le petit emote de sablier
                        prev_players_markdown[n] = (
                            player + " <a:hourgalss:873200874636337172>"
                        )
                    embed.add_field(
                        name="{} joueur{}".format(
                            len(prev_players_markdown),  # Nombre de joueurs
                            "s" if len(prev_players_markdown) > 1 else "",
                        ),
                        value="\n".join(prev_players_markdown),
                    )  # Remise de la liste des joueurs
                    await message.edit(embed=embed)  # Edit de l'ancien embed

                    await message.clear_reaction(REACTIONS.START_QUIZ)
                    await message.add_reaction(REACTIONS.FORWARD_QUESTION)
                    self.parties[party_id]["started"] = True
                    # On envoit les questions en mp
                    return await self.send_party_question(party_id)

                elif (
                    pauload.emoji.name == REACTIONS.STOP_QUIZ
                ):  # ❌ => annulation du quizz
                    embed = discord.Embed(title="Quizz annulé")
                    self.parties.pop(party_id)  # Supression dans le dict
                    await message.clear_reactions()  # Retire toute les réactions
                    return await message.edit(embed=embed)  # Feedback user

                elif (
                    pauload.emoji.name == REACTIONS.FORWARD_QUESTION
                ):  # on skip cette question
                    if not self.has_everyone_answered(party_id):
                        return await channel.send(
                            f"<@{self.parties[party_id]['author_id']}> tout le monde n'a pas encore répondu !"
                        )

                    if self.parties[party_id]["quizz"]["current"] < 10:
                        embed = self.ez_question_embed(
                            party_id, leaderboard=True, waiting=True
                        )
                        await message.edit(embed=embed)
                        # On envoit les questions en mp
                        await self.send_party_question(party_id)
                        for player in self.parties[party_id]["players"]:
                            self.parties[party_id]["players"][player]["answer"] = None
                        await message.remove_reaction(
                            REACTIONS.FORWARD_QUESTION, pauload.member
                        )
                    else:
                        await message.clear_reactions()
                        await message.edit(embed=self.ez_summary_embed(party_id))
                        return self.parties.pop(party_id)
            else:
                if pauload.emoji.name == REACTIONS.JOIN_QUIZ:  # Un joueur join
                    embed = message.embeds[0]
                    # Rajoute le joueur dans l'embed
                    players = (
                        embed.fields[0].value + f"\n- <@!{pauload.user_id}> 0/10"
                        f'{" <a:hourgalss:873200874636337172>" if self.parties[party_id]["started"] else ""}'
                    )
                    embed.clear_fields()  # Cleanup

                    temp = players.split("\n")
                    embed.add_field(
                        name="{} joueur{}".format(
                            len(temp), "s" if len(temp) > 1 else ""
                        ),
                        value=players,
                    )
                    embed.set_footer(text=party_id)
                    embed = self.ez_set_author(embed, party_id)
                    self.parties[party_id]["players"][int(pauload.user_id)] = {
                        "score": 0,
                        "answer": None,
                        "msg_id": 0,
                    }
                    if self.parties[party_id]["started"]:
                        await self.send_question(pauload.user_id, party_id)

                    return await message.edit(embed=embed)  # Nouvel embed

        else:  # Si c'est en mp
            if pauload.emoji.name == REACTIONS.ANSWER_FALSE:
                # Choisi la réponse négative
                self.parties[party_id]["players"][pauload.user_id]["answer"] = False
                await self.update_player_choice(party_id, pauload.user_id)
            elif pauload.emoji.name == REACTIONS.ANSWER_TRUE:
                # Choisi la réponse positive
                self.parties[party_id]["players"][pauload.user_id]["answer"] = True
                await self.update_player_choice(party_id, pauload.user_id)

            if pauload.emoji.name in [REACTIONS.ANSWER_TRUE, REACTIONS.ANSWER_FALSE]:
                if self.has_everyone_answered(party_id):
                    main_channel: discord.TextChannel = await self.bot.fetch_channel(
                        self.parties[party_id]["channel_id"]
                    )
                    main_message: discord.Message = await main_channel.fetch_message(
                        self.parties[party_id]["msg_id"]
                    )
                    await main_message.edit(embed=self.ez_answer_embed(party_id))
                    await self.send_answer(party_id)
                    self.parties[party_id]["quizz"]["current"] += 1
                    return

            if (
                pauload.emoji.name == REACTIONS.ANSWER_LEAVE
            ):  # Le joueur veut quitter le quizz
                main_channel: discord.TextChannel = await self.bot.fetch_channel(
                    self.parties[party_id]["channel_id"]
                )
                main_message: discord.Message = await main_channel.fetch_message(
                    self.parties[party_id]["msg_id"]
                )
                # Faut optimiser ct'e merde
                user = await self.bot.fetch_user(pauload.user_id)
                # Retire le joueur
                await self.player_leave_update(main_message, party_id, user)
                # Feedback user
                return await channel.send("Vous avez quitté le quizz")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, pauload: discord.RawReactionActionEvent):
        if pauload.emoji.name != REACTIONS.JOIN_QUIZ:
            return  # Si c'est pas les émojis du quizz alors on passe
        elif pauload.user_id == self.bot.user.id:
            return  # Si c'est le bot, alors on passe
        elif pauload.channel_id not in self.quick_quizz_channels:
            return  # Permet d'éviter de faire une chiée de requêtes
        elif pauload.message_id not in self.quick_quizz_messages:
            return  # Same

        channel: discord.DMChannel = await self.bot.fetch_channel(pauload.channel_id)
        message: discord.Message = await channel.fetch_message(pauload.message_id)
        if len(message.embeds) == 0:
            return  # Vu que tout passe par embeds, si y'en a pas on passe

        try:
            # On vérifie que y'est bien l'id de la party dans le footer
            party_id = int(message.embeds[0].footer.text)
        except ValueError:
            return  # Sinon on passe

        party_id = str(party_id)
        self.update_timestamp(party_id)
        if party_id not in self.parties:
            return

        if (
            pauload.guild_id is not None
            and pauload.emoji.name == REACTIONS.JOIN_QUIZ
            and not self.parties[party_id]["started"]
        ):  # Si un joueur se barre
            # Récupère l'user
            user: discord.User = await self.bot.fetch_user(pauload.user_id)
            # Generate new player list
            return await self.player_leave_update(message, party_id, user)

    @commands.group(name="quizz")
    async def quizz_core(self, ctx: MyContext):
        await ctx.message.delete()
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(title="Quizz help", color=discord.Colour.orange())
            embed.add_field(name=f"`quizz`", value="Shows this message", inline=False)
            embed.add_field(
                name=f"`quizz start <quizz_id>`", value="Démarre un quizz", inline=False
            )
            embed.add_field(
                name="`quizz themes`",
                value="Donne la liste des thèmes WIP",
                inline=False,
            )
            return await ctx.send(embed=embed)

    @quizz_core.command(name="start")
    async def _quizz_start(self, ctx: MyContext, quizz_id: str):
        party_id = "0"
        while party_id in self.parties:
            party_id = str(round(random.random() * 10000))

        question_ids = []
        raw_question = self.QPQ.get_questions(quizz_id)
        if raw_question is None:
            return await ctx.send("L'ID du quizz est invalide.")
        for question_id in raw_question:
            question_ids.append(question_id)

        self.parties[party_id] = {
            "author_id": ctx.author.id,
            "guild_id": ctx.guild.id,
            "timestamp": time.time(),
            "msg_id": 0,
            "channel_id": ctx.channel.id,
            "players": {int(ctx.author.id): {"score": 0, "answer": None, "msg_id": 0}},
            "quizz": {"id": quizz_id, "current": 0},
            "ids": question_ids,
            "started": False,
        }

        embed = discord.Embed(
            title=f"Partie de {ctx.author.display_name}",
            description=f"Sur le thème de :\n\t- **{self.QPQ.get_name(quizz_id)}**",
        )
        embed.add_field(name="1 joueur", value=f"- {ctx.author.mention}: 0/10")
        embed.set_footer(text=party_id)
        embed = self.ez_set_author(embed, party_id)
        msg: discord.Message = await ctx.send(embed=embed)
        self.parties[party_id]["msg_id"] = msg.id
        emojis = [REACTIONS.JOIN_QUIZ, REACTIONS.STOP_QUIZ, REACTIONS.START_QUIZ]
        for emoji in emojis:
            await msg.add_reaction(emoji)
        self.quick_quizz_messages.append(msg.id)
        self.quick_quizz_channels.append(ctx.channel.id)

    @quizz_core.command(name="themes")
    async def _quizz_themes(self, ctx: MyContext):
        embed = discord.Embed(title="THEMES", color=discord.Colour.random())
        ids = [quizz_id for quizz_id in self.QPQ.data]
        for n in range(15):
            embed.add_field(
                name=self.QPQ.data[ids[n]]["name"], value=f"ID du quizz: `{ids[n]}`"
            )
        embed.set_footer(text=f"1/{len(self.QPQ.data)//15}")
        msg: discord.Message = await ctx.send(embed=embed)
        emojis = ["⬅️", "➡️"]
        for emoji in emojis:
            await msg.add_reaction(emoji)
        self.quick_quizz_messages.append(msg.id)
        self.quick_quizz_channels.append(ctx.channel.id)
        return

config = {}
async def setup(bot:Gunibot=None, plugin_config:dict=None):
    if bot is not None:
        await bot.add_cog(Quizz(bot), icon="❓")
    if plugin_config is not None:
        global config
        config.update(plugin_config)

