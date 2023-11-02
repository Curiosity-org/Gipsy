"""
Ce programme est régi par la licence CeCILL soumise au droit français et
respectant les principes de diffusion des logiciels libres. Vous pouvez
utiliser, modifier et/ou redistribuer ce programme sous les conditions
de la licence CeCILL diffusée sur le site "http://www.cecill.info".
"""

import datetime
import time

import discord
from discord.ext import tasks

from utils import Gunibot

fr_months = [
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Aout",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]
en_months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
fi_months = [
    "tammikuu",
    "helmikuu",
    "maaliskuu",
    "huhtikuu",
    "toukokuu",
    "kesäkuu",
    "heinäkuu",
    "elokuu",
    "syyskuu",
    "lokakuu",
    "marraskuu",
    "joulukuu",
]


class TimeCog(discord.ext.commands.Cog):
    """This cog handles all manipulations of date, time, and time interval. So cool, and so fast"""

    def __init__(self, bot: Gunibot):
        self.bot = bot
        self.file = "timeclass"

    def add_task(self, delay: int, coro, *args, **kwargs):
        """Schedule a task for later, using discord.ext tasks manager"""
        delay = round(delay)

        async def launch(task, coro, *args, **kwargs):
            if task.current_loop != 0:
                await self.bot.wait_until_ready()
                self.bot.log.info(
                    f"[TaskManager] Tâche {coro.__func__} arrivée à terme"
                )
                try:
                    await coro(*args, **kwargs)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self.bot.get_cog("Errors").on_error(exc)

        a = tasks.loop(seconds=delay, count=2)(launch)
        a.error(self.bot.get_cog("Errors").on_error)
        a.start(a, coro, *args, **kwargs)
        self.bot.log.info(
            f"[TaskManager] Nouvelle tâche {coro.__func__} programmée pour dans {delay}s"
        )
        return a

    class timedelta:
        def __init__(
            self,
            years=0,
            months=0,
            days=0,
            hours=0,
            minutes=0,
            seconds=0,
            total_seconds=0,
            precision=2,
        ):
            self.years = years
            self.months = months
            self.days = days
            self.hours = hours
            self.minutes = minutes
            self.seconds = seconds
            self.total_seconds = total_seconds
            self.precision = precision

        def set_from_seconds(self):
            t = self.total_seconds
            rest = 0
            years, rest = divmod(t, 86400 * 365)
            months, rest = divmod(rest, 86400 * 365 / 12)
            days, rest = divmod(rest, 86400)
            hours, rest = divmod(rest, 3600)
            minutes, rest = divmod(rest, 60)
            seconds = rest
            self.years = int(years)
            self.months = int(months)
            self.days = int(days)
            self.hours = int(hours)
            self.minutes = int(minutes)
            if self.precision == 0:
                self.seconds = int(seconds)
            else:
                self.seconds = round(seconds, self.precision)

    async def time_delta(
        self,
        date1,
        date2=None,
        lang="en",
        year=False,
        hour=True,
        form="developed",
        precision=2,
    ):
        """Traduit un intervale de deux temps datetime.datetime en chaine de caractère lisible"""
        if date2 is not None:
            if isinstance(date2, datetime.datetime):
                delta = abs(date2 - date1)
                inputed_time = await self.time_interval(delta, precision)
            else:
                raise ValueError
        else:
            inputed_time = self.timedelta(total_seconds=date1, precision=precision)
            inputed_time.set_from_seconds()
        if form == "digital":
            if hour:
                inputed_hours = (
                    f"{inputed_time.hours}:{inputed_time.minutes}:"
                    f"{inputed_time.seconds}"
                )
            else:
                inputed_hours = ""
            if lang == "fr":
                text = "{}/{}{} {}".format(  # pylint: disable=consider-using-f-string
                    inputed_time.days,
                    inputed_time.months,
                    "/" + str(inputed_time.years) if year else "",
                    inputed_hours,
                )
            else:
                text = "{}/{}{} {}".format(  # pylint: disable=consider-using-f-string
                    inputed_time.months,
                    inputed_time.days,
                    "/" + str(inputed_time.years) if year else "",
                    inputed_hours,
                )
        elif form == "temp":
            text = str()
            if (
                inputed_time.days
                + inputed_time.months * 365 / 12
                + inputed_time.years * 365
                > 0
            ):
                inputed_days = round(inputed_time.days + inputed_time.months * 365 / 12)
                if not year:
                    inputed_days += round(inputed_time.years * 365)
                elif year and inputed_time.years > 0:
                    text += (
                        str(inputed_time.years) + "a "
                        if lang == "fr"
                        else str(inputed_time.years) + "y "
                    )
                text += (
                    str(inputed_days) + "j "
                    if lang == "fr"
                    else str(inputed_days) + "d "
                )
            if hour:
                if inputed_time.hours > 0:
                    text += str(inputed_time.hours) + "h "
                if inputed_time.minutes > 0:
                    text += str(inputed_time.minutes) + "m "
                if inputed_time.seconds > 0:
                    text += str(inputed_time.seconds) + "s "
            text = text.strip()
        else:
            text = str()
            if lang == "fr":
                lib = [
                    "ans",
                    "an",
                    "mois",
                    "mois",
                    "jours",
                    "jour",
                    "heures",
                    "heure",
                    "minutes",
                    "minute",
                    "secondes",
                    "seconde",
                ]
            elif lang == "lolcat":
                lib = [
                    "yearz",
                    "year",
                    "mons",
                    "month",
                    "dayz",
                    "day",
                    "hourz",
                    "hour",
                    "minutz",
                    "minut",
                    "secondz",
                    "secnd",
                ]
            elif lang == "fi":
                lib = [
                    "Vuotta",
                    "vuosi",
                    "kuukautta",
                    "kuukausi",
                    "päivää",
                    "päivä",
                    "tuntia",
                    "h",
                    "minuuttia",
                    "minute",
                    "sekuntia",
                    "toinen",
                ]
            else:
                lib = [
                    "years",
                    "year",
                    "months",
                    "month",
                    "days",
                    "day",
                    "hours",
                    "hour",
                    "minutes",
                    "minute",
                    "seconds",
                    "second",
                ]
            if year and inputed_time.years != 0:
                if inputed_time.years > 1:
                    text += str(inputed_time.years) + " " + lib[0]
                else:
                    text += str(inputed_time.years) + " " + lib[1]
                text += " "
            if inputed_time.months > 1:
                text += str(inputed_time.months) + " " + lib[2]
            elif inputed_time.months == 1:
                text += str(inputed_time.months) + " " + lib[3]
            text += " "
            if inputed_time.days > 1:
                text += str(inputed_time.days) + " " + lib[4]
            elif inputed_time.days == 1:
                text += str(inputed_time.days) + " " + lib[5]
            if hour:
                if inputed_time.hours > 1:
                    text += " " + str(inputed_time.hours) + " " + lib[6]
                elif inputed_time.hours == 1:
                    text += " " + str(inputed_time.hours) + " " + lib[7]
                text += " "
                if inputed_time.minutes > 1:
                    text += str(inputed_time.minutes) + " " + lib[8]
                elif inputed_time.minutes == 1:
                    text += str(inputed_time.minutes) + " " + lib[9]
                text += " "
                if inputed_time.seconds > 1:
                    text += str(inputed_time.seconds) + " " + lib[10]
                elif inputed_time.seconds == 1:
                    text += str(inputed_time.seconds) + " " + lib[11]
        return text.strip()

    async def time_interval(self, tmd, precision=2):
        """Crée un objet de type timedelta à partir d'un objet datetime.timedelta"""
        inputed_time = tmd.total_seconds()
        obj = self.timedelta(total_seconds=inputed_time, precision=precision)
        obj.set_from_seconds()
        return obj

    async def date(self, date, lang="fr", year=False, hour=True, digital=False):
        """
        Traduit un objet de type datetime.datetime en chaine de caractère lisible.
        Renvoie un str
        """
        if isinstance(date, time.struct_time):
            date = datetime.datetime(*date[:6])
        if isinstance(date, datetime.datetime):
            if len(str(date.day)) == 1:
                jour = "0" + str(date.day)
            else:
                jour = str(date.day)
            times = []
            if lang == "fr":
                month = fr_months
            elif lang == "fi":
                month = fi_months
            else:
                month = en_months
            for i in ["hour", "minute", "second"]:
                argument = getattr(date, i)
                if len(str(argument)) == 1:
                    times.append("0" + str(argument))
                else:
                    times.append(str(argument))
            if digital:
                if date.month < 10:
                    month = "0" + str(date.month)
                else:
                    month = str(date.month)
                separator = "/"
                if lang == "fr":
                    formated_date = "{d}/{m}{y}  {h}"
                elif lang == "fi":
                    formated_date = "{d}.{m}{y}  {h}"
                    separator = "."
                else:
                    formated_date = "{m}/{d}{y}  {h}"
                formated_date = formated_date.format(
                    d=jour,
                    m=month,
                    y=separator + str(date.year) if year else "",
                    h=":".join(times) if hour else "",
                )
            else:
                if lang == "fr" or lang == "fi":
                    formated_date = "{d} {m} {y}  {h}"
                else:
                    formated_date = "{m} {d}, {y}  {h}"
                formated_date = formated_date.format(
                    d=jour,
                    m=month[date.month - 1],
                    y=str(date.year) if year else "",
                    h=":".join(times) if hour else "",
                )
            return formated_date.strip()


async def setup(bot: Gunibot = None):
    await bot.add_cog(TimeCog(bot))
