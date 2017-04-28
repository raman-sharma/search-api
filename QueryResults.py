from concurrent import futures
import requests
import json
import urllib.parse
from requests_oauthlib import OAuth1

class QueryResults():
	# class variable that contains list of all sources to query from 
	queryTerm=''
	searchResults = {}
	urls = []
	googleConf={}
	twitterConf={}
	def __init__(self,queryTerm):
		self.queryTerm = queryTerm
		with open('config/config.json') as conf:
			data = json.load(conf)
		self.googleConf = data['google']
		self.twitterConf = data['twitter']
		query=urllib.parse.quote(self.queryTerm)
		self.urls.append("http://api.duckduckgo.com/?q={query}&format=json".format(query=query))
		self.urls.append("https://www.googleapis.com/customsearch/v1?key={key}&cx=017576662512468239146:omuauf_lfve&q={query}".format(
               	     key=self.googleConf['apiKey'], query=query))
		self.urls.append("https://api.twitter.com/1.1/search/tweets.json?q={query}".format(query=query))

	def getSearchEndpoint(self,url):
		if url.find('duckduckgo')!=-1:
			return 'DuckDuckGo'
		elif url.find('googleapis')!= -1:
			return 'Google'
		return 'Twitter'


	def getUrlResult(self,url,timeout):
		if url.find('twitter') != -1:
			oauth = OAuth1(self.twitterConf['CONSUMER_KEY'],
                client_secret=self.twitterConf['CONSUMER_SECRET'],
                resource_owner_key=self.twitterConf['OAUTH_TOKEN'],
                resource_owner_secret=self.twitterConf['OAUTH_TOKEN_SECRET'])
			return requests.get(url,timeout=timeout, auth=oauth)
		return requests.get(url,timeout=timeout)

	def getQueryResults(self):
		self.searchResults['query'] = self.queryTerm
		# Add twitter also
		with futures.ThreadPoolExecutor(max_workers=4) as executor:
			future_to_url = {executor.submit(self.getUrlResult, url, 1): url for url in self.urls}
			for future in  futures.as_completed(future_to_url):
				searchEndpoint = self.getSearchEndpoint(future_to_url[future])
				try:
					data = future.result()
					if(searchEndpoint=='DuckDuckGo'):
						self.searchResults[searchEndpoint] = self.getDuckDuckGoResults(data)
					elif (searchEndpoint == 'Google'):
						self.searchResults[searchEndpoint] = self.getGoogleResults(data)
					else:
						self.searchResults[searchEndpoint] = self.getTwitterResults(data)
				except requests.exceptions.Timeout:
					self.searchResults[searchEndpoint] = "Request Timeout Error"

		return self.searchResults

	def getDuckDuckGoResults(self,r):
		results={}
		if r.status_code == 200:
			result = r.json()
			if len(result['RelatedTopics'])>0:
				content = result['RelatedTopics'][0]
				results['url'] = content['FirstURL']
				results['text'] = content['Text']
			else:
				results['message'] = "No results"
		else:
			results['message'] = "Failed to retreive data"
		return results

	def getGoogleResults(self,r):
		results={}
		if r.status_code == 200:
			result = r.json()
			if(len(result['items'])>0):
				content = result['items'][0]
				results['url'] = content['link']
				results['text'] = content['snippet']
			else:
				results['message'] = "No results"
		else:
			results['message'] = "Failed to retreive data"
		return results

	def getTwitterResults(self,r):
		results={}
		if r.status_code == 200:
			result = r.json()
			if(len(result['statuses'])>0):
				content = result['statuses'][0]
				results['text'] = content['text']
			else:
				results['message'] = "No results"
		else:
			results['message'] = "Failed to retreive data"
		return results
