'''
Lambda function to perform checking on vote based on article_id provided by client.
'''
from os import environ
import json
import logging
import boto3
from boto3.dynamodb.conditions import Key
from cerberus import Validator

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def response_proxy(data):
	'''
	For HTTP status codes, you can take a look at https://httpstatuses.com/
	'''
	response = {}
	response["isBase64Encoded"] = False
	response["statusCode"] = data["statusCode"]
	response["headers"] = {}
	if "headers" in data:
		response["headers"] = data["headers"]
	response["body"] = json.dumps(data["body"])
	return response

def request_proxy(data):
	'''
	Request proxy function
	'''
	try:
		request = {}
		request = data
		request["body"] = json.loads(data["body"])
	except Exception as e:
		logger.error(e)
	return request

def lambda_handler(event, context):
	'''
	Normalize the request and response
	'''
	response = {}
	try:                
		request = request_proxy(event)
		logger.info("Validating request")
		logger.info(request["body"])
		if not validate_request(request["body"]):
			response["statusCode"] = 400
			response["body"] = {}
			return response_proxy(response)

		logger.info("Checking to DB")
		total_vote = vote_check_db(request["body"]["poll_id"])

		response["statusCode"] = 200
		response["headers"]={}
		response["headers"]["Access-Control-Allow-Origin"]="*"        
		response["body"] = {}
		response["body"]["votes"] = total_vote
	except Exception as e:
		logger.error(e)
		response["statusCode"] = 500
		response["body"] = {}
	return response_proxy(response)

def validate_request(data):
	'''
	Challenge the data request with the validation scheme using Cerberus
	'''
	schema = {'poll_id':{'type':'string', 'maxlength':100, 'required': True}}
	validator = Validator(schema)
	if validator.validate(data):
		return True
	logger.error('Request did not pass validation.')
	return False

def vote_check_db(poll_id):
	'''
	Check to database
	'''
	try:
		dynamodb = boto3.resource('dynamodb')
		table = dynamodb.Table(environ["DB_VOTE_SCORE"])
		response = table.query(
			IndexName="poll_ID_index",
			Select="ALL_ATTRIBUTES",
			KeyConditionExpression=Key('poll_ID').eq(poll_id),
		)
		logger.info(response)
		if "Items" not in response:
			return []
		else:
			data = {}
			for item in response["Items"]:
				if item["item_ID"] in data:
					data[item["item_ID"]] += 1
				else:
					data[item["item_ID"]] = 1
			logger.info(data)
			return data
	except Exception as e:
		logger.info(e)
		logger.error(e)
		return 0
