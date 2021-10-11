# Bamboo's Sidekick
import asyncio, signal
import discord
import os, os.path
from os import path
import lyricsgenius as genius
import config_sample
from discord.ext import commands
from discord.ext.commands import Bot
import random, math
import openweather
from datetime import datetime
import requests, json
import time, multiprocessing, threading
import qbittorrentapi
from azlyrics.azlyrics import lyrics as az_lyrics

from src import db

# OpenWeather setup
ow = openweather.OpenWeather()
owurl = "http://api.openweathermap.org/data/2.5/weather?"

# Genius Setup
gapi = genius.Genius(config_sample.GENIUS_TOKEN)

# Discord Setup
#TOKEN = os.getenv("TOKEN")
client = discord.Client()

# qBT Setup
qbt_client = qbittorrentapi.Client(host=f'{config_sample.EXT_HOST}:{config_sample.QBIT_PORT}', username=config_sample.QBIT_USER, password=config_sample.QBIT_PASS)
def qbtLogIn():
    try:
        print("Attempting qBitTorrent Web API auth...")
        p = multiprocessing.Process(target=qbt_client.auth_log_in)
        p.start()
        p.join(10)
        isKill = False
        if p.is_alive():
            print("[!] QBT Login timeout. Killing...")
            isKill = True
            p.kill() # ?! this code may not differentiate between the process if it is still trying to connect, or if it has connected but has remained an active socket
            p.join()
        if isKill == False:
            print("Process has not died. Assuming qBitTorrent connection is good.")
            p.join()
    except Exception as e:
        print("[E] FAILED TO CONNECT TO QBT")
threading.Thread(target=qbtLogIn).start()
print("Spun off thread qbtLogIn...")

# TMDB api and config
tmdbapiurl = "https://api.themoviedb.org/3/"

try:
    r = requests.get(f'{tmdbapiurl}configuration')
    tmdbResp = json.loads(r.text)
except Exception as e:
    print(e)



### Strings
helpMessage = """**Bamboo's Sidekick here!**\nHere's what I can do:
**Genius Commands**:
b!lyricsfor / b!lf (artist) - (song) = Get lyrics from Genius for specified song
b!genius / b!g (artist) - (song) = Get a Genius page link for a song

**Weather Commands**:
b!setlocation (city/ZIP) = Set your user's location
b!weather [city/ZIP] = Get location. Requires city/ZIP if you have not set your location

**qBitTorrent Local Commands**
qb!info = request qBitTorrent info for specified host on my LAN
qb!all = get all torrent info for specified host on my LAN

**Radarr Local Commands**
r!info = get info for Radarr instance for specified host on my LAN
r!get (tmdb) = get info for a specific movie using a TMDB ID number

This bot also listens for certain phrases and the Chuu bot to provide lyrics passively.
"""

## RADARR FUNCTIONS

@client.event
async def reqRadarr(rapir, args):
    if len(args) == 0:
        r = requests.get(f'http://{config_sample.rhost}:{config_sample.rport}/api/v3/{rapir}?apiKey={config_sample.rapi}')
    else:
        r = requests.get(f'http://{config_sample.rhost}:{config_sample.rport}/api/v3/{rapir}?{args}&apiKey={config_sample.rapi}')
    return r

@client.event
async def getRadarrInfo():
    try:
        r = await reqRadarr("system/status", "")
    except Exception as e:
        print(e)
        return e
    try:
        radarrResp = json.loads(r.text)
    except Exception as e:
        print(e)
        return e

    raMsgEmbed = discord.Embed(title="Radarr Application Info", description="", color=0x37ff00)
    raMsgEmbed.set_author(name="Radarr API")
    raMsgEmbed.add_field(name="Version:", value=radarrResp["version"])
    raMsgEmbed.add_field(name="OS:", value=f'{radarrResp["osName"]} {radarrResp["osVersion"]}')
    raMsgEmbed.add_field(name="SQLite Version:", value=radarrResp["sqliteVersion"])
    if radarrResp["isProduction"]:
        raMsgEmbed.add_field(name="Status:", value="Production build")

    return raMsgEmbed

@client.event
async def getRadarrMovies(tmdb):
    try:
        r = await reqRadarr("movie", f"tmdbId={tmdb}")
    except Exception as e:
        return e
        print(e)
    try:
        radarrResp = json.loads(r.text)
    except Exception as e:
        print(e)
        return e

    genres = ""
    for i in len(radarrResp[0]["genres"]):
        if i == 1:
            genres += radarrResp[0]["genres"][i]
        else:
            genres += ", " + radarrResp[0]["genres"][i]

    rgMsgEmbed = discord.Embed(title=f'{genres}', description=f'{radarrResp[0]["year"]}')
    rgMsgEmbed.set_author(name=f'{radarrResp[0]["title"]}', url=f'{radarrResp[0]["website"]}')
