import html
import json
from getpass import getpass
from pprint import pprint

import requests
from bs4 import BeautifulSoup


class VKError(Exception):
    pass

def _parse_tracks(tracks_html):
    tracks = []
    for track in tracks_html:
        cover = track.find(class_="ai_play")["style"].split("background-image:url(")
        if len(cover) > 1:
            cover = cover[1].split(")")[0]
        else:
            cover = None
        tracks.append({
            "cover":cover,
            "duration":track.find(class_="ai_dur")["data-dur"],
            "artist":track.find(class_="ai_artist").text,
            "title":track.find(class_="ai_title").text,
            "url":track.input["value"],
            "mgmtid":track.parent["onclick"].split("'")[1],
        })
    return tracks

def audio_get(cookie, query=None, offset=0, no_remixes=False, playlist="/audios0"):
    if query:
        params = {
            "q":query,
            "offset":offset,
            "act":"search"
        }
    else:
        params = {}
    r = requests.get("https://m.vk.com" + playlist,
                     cookies={"remixsid":cookie},
                     params=params
                     )
    if r.status_code != 200:
        raise VKError("Сервер вконтакте вернул код, который не 200:%s" % r.status_code)
    soup = BeautifulSoup(r.text, 'html5lib')
    playlists = [{"name":"Все треки", "url":"/audios0"}]
    tracks = []
    pages = soup.find(class_="pagination")
    if pages:
        tracks += _parse_tracks(soup.find_all(class_="ai_info"))
        last_offset = 50 # Fallback value
        for page in pages.find_all(class_="pg_link"):
            if page.text == "»":
                last_offset = int(page["href"].split("offset=")[-1])
        offset = 50
        while offset != (last_offset + 50):
            params["offset"] = offset
            params["id"] = uid
            r = requests.get("https://m.vk.com/audio?id=0&offset=350",
                    cookies={"remixsid":cookie},
                    params=params
            )
            tracks += _parse_tracks(BeautifulSoup(r.text, 'html5lib').find_all(class_="ai_info"))
            offset += 50
    else:
        tracks += _parse_tracks(soup.find_all(class_="ai_info"))
    for playlist in soup.find_all(class_="al_playlist"):
        playlists.append({"name":playlist.find(class_="audioPlaylists__itemTitle").text, "url":playlist["href"]})
    if no_remixes:
        for track in tracks:
            if "remix" in track["title"].lower() or "remix" in track["artist"].lower():
                print("Found remix.")
                tracks.remove(track)
    return tracks, playlists

def track_mgmt(act,cookie, trackid):
    hashes = requests.get("https://m.vk.com/audio",
                     cookies={"remixsid":cookie, "remixmdevice":"1920/1080/1/!!-!!!!"}).text
    hashes = json.loads(hashes.split("audioplayer.init(")[1].split(")")[0])
    if act == "delete":
        acthash = hashes["del_hash"]
    else:
        acthash = hashes[act+"_hash"]
    requests.post("https://m.vk.com/audio", 
    cookies={
        "remixsid":cookie,
    },
    data={
        "act":act,
        "_ajax":"1",
        "hash":acthash,
        "audio":trackid
    })

