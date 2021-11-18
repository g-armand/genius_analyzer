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
def write_file(link, name, title, index):
	"""
	When called, this function manages the html text retrieval, text cleaning and text storage for a song.
	Does not return anything.
	"""
	
	#call the get_right_version() function to get a clean text from genius.com
	html_text = get_right_version(link)

	#in case the clean text couldn't get retrieved from genius,
	#we return None, and we let it know to the user
	if html_text == "None":
		print(f"{title}, n'a rien donné.")
		return None

	#cleaning of the html text
	clean_text = clean_and_format(html_text)

	#make a new directory to store songs
	if os.path.isdir(name) == False:
		os.mkdir(name)

	#make a new file for each song
	path = f"C:/Users/HP/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Python 3.10/prog/genius analyzer/{name}"
	file_name_path = f"{path}/{name}_{title}.txt"
	with open(file_name_path, 'w', encoding = 'utf-8') as f:
		f.write(clean_text)

	print(index) #can get erased

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
		bad_version = key_word in html_text

		#management of wrong format cases
		if bad_version:
			count += 1
		if "Lyrics for this song have yet to be released." in html_text:
			return "None"
	if count >=10:
		return "None"

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
		if text[i:i+34] in """<div initial-content-for="lyrics">""":
			text = text[i:]
			break
		i += 1

	#...and the end
	i = 0
	while i < len(text):
		if  text[i:i+48] == """<div initial-content-for="recirculated_content">""":
			text = text[:i]
			break
		i+=1
	
	#BeautifulSoup is wonderful
	soup = Bs(text, features="html.parser")
	soup.p.encode('utf-8')
	lyrics = soup.get_text()

	return lyrics.strip()

#text:(str(clean text))
def tokenize(text):
	"""tokenization line by line and then word by word"""

	liste_tokens = []

	#working on lines
	liste_lines = text.split("\n")

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

	print(json_response)
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
def get_clean_titles(songs, artist_name):
	"""
	when called, will turn song title into its url format, for each song in songs.
	it is then combined with artist_name to create the final genius url.
	the url is then requested and if response == 200: the song's url is added to liste_url
	returns a list of all working songs, and a list of their corresponding urls
	"""

	#variable initialization
	working_songs = []
	liste_url = []
	artist_name = artist_name.replace(' ', '-')

	#replacing every character with their corresponding character
	for index, title in enumerate(songs):

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
		if request.status_code == 200:
			print(title)
			working_songs.append(title)
			liste_url.append(url)
			
	return working_songs, liste_url

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

	print(f"artist's ID ({artist_id})retrieved succesfully !")

	#find all songs
	all_songs = get_artist_songs(artist_id)
	print(f"{len(all_songs)} songs retrieved")

	#find all working songs
	working_songs, liste_url = get_clean_titles(all_songs, search_term)

	#write a song.txt file for each working song 
	for index, url in enumerate(liste_url):
		write_file(url, search_term, working_songs[index], index)


#main('sofiane')

a,b,c = int(), int(),int()