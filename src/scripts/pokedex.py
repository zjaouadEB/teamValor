import requests
import re
from bs4 import BeautifulSoup
from html.parser import HTMLParser
import sys
import traceback
import json
import pymysql

import os.path
import os

from datetime import datetime

def filePutContents(filename, data):
    with open(filename, 'w') as f:
        f.write(data)
        f.close()

USERAGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246' #'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.93 Safari/537.36',class

headers = {
  'User-Agent': USERAGENT,
  'Referer': 'https://pokemondb.net'
}

#DB Credentials
connection = pymysql.connect(
	host='',
	user='',
	password='',
	db='',
	charset='utf8mb4',
	cursorclass=pymysql.cursors.DictCursor
)


mainURL = 'https://pokemondb.net'

def addPokemon(details):
	for detail in details['pokemons']:
		arrParams = {}
		for key in detail.keys():
			paramKey = key.lower()
			reg = re.compile('(\w+).?\s(\w+)')
			if reg.match(paramKey):
				matches = reg.match(key).groups()
				first = matches[0].lower()
				second = matches[1].capitalize()
				tmpKey = first + second
				arrParams[tmpKey] = str(detail[key]).strip()
			elif paramKey == 'national №':
				arrParams['pokeNumber'] = detail[key]
			elif paramKey == 'hp':
				arrParams['health'] = detail[key]
			elif isinstance(detail[key], list):
				paramKey = key.lower()
				arrParams[paramKey] = str(detail[key])
			elif key == 'Local №':
				continue
			elif detail[key] is None:
				arrParams[paramKey] = 'NULL'
			else:
				arrParams[paramKey] = str(detail[key])
		insertPokemon(arrParams)
	connection.close()

def insertPokemon(params):
	try:
		with connection.cursor() as cursor:
			sql = "INSERT INTO `pokemons` (`image`, `name`, `pokeNumber`, `type`, `species`, `height`, `weight`, `abilities`, `evYield`, `catchRate`, `baseFriendship`, `baseExp`, `growthRate`, `eggGroups`, `gender`, `eggCycles`, `health`, `attack`, `defense`, `spAtk`, `spDef`, `speed`, `evolutions`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
			cursor.execute(sql, (
				params['image'],
				params['name'],
				params['pokeNumber'],
				params['type'],
				params['species'],
				params['height'].encode('ascii','ignore'),
				params['weight'].encode('ascii','ignore'),
				params['abilities'],
				params['evYield'],
				params['catchRate'],
				params['baseFriendship'],
				params['baseExp'],
				params['growthRate'],
				params['eggGroups'],
				params['gender'],
				params['eggCycles'],
				params['health'],
				params['attack'],
				params['defense'],
				params['spAtk'],
				params['spDef'],
				params['speed'],
				params['evolutions']
			))
		connection.commit()
		print('Inserted data to DB successful...')
	except Exception as e:
		print('exception happened')
		print(e)
	

def getSession():
	session = requests.session()
	return session

def getPokemonList(session):
	#"https://pokedex.org/"
	#https://pokemondb.net/pokedex/national#gen-1
	url = "https://pokemondb.net/pokedex/game/red-blue-yellow"
	resp = session.get(url, headers=headers)
	htmlResp = resp.content
	soup = BeautifulSoup(htmlResp, "html5lib")
	pokemonNames = []

	# #Find the div tags that contain pokemon details
	pokemonMainDiv = soup.find('div', {'class': 'infocard-list-pkmn-lg'})
	pokemonSpans = pokemonMainDiv.find_all('span', {'class': 'infocard-lg-img'})
	for span in pokemonSpans:
		link = span.find('a').attrs['href']
		#link format
		#/pokedex/chansey
		regex = re.compile('\/pokedex\/(\w+)')
		name = regex.match(link).groups(1)[0]
		pokemonParams = {
		  'link': link,
		  'name': name
		}
		pokemonNames.append(pokemonParams)
	return pokemonNames