#    rgMsgEmbed.set_thumbnail(url=)


## QBIT FUNCTIONS
@client.event
async def getQbtAppInfo():
    qbOtherDesc = ""
    try:
        for k,v in qbt_client.app.build_info.items():
            qbOtherDesc += f'{k}: {v}; '
    except Exception as e:
        await message.channel.send(f"qBT info request failed with: ```{e}```")
    qbMsgEmbed = discord.Embed(title="qBittorrent Application Info", description="", color=0x37ff00)
    qbMsgEmbed.set_author(name="qBitTorrent API")
    qbMsgEmbed.add_field(name="Client App version:", value=qbt_client.app.version, inline=True)
    qbMsgEmbed.add_field(name="API Version:", value=qbt_client.app.web_api_version, inline=True)
    qbMsgEmbed.add_field(name="Others:", value=qbOtherDesc)

    return qbMsgEmbed

@client.event
async def getQbtAllTorrents():
    qbtTorrentList = ""
    #for torrent in qbt_client.torrents_info():
    #    qbtTorrentList += f'{torrent.hash[-6:]}: {torrent.name} ({torrent.state}) \n'

    qbtMessage = """
QBT Torrent List:\n
"""
    try:
        for torrent in qbt_client.torrents_info():
            #qbtTorrentList += f'{torrent.name} {torrent.state}'
            if torrent.state == "downloading":
                qbtTorrentState = "Downloading"
            elif torrent.state == "forcedDL":
                qbtTorrentState = "Downloading [F]"
            elif torrent.state == "pausedDL":
                qbtTorrentState = "Paused [DL]"
            elif torrent.state == "queuedDL":
                qbtTorrentState = "Queued [DL]"
            elif torrent.state == "stalledDL":
                qbtTorrentState = "Stalled [DL]"
            elif torrent.state == "stalledUP":
                qbtTorrentState = "Stalled [UL]"
            elif torrent.state == "uploading":
                qbtTorrentState = "Seeding"
            elif torrent.state == "forcedUP":
                qbtTorrentState = "Seeding [F]"
            elif torrent.state == "pausedUP":
                qbtTorrentState = "Paused [UL]"
            elif torrent.state == "queuedUP":
                qbtTorrentState = "Queued [UL]"
            elif torrent.state == "error":
                qbtTorrentState = "Error"
            else:
                qbtTorrentState = torrent.state
            torrentEntry = f'[H]: {torrent.hash[-6:]} --> {torrent.name} // State: {qbtTorrentState}'
            qbtMessage += "     └: %s \n" % torrentEntry
    except Exception as e:
        await message.channel.send(f"Failed to request torrent list: ```{e}```")

    return qbtMessage

#@client.event
#async def getQbtTorrentInfo(args):
    # # TODO: Add more things

## GENIUS FUNCTIONS
@client.event
async def getLyricsFor(a, s, message):
    try:
        print("[@] Attempting Genius API search...")
        song = gapi.search_song(s, a)
    except Exception as e:
        errorMsg = "Failed to execute Genius API search\n```" + str(e) + "```"
        print("[!] Failed to execute Genius API for %s \n" % str(message.author) + str(e))
        return errorMsg
    if song:
        url = song.url
        lyrics = song.lyrics
        for line in lyrics:
            if line == '':
                lyrics.remove(line)

        if lyrics.rstrip().lstrip().split()[-1] == "URLCopyEmbedCopy":
            lyrics = lyrics[:-28].rstrip('0123456789')
            print("[!] Cut out Genius anomalies")

        response = f"```{lyrics}```"
        return response
    else:
        errorMsg = "I was unable to find the queried song. My apologies!"
        print("[W] No results found for {} by {}".format(s, a))
        return errorMsg

