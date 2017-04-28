from flask import Flask,request,jsonify
from QueryResults import QueryResults
import time

app = Flask(__name__)

@app.route('/')
def searchQuery():
	query = request.args.get("q","")
	if not query:
		return "Please pass query parameter"
	else:
		queryObj = QueryResults(query)
		result = jsonify(queryObj.getQueryResults())
		return result
		

if __name__ == "__main__":
	app.run(debug=True)