def getPokemonDetails(session, pokemonParams):
	details = []
	for pokemon in pokemonParams:
		print(pokemon['name'])
		url = mainURL + pokemon['link']
		resp = session.get(url, headers=headers)
		htmlResp = resp.content
		soup = BeautifulSoup(htmlResp, "html5lib")
		defDiv = soup.find('div', {'class': 'tabs-panel-list'})
		gridRows = defDiv.find_all('div', {'class': 'grid-row'})
		cols = {}
		cols['name'] = pokemon['name']
		count = 0
		for grid in gridRows:
			count += 1
			# print('grid'+str(count))
			subCols = grid.find_all('div', {'class': ['grid-col span-md-6', 'span-lg-4', 'span-md-12', 'span-lg-8']})
			for col in subCols:
				# print(col.attrs['class'])
				if 'text-center' in col.attrs['class']:
					imageLink = col.find('a').attrs['href']
					cols['image'] = imageLink
				elif 'span-md-6' in col.attrs['class'] and 'text-center' not in col.attrs['class']:
					tbody = col.find('tbody')
					rows = tbody.find_all('tr')
					for row in rows:
						header = row.find('th').string
						rowVal = row.find('td')
						value = ""
						if rowVal.string:
							value = rowVal.string
						elif rowVal.find('a'):
							tmpVals = []
							values = rowVal.find_all('a')
							for val in values:
								tmpVals.append(val.text)
							value = tmpVals
						cols[header] = value
				elif 'span-md-12' in col.attrs['class']:
					if 'span-lg-8' in col.attrs['class']:
						tbody = col.find('tbody')
						rows = tbody.find_all('tr')
						for row in rows:
							header = row.find('th').string
							value = row.find('td', {'class': 'cell-num'}).text
							cols[header] = value
					miniGrid = col.find_all('div', {'class': ['grid-col', 'span-md-6,' 'span-lg-12']})
					for subCol in miniGrid:
						tbody = col.find_all('tbody')
						for body in tbody:
							rows = body.find_all('tr')
							for row in rows:
								headerHTMl = row.find('th')
								if headerHTMl.find('a'):
									header = headerHTMl.text
								else:
									header = row.find('th').string
								rowVal = row.find('td')
								value = ""
								if rowVal.string:
									value = rowVal.string
								elif rowVal.find('a'):
									tmpVals = []
									values = rowVal.find_all('a')
									for val in values:
										tmpVals.append(val.text)
									value = tmpVals
								elif rowVal.find('small'):
									value = rowVal.text
								cols[header] = value
		if soup.find('div', {'class': 'infocard-list-evo'}):
			evoGrid = soup.find('div', {'class': 'infocard-list-evo'})
			evoLvlCards = evoGrid.find_all('span', {'class': 'infocard-arrow'})
			evoCards = evoGrid.find_all('div', {'class': 'infocard'})
			levels = []
			evolutions = {}
			for lvl in evoLvlCards:
				level = lvl.text.strip('(Level ')
				level = level.strip(')')
				levels.append(level)
			for index, evoCard in enumerate(evoCards):
				evolution = {}
				name = evoCard.find('a', {'class': 'ent-name'}).text
				if index > 0:
					evolution['name'] = name
					evolution['lvl'] = 0
					evolutions[name] = evolution
			for index, evolution in enumerate(evolutions):
				print(evolution)
				evolutions[evolution]['lvl'] = levels[index]
			cols['evolutions'] = evolutions
			details.append(cols)
		else:
			cols['evolutions'] = None
			details.append(cols)
	pokemons = {
	    'pokemons': details
	}
	return pokemons

### MAIN ###
if __name__ == "__main__":
	print('Script to populate DB with pokemon info')
	#### If you want to scrape a site and get the most recent data if any changes occured###
	session = getSession()
	pokemonParams = getPokemonList(session)
	details = getPokemonDetails(session, pokemonParams)

	# with open('pokemon.json', 'w') as outfile:
	# 	json.dump(details, outfile)

	### We have prepared a recent list of pokemon details for you ###
	# with open('pokemon.json') as f:
	# 	details = json.load(f)

	#Add pokemon details to DB
	#STUB
	# test = addPokemon(details)
	# print(test)
	#LIVE
	addPokemon(details)

	# print('Go check the json file pokemon.json for further testing')
	# filePutContents('test.html', str(details))




#Put pokemon details into dict
#add pokemon to DB
#Test SELECT DB action with user credentials given