@client.event
async def getWeatherForCity(city, message):
    owresponse = requests.get(owurl + "appid=" + config_sample.OWAPI + "&q=" + city).json()
    if owresponse["cod"] != "404":
        owMainData = owresponse["main"]
        owWindData = owresponse["wind"]
        owSysData = owresponse["sys"]

        # from main data
        curTempK = owMainData["temp"]
        curFeelsLikeK = owMainData["feels_like"]
        tempMinK = owMainData["temp_min"]
        tempMaxK = owMainData["temp_max"]
        curPres = owMainData["pressure"]
        curHumid = owMainData["humidity"]

        # from wind data
        windSpeed = owWindData["speed"]
        windDeg = owWindData["deg"]

        # from sys data
        sunrise = owSysData["sunrise"]
        sunset = owSysData["sunset"]
        owCountry = owSysData["country"]

        # convert current temp from Kelvin to Farenheit
        curTempC = curTempK - 273.15
        curTempF = round(curTempC * ( 9 / 5 ) + 32, 1)

        # - feels like
        curFeelsLikeC = curFeelsLikeK - 273.15
        curFeelsLikeF = round(curFeelsLikeC * ( 9 / 5 ) + 32, 1)

        # - min/max
        tempMinC = tempMinK - 273.15
        tempMaxC = tempMaxK - 273.15
        tempMinF = round(tempMinC * ( 9 / 5 ) + 32, 1)
        tempMaxF = round(tempMaxC * ( 9 / 5 ) + 32, 1)

        if windDeg >= 350 or windDeg <= 10:
            windDir = "North"
        elif windDeg >= 281 and windDeg <= 349:
            windDir = "NW"
        elif windDeg >= 260 and windDeg <= 280:
            windDir = "West" # ey, Sleeping at Last
        elif windDeg >= 191 and windDeg <= 259:
            windDir = "SW"
        elif windDeg >= 170 and windDeg <= 190:
            windDir = "South"
        elif windDeg >= 101 and windDeg <= 169:
            windDir = "SE"
        elif windDeg >= 80 and windDeg <= 100:
            windDir = "East"
        elif windDeg >= 11 and windDeg <= 79:
            windDir = "NE"
        else:
            windDir = windDeg

        weatherDesc = ""
        if curTempF >= 50 and curTempF <= 77: # comfortable temperature
            if curHumid < 60:
                weatherDesc = "Quite nice out! Not too warm, not too cold. Not too humid."
            else:
                weatherDesc = "Oi. Hoomid"
        elif curTempF >= 32 and curTempF <= 49: # chillay
            weatherDesc = "A bit chillay out!"
        elif curTempF < 32: # freezingggg
            weatherDesc = "Ffffrrrreeezzzzzinngggg"
        else:
            weatherDesc = ""

        srTime = time.strftime("%H:%M:%S", time.localtime(sunrise))
        ssTime = time.strftime("%H:%M:%S", time.localtime(sunset))

        msgRasEmbed = discord.Embed(title=weatherDesc, description="", color=0x37ff00)
        msgRasEmbed.set_author(name="Weather for {}, {}".format(city.capitalize(), owCountry))
        msgRasEmbed.add_field(name="Current Temp/Feels Like:", value="{}°F / {}°F".format(curTempF, curFeelsLikeF), inline=True)
#        msgRasEmbed.add_field(name="High/Low:", value="{}°F / {}°F".format(tempMaxF, tempMinF), inline=True) # This was causing incorrect data
        msgRasEmbed.add_field(name="Humidity:", value="{}%".format(curHumid), inline=True)
        msgRasEmbed.add_field(name="Wind Speed/Dir:", value="{} / {}".format(windSpeed, windDir), inline=True)
        msgRasEmbed.add_field(name="Sunrise/Sunset:", value="{} / {}".format(srTime, ssTime), inline=True)

        return msgRasEmbed

@client.event
async def setLocation(discordID, discordUsername, location):
    print(f"[@] {discordUsername} executed b!setlocation with args: {location} and user id {discordID}")
    with db.Weather() as weatherDB:
        try:
            weatherDB.insert_data(discordID, discordUsername, location)
        except db.UniqueException:
            weatherDB.update_data(discordID, discordUsername, location)
            return "Updated your location!"
        return "Added your location! Next time, just execute `b!weather` without the location argument to use your stored location"

@client.event
async def on_ready():
#        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the humans")) # Status set
        await client.change_presence(status=discord.Status.online)
        await presenceChange() # don't look at my horrible code
        print("[@] Connection to Discord established. Bot ready")

@client.event
async def presenceChange():
        presenceWanted = random.randint(1, 9)
        if presenceWanted == 1:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over the humans"))
        elif presenceWanted == 2:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the stars"))
        elif presenceWanted == 3:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your conversations"))
        elif presenceWanted == 4:
            await client.change_presence(activity=discord.Game(name="with LEGOs. Want to join?"))
        elif presenceWanted == 5:
            await client.change_presence(activity=discord.Streaming(name="my MINECRAFT LP SMP EPISODE 2!!!", url="https://twitch.tv/"))
        elif presenceWanted == 6:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="a movie"))
        elif presenceWanted == 7:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="The Office. Good show"))
        elif presenceWanted == 8:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the sunset"))
        elif presenceWanted == 9:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="moosic"))
        print("[@] Presence changed to state %s" % str(presenceWanted))

