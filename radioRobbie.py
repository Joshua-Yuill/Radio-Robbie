from __future__ import print_function
import discord
from discord.ext import commands
import re
import struct
import urllib.request as urllib2
import csv
import requests as r

intents=discord.Intents.all()

bot = commands.Bot(command_prefix='?', intents=intents)

radioSource = "http://media-ice.musicradio.com/CapitalMP3"

stationName = []
stationFreq = []
stationLocation = []
stationUrl = []
with open('stationList.csv') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
        else:
            stationName.append(row[0])
            stationFreq.append(row[1])
            stationLocation.append(row[3])
            stationUrl.append(row[2])
            line_count += 1


tokens = open('tokens.txt').readlines() 

#Spotify Access Token Getter
try:
    client_id = "6159b0c7d8bc4c159a13b2d56461243b"
    client_secret = "0fc0dee3c45249f0ad6694c865caf703"

    auth_url = 'https://accounts.spotify.com/api/token'

    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
    }

    auth_response = r.post(auth_url, data=data)

    access_token = auth_response.json().get('access_token')
    print("Spotify Token Acquired: " + access_token)
except:
    print("Unable to get Spotify token")

# - - - - - 

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game('The Radio'))

    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    await bot.tree.sync()

@bot.command()
async def join(ctx):
    try:
        channel = ctx.author.voice.channel
        global vc
        vc = await channel.connect(self_deaf=True)
        vc.play(discord.FFmpegPCMAudio(executable="E:/Downloads/ffmpeg-master-latest-win64-gpl/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe",source=radioSource, options=""))
    except:
        await ctx.send("You need to be in a voice channel to use this feature")

@bot.command(pass_context=True)
async def station(ctx, num:int = 0):
    global radioSource
    
    try:
        if num > 0:
            radioSource = str(stationUrl[(num - 1)])
            await ctx.send(f"Changed station to **{stationName[(num - 1)]} - {stationFreq[(num - 1)]}**")
            ctx.voice_client.stop()
            vc.play(discord.FFmpegPCMAudio(executable="E:/Downloads/ffmpeg-master-latest-win64-gpl/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe",source=radioSource, options=""))

        else:
            message = ""
            for i in stationName:
                holding = ((str(stationName.index(i))) + ". **" + (str(i)) + " - " + (str(stationFreq[stationName.index(i)])) + " - " + (str(stationLocation[stationName.index(i)])) + "**\n")
                message = message + holding
            message = message + "\n\nTo change station use **?station [number]**\t Example: **?station 1**"
            await ctx.send(message)
    except:
        await ctx.send("An error has occurred, please try again later [404]")



@bot.command(pass_context=True)
async def song(ctx):
    try:
        global radioSource
        url = radioSource  # radio stream
        encoding = 'latin1' # default: iso-8859-1 for mp3 and utf-8 for ogg streams
        request = urllib2.Request(url, headers={'Icy-MetaData': 1})  # request metadata
        response = urllib2.urlopen(request)
        metaint = int(response.headers['icy-metaint'])
        for _ in range(10): # # title may be empty initially, try several times
            response.read(metaint)  # skip to metadata
            metadata_length = struct.unpack('B', response.read(1))[0] * 16  # length byte
            metadata = response.read(metadata_length).rstrip(b'\0')
            # extract title from the metadata
            m = re.search(br"StreamTitle='([^']*)';", metadata)
            if m:
                title = m.group(1)
                if title:
                    break
        
        songtitle = str(title.decode(encoding, errors='replace'))

        if songtitle == '':
            await ctx.send("There is no song title (This could be because of an ad break or spoken segment)")
        else:
            url = songtitle.replace(" -", "")
            url = url.replace(" ", "+")
            rURL = (f"https://api.spotify.com/v1/search?q={url}&type=track")
            response = r.get(f"https://api.spotify.com/v1/search?q={url}&type=track&offset=0&limit=1", headers = {
        'Authorization': 'Bearer {}'.format(access_token)
    })
            await ctx.send("Current song: **" + songtitle + "**\n**Spotify link**: " + response.json()['tracks']['items'][0]['external_urls']['spotify'])
    except:
        await ctx.send("Unable to get song info for this station")


@bot.command(pass_context=True)
async def wst(ctx):
    global radioSource
    await ctx.send("Current radio: **" + stationName[stationUrl.index(radioSource)] + "**")

@bot.command()
async def stop(ctx):
    ctx.voice_client.stop()


@bot.command()
async def leave(ctx):
    ctx.voice_client.stop()
    await ctx.voice_client.disconnect()
    print(radioSource)

bot.run(tokens[0])