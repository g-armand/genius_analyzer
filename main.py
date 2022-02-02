# -*- coding: utf-8 -*- 

#All along this program we need to specify the encoding as utf-8

#TODO: 
#
#

#libraries:
from bs4 import BeautifulSoup as Bs #html_text cleaning
import requests as r				#making html requests, and using genius' API
import os							#working with files


#link = str(the full link to the genius.com page)
#name = str(artist's name)
#title = str(title of the song)
#index = int(just a counter)
def write_file(name, title, clean_text):
	"""
	When called, this function manages the text storage for a song.
	Does not return anything.
	"""

	#make a new directory to store songs
	if os.path.isdir(name) == False:
		os.mkdir(name)

	#make a new file for each song
	path = os.getcwd() + f"/{name}"
	path = path.replace("\\", "/")
	file_name_path = f"{path}/{name}_{title}.txt"
	with open(file_name_path, 'w', encoding = 'utf-8') as f:
		f.write(clean_text)

#link: str(the genius.com link to the song)
def get_right_version(link):
	"""
	when called, this function checks for the right version (that does not contains key_word)
	by making (max 10) requests to retrieve the html text.
	returns str(the whole html text), or "None" if not possible to find right version
	"""

	#double factors to check for right version of html text
	#bad_version will switch to False if right version is found...
	#count avoids an infinite loop, by allowing only 10 requests
	bad_version = True
	count = 0
	while bad_version == True and count < 10:

		#html text retrieval
		texte = r.get(link)
		texte.encoding = "utf-8"
		html_text = texte.text

		#when the string in key_word is in the html text, the final text is not well cleaned
		#because beautiful soup does not handle well json files
		key_word = "window.__PRELOADED_STATE__ = JSON.parse"

		bad_version = key_word not in html_text
		#management of wrong format cases
		if bad_version:
			count += 1
		if "Lyrics for this song have yet to be released." in html_text:
			return "None"
	if count >=10:
		return None

	return html_text

#text: str(html_text)
def clean_and_format(text):
	"""
	when called, cleans the html text and makes it look unified
	returns that clean text
	"""
	if text == "None":
		return "None"
	#let's just cut the not useful parts of this text...
	#the start...
	i = 0
	while i < len(text):
		if text[i:i+39] in """window.__PRELOADED_STATE__ = JSON.parse""":
			text = text[i:]
			break
		i += 1

	i = 0
	while i < len(text):
		if text[i:i+33] in """lyricsData\\":{\\"body\\":{\\"html\\":\\"<p>[""":
			text = text[i:]
			break
		i += 1

	#...and the end
	i = 0
	while i < len(text):        
		if  text[i:i+30] == """,\\"children\\":[{\\"children\\":[""":
			text = text[:i]
			break
		i+=1

	#BeautifulSoup is wonderful
	soup = Bs(text, features="html.parser")

	soup.p.encode('utf-8')
	lyrics = soup.get_text()
	lyrics = lyrics.replace("<\\/a>", "")
	lyrics = lyrics.replace("<\\/i>", "")
	lyrics = lyrics.replace("<\\/p>", "")
	lyrics = lyrics.replace(r"\\n", "\n")
	lyrics = lyrics.replace("\\", "")

	#removing first line
	lyrics = lyrics.strip()
	lyrics = lyrics.split("\n")
	lyrics = lyrics[1:]
	lyrics = "\n".join(lyrics)

	return lyrics.strip()


#text:(str(clean text))
def tokenize(text):
	"""tokenization line by line and then word by word"""

	liste_tokens = []

	#working on lines
	liste_lines = text.split("\n")
	print(liste_lines[0])
	#working on words
	for line in liste_lines:
		liste_tokens.extend(line.split(" "))

	return liste_tokens


def get_keys():

	#retirieving keys for api from api_keys.py
	with open("api_keys.py", "r") as file:
		api_keys = file.read()
	api_keys = api_keys.split("\n")

	dict_api_keys = {}
	dict_api_keys[str(api_keys[0])] = str(api_keys[1])
	dict_api_keys[str(api_keys[2])] = str(api_keys[3])
	dict_api_keys[str(api_keys[4])] = str(api_keys[5])

	return dict_api_keys