@client.event
async def on_message(message):
        if message.author == client.user:
            return

        if message.content.upper() == ('B!HELP'): ## Help message
            print("[@] " + str(message.author) + " - executed help command")
            await message.channel.send(helpMessage)

        if message.content.upper().startswith('B!LYRICSFOR') or message.content.upper().startswith('B!LF'): ## Lyrics for command
            userID = message.author.id
            if message.content.find("-") == -1:
                await message.channel.send("Sorry <@%s>, please specify an artist and song. ex: `b!lf Sleeping at Last - Two`" % userID)
                print("[@] " + str(message.author) + " - executed lyricsfor command with an arg error")
            else:
                print("[@] " + str(message.author) + " - executed lyricsfor command with args")
                args = message.content.lower().replace("b!lyricsfor","").replace("b!lf", "").lstrip().rstrip().split("-")
                a = args[0].lstrip().rstrip()
                # You can set aliases here, if you'd like
                if a == "sal":
                    a = "Sleeping at Last"
                s = args[1].lstrip().rstrip()
                await message.channel.send("Searching for the lyrics to *{}* by *{}*...".format(s,a))
                genius = True
                az = False
                try:
                    await message.channel.send(await getLyricsFor(a, s, message))
                except Exception as e:
                    genius = False
                    az = True
                    await message.channel.send(f"Something didn't work right when attempting to send to Discord. Most likely Genius returned junk instead of the lyrics you were expecting. This seach query will most likely return this same message\n```{e}```")
                    pass
                if az:
                    wd = az_lyrics(s, a)
                    uwd = ""
                    for line in wd:
                        uwd += line
                    if uwd == "Error":
                        print(f"[W] AZLyrics fallback command from {userID} failed. No lyrics gathered")
                        await message.channel.send(f"Could not find lyrics for *{s}* by *{a}*")
                    else:
                        await message.channel.send(f"AZLyrics fallback result:\n**{a} - {s}**\n```{uwd}```")

        if message.content.upper().startswith('B!G') or message.content.upper().startswith('B!GENIUS'): # get Genius URL
            userID = message.author.id
            if message.content.find("-") == -1:
                await message.channel.send("Sorry <@%s>, please specify an artist and song. ex: `b!lf Sleeping at Last - Two`" % userID)
                print("[@] " + str(message.author) + " - executed lyricsfor command with an arg error")
            else:
                print("[@] " + str(message.author) + " - executed lyricsfor command with args")
                args = message.content.lower().replace("b!g","").replace("b!genius", "").lstrip().rstrip().split("-")
                a = args[0].lstrip().rstrip()
                s = args[1].lstrip().rstrip()
                try:
                    await message.channel.send("Getting URL for *{}* by *{}*...".format(s,a))
                    song = gapi.search_song(s, a)
                except Exception as e:
                    print("[!] Failed to execute Genius API for %s \n" % str(message.author) + str(e))
                    await message.channel.send("Failed to execute Genius API search\n```" + str(e) + "```")
                    return
                if song:
                    await message.channel.send(str(song.url))
                else:
                    print("[W] No results for {} by {} executed by {}".format(s, a, userID))
                    await message.channel.send("No results for {} by {}".format(s, a))

        if message.content.upper().startswith('B!WEATHER') or message.content.upper().startswith('B!W'): ## get Weather
            userID = message.author.id
            if message.content.find(" ") == -1:
                # if userID has location stored: # incomplete code
                #   get weather
                # else:
                with db.Weather() as weatherDB:
                    try:
                        location = weatherDB.select_data(userID)
                    except db.QueryFailed:
                        await message.channel.send("Sorry <@%s>, we couldn't find you in the database. Please specify a city or ZIP code, or set your location with `b!setlocation`" % userID)
                        print("[@] " + str(message.author) + " - executed getWeatherForCity command but was not found in database")
                        return
                    await message.channel.send("Getting weather for `{}`...".format(location))
                    print("[@] " + str(message.author) + " - executed getWeatherForCity command without args")
                    try:
                        await message.channel.send(embed=await getWeatherForCity(location, message))
                    except Exception as e:
                            await message.channel.send("Could not get weather\n```" + str(e) + "```")

            else:
                print("[@] " + str(message.author) + " - executed getWeatherForCity command")
                args = message.content.lower().replace("b!weather", "").replace("b!w", "").lstrip().rstrip()
                await message.channel.send("Getting weather for `{}`...".format(args.capitalize()))
                #e = ""
                try:
                    await message.channel.send(embed=await getWeatherForCity(args, message))
                except Exception as e:
                    await message.channel.send("Could not get weather\n```" + str(e) + "```")

        if message.content.upper().startswith('B!SETLOCATION') or message.content.upper().startswith('B!SL'): # set location for weather
            userID = message.author.id
            if message.content.find(" ") == -1:
                await message.channel.send("Sorry <@%s>, please specify a city or ZIP code" % userID)
                print("[@] " + str(message.author) + " - executed setlocation command with an arg error")
            else:
                print("[@] " + str(message.author) + " - executed setlocation command")
                args = message.content.lower().replace("b!setlocation", "").replace("b!sl", "").lstrip().rstrip()
                await message.channel.send(await setLocation(discordID=userID, discordUsername=str(message.author)[:-5], location=args))

        if "Chuu" in str(message.author): # Check if we can link a Genius link from Chuu's !lyrics command. Checks if it is an embed
            # find song from embed author
            try:
                embed = message.embeds[0].to_dict()
            except:
                pass
            if 'embed' in locals(): # this stupid code causing trouble
                if "Lyrics found for" in str(embed.get("footer")):
                    print("Lyrics command return detected")
                    print("[@] Attempting to append Genius URL...")
                    args = str(embed['author']['name']).lstrip().rstrip().split("-")
                    a = args[0].lstrip().rstrip()
                    s = args[1].lstrip().rstrip()
                    try:
                        song = gapi.search_song(s, a)
                    except Exception as e:
                        print("[!] Failed to execute Genius API: %s \n" % str(e))
                        await message.channel.send(f"Could not fetch a Genius link for the song: *{embed['author']['name']}*\n```{str(e)}```")
                        return
                    if song:
                        geniusEmbed = discord.Embed(title=embed['author']['name'], url=song.url, description="Link to Genius page")
                        if (random.randint(0, 3) == 0):
                            geniusEmbed.set_footer(text="Still better than that other bot...")
                        await message.channel.send(embed=geniusEmbed)
                    else:
                        print(f"[W] No results for {s} by {a} from Overseer")
                        await message.channel.send(f"Could not find a Genius link for *{embed['author']['name']}* ")

        if message.content.upper().startswith('QB!INFO'):
            userID = message.author.id
            print(f"[@] {userID} requested QBT info")
            await message.channel.send(embed=await getQbtAppInfo())

        if message.content.upper().startswith('QB!ALL'):
            userID = message.author.id
            qbMsg = await getQbtAllTorrents()

            chunkLen = 1994
            chunks = [qbMsg[i:i+chunkLen ] for i in range(0, len(qbMsg), chunkLen)]
            for chunk in chunks:
                await message.channel.send("```" + chunk + "```")

        if message.content.upper().startswith('R!INFO'):
            userID = message.author.id
            await message.channel.send(embed=await getRadarrInfo())

        if message.content.upper().startswith('R!GET'):
            userID = message.author.id
            tmdb = ''
            if len(message.content) < 6:
                await message.channel.send("Missing TMDB ID. Cannot execute without TMDB ID!")
                print("[@] " + str(message.author) + " - executed radarrGet command with arg error")
            else:
                tmdb = str(message.content.lower().replace("r!get", "").replace("r!g", "").lstrip().rstrip())
                print(tmdb)
                await message.channel.send(embed=await getRadarrMovies(tmdb))

        if message.content.upper().startswith('B!PING'):
            await message.channel.send(f"Pong! {math.trunc(client.latency*1000)}ms")

def handleExit(): # I hate this
    client.change_presence(status=discord.Status.offline)
    client.logout()
    client.close()
    print("Disconnected")

#loop = asyncio.get_event_loop() # I hate all of this. Why can't we handle exits gracefully
#loop.run_until_complete(handleExit())
#signal.signal(signal.SIGINT, handleExit)
#signal.signal(signal.SIGTERM, handleExit)

print("Attempting to connect to Discord...")
try:
    client.run(config_sample.TOKEN)
except: # sigh
    print("Caught KeyboardInterrupt")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.change_presence(status=discord.Status.offline))
    print("Set offline")
    client.logout()
    client.close()
    print("Disconnected")
#except Exception as e:
#    print(f"[!] Failed to connect to Discord: {e}")
