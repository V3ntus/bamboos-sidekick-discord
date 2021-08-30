# bamboos-sidekick-discord
### Multipurpose Discord bot (Genius lyrics, qBitTorrent, Radarr, Weather, etc.)

#### Functions:
* Can grab lyrics and other resources from Genius
* Can interface with a local qBitTorrent instance to grab a list of active torrents and such
* Can interface with Radarr and TMDB
* Can grab weather for specific cities and postal codes

### Bot commands:
**Genius Commands**:  
`b!lyricsfor / b!lf (artist) - (song)` = Get lyrics from Genius for specified song  
`b!genius / b!g (artist) - (song)` = Get a Genius page link for a song  
  
**Weather Commands**:  
`b!setlocation (city/ZIP)` = Set your user's location  
`b!weather [city/ZIP]` = Get location. Requires city/ZIP if you have not set your location  
  
**qBitTorrent Local Commands**  
`qb!info` = request qBitTorrent info for specified host on my LAN  
`qb!all` = get all torrent info for specified host on my LAN  
  
**Radarr Local Commands**  
`r!info` = get info for Radarr instance for specified host on my LAN  
`r!get (tmdb)` = get info for a specific movie using a TMDB ID number  
  
This bot also listens for certain phrases and the Chuu bot to provide lyrics passively.  

---

## Setup
#### Requires:  

**Python Version:**  
Python 3.7+ (may work on older versions, but was coded and tested in 3.7 and 3.9)  
**Python Modules:**  
```
discord
lyricsgenius
openweather
requests
qbittorrent-api
azlyrics
```  
# 1.  
**Install dependencies**  
```
pip3 install discord lyricsgenius openweather requests qbittorrent-api azlyrics
```
*or*  
```
pip3 install -r requirements.txt
```
# 2.  
Copy the [config_sample.py.sample](https://github.com/V3ntus/bamboos-sidekick-discord/blob/main/config_sample.py.sample) to a usable python script:  
```
cp config_sample.py.sample config_sample.py
```
Edit this new file and add your API keys and other configuration values:  
```
nano config_sample.py
```
Here are links and info for relevant API and configuration:  
* [Discord](https://discord.com/developers) ([Discord Bot Token Guide](https://realpython.com/how-to-make-a-discord-bot-python/#creating-an-application))
* [Genius](https://genius.com/api-clients)
* [OpenWeather](https://home.openweathermap.org/api_keys)
* [Radarr](https://www.home-assistant.io/integrations/radarr/#api_key) (found in Settings > General of the Radarr server web UI)
* [TMDB](https://www.themoviedb.org/settings/api)
* `EXT_HOST` = IP or hostname of machine hosting qBittorrent and Radarr
* `QBIT_USER` = Username of qBitTorrent web UI (You may need to [enable the web UI](https://lgallardo.com/2014/09/29/como-activar-la-interfaz-web-de-qbittorrent/), if not already enabled)
* `QBIT_PASS` = If you set one in the web UI, please set it here
* `QBIT_PORT` = If you changed the port where the qBTT web server listens, please specify it here. Otherwise, leave this as is.
* `rhost` = If Radarr is listening on a different IP or machine, you may set it here
* `rport` = If you changed the port where the Radarr web server listens, please specify it here. Otherwise, leave this as is  
# 3.  
That's all! You may now run the bot using  
```
python3 bot.py
```

---



## TODO:
* Need to add more qBTT functions. It's pretty boring
* ^ Radarr as well
* The weather system might need to be revamped