#search_term: str(artist's name)
def get_artist_id(search_term):
	"""
	when called, uses genius' API to get artist's ID
	search term as to be striped, case does not matter
	"""
	#variable initialization  
	dict_api_keys = get_keys()
	querystring = {"access_token" : dict_api_keys["token"]}

	#requesting genius' API, querystring is mandatory to access it
	request_url = f"http://api.genius.com/search?q={search_term}"
	response = r.request("GET", request_url, params = querystring)
	json_response = response.json()
	artist_id = int()

	#finding artist's ID
	for id in json_response['response']['hits']:
		if id['result']['primary_artist']['name'].upper() in search_term.upper():
			artist_id = id['result']['primary_artist']['id']

	return artist_id

#artist_id: int(obtained from get_artist_id())
def get_artist_songs(artist_id):
	"""
	when called, uses genius' API to get all songs from artist_id
	"""

	#variable initialization
	dict_api_keys = get_keys()
	querystring = {"access_token":dict_api_keys["token"], "per_page" : 50, 'page' :1}
	request_url = f"http://api.genius.com/artists/{artist_id}/songs"
	all_songs = []

	#to replace by bool(first request)
	#first request
	response = r.request("GET", request_url, params = querystring)
	json_response = response.json()
	for song in json_response['response']['songs']:
		all_songs.append(song['title'])
		print(song['title'])
	#going to next page
	querystring['page'] = json_response['response']['next_page']

	#[next_page] contains an integer if there is next page of songs, None otherwise
	while json_response['response']['next_page'] != None:

		#repeat the process as many times as there is another next page available
		response = r.request("GET", request_url, params = querystring)
		json_response = response.json()

		#append songs to all_songs list
		for song in json_response['response']['songs']:
			all_songs.append(song['title'])
			print(song['title'])
		
		#going to next page
		querystring['page'] = json_response['response']['next_page']
	
	return all_songs

#songs: list(all songs obtained with get_artist_songs())
#artist_name: str()
def get_clean_titles_and_text(title, artist_name):
	"""
	when called, will turn song title into its url format, for each song in songs.
	it is then combined with artist_name to create the final genius url.
	the url is then requested and if response == 200: the song's url is used to retrieve a clean text with get_clean_text()
	does not return anything
	"""

	#variable initialization

	artist_name = artist_name.replace(' ', '-')

	#replacing every character with their corresponding character


	title = title.replace('é', 'e')
	title = title.replace('è', 'e')
	title = title.replace('ê', 'e')
	title = title.replace('ë', 'e')
	title = title.replace('à', 'a')
	title = title.replace('â', 'a')
	title = title.replace('ï', 'i')
	title = title.replace('î', 'i')
	title = title.replace('ù', 'u')
	title = title.replace('û', 'u')
	title = title.replace('ô', 'o')
	title = title.replace('À', 'a')
	title = title.replace('ç', 'c')
	title = title.replace('Ç', 'c')
	title = title.replace('ñ', 'n')
	title = title.replace('/', "")

	for i, elt in enumerate(title):
		if elt not in " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890":
			title = title.replace(elt, "")
		
	#some titles have a weird format...		
	title = title.replace('   ', '-')
	title = title.replace('  ', '-')
	title = title.replace(' ', '-')

	if len(title) >= 1 and title[-1] == '-':
		title = title[:-1]

	url = f"https://genius.com/{artist_name}-{title}-lyrics"

	#making request, append title and url if working
	request = r.get(url)

	if request.status_code != 200:
		return None, None

	elif request.status_code == 200:
		#call the get_right_version() function to get a clean text from genius.com
		text = get_right_version(url)
		if text == "None":
			return None, None
		elif text:
			#cleaning of the html text
			clean_text = clean_and_format(text)
			print('cleaning done')
			return clean_text, title
		else:
			return None, None

#search_term: str(artist's name)
def main(search_term):
	"""
	main function, calls the functions defined above
	retrieve artist's ID, the working songs and corresponding urls
	eventually calls write_file() to store all texts in files
	"""

	#find artist's id
	artist_id = get_artist_id(search_term)
	if artist_id == 0:
		print("Unable to find artist's ID...")
		return(None)

	print(f"artist's ID ({artist_id}) retrieved succesfully !")

	#find all songs
	all_songs = get_artist_songs(artist_id)
	print(f"{len(all_songs)} songs retrieved")

	#work on each song
	for song in all_songs:
		#retrieve text
		clean_text, title = get_clean_titles_and_text(song, search_term)
		if clean_text == None:
			pass
		else:
			#write a song.txt file for each working song 
			search_term = search_term.replace(" ", "-")
			write_file(search_term, title, clean_text)
			print(title, 'writing done')

