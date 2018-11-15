import os
import json
import logging
import boto3
from cerberus import Validator
import hashlib

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
	request = {}
	request = data
	request["body"]=json.loads(data["body"])
	return request

def lambda_handler(event, context):
	response = {}
	try:
		request = request_proxy(event)
		logger.info("Validating request")
		if not validate_request(request["body"]):
			response["statusCode"]=400
			response["body"]={}     
			return response_proxy(response)

		logger.info(request["body"]["user_id"])
		logger.info("Checking to DB")
		if not vote_check_db(request["body"]["user_id"],request["body"]["poll_id"]):
			response["statusCode"]=400
			response["body"]={}     
			return response_proxy(response)
		
		logger.info("Saving to DB")
		vote_save_db(request["body"]["user_id"],request["body"]["poll_id"], request["body"]["item_id"])
		response["statusCode"]=200
		response["headers"]={}
		response["headers"]["Access-Control-Allow-Origin"]="*"        
		response["body"]={}
	except Exception as e:
		logger.info(e)
		logger.error(e)		
		response["statusCode"]=500
		response["body"]={}     
	return response_proxy(response)

def validate_request(data):
	schema = {'user_id': {'type': 'string', 'maxlength': 100,'required': True}, 'poll_id':{'type':'string','maxlength':100,'required': True}, 'item_id': {'type': 'string', 'maxlength': 100,'required': True}}
	v = Validator(schema)
	if(v.validate(data)):
		return True	
	logger.error('Request did not pass validation.')
	return False


def vote_check_db(user_id, poll_id):
	try:
		dynamodb = boto3.resource('dynamodb')
		table = dynamodb.Table(os.getenv("DB_VOTE_SCORE"))
		key = user_id+poll_id
		key = key.encode("utf-8")
		ID=str(hashlib.md5(key).hexdigest())
		
		response = table.get_item(
			Key={
				'ID': ID,			
			}
		)
		logger.info(response)

		if "Item" not in response:
			return True

		if len(response['Item'])==0:
			return True
		else:
			return False
	except Exception as e:
		logger.info(e)
		logger.error(e)
		return False		

def vote_save_db(user_id, article_id, post_url):
	try:
		dynamodb = boto3.resource('dynamodb')
		table = dynamodb.Table(os.getenv("DB_VOTE_SCORE"))
		key = user_id+article_id
		key = key.encode("utf-8")
		ID=str(hashlib.md5(key).hexdigest())
		response = table.put_item(
			Item={
				'ID':ID,
				'user_ID': user_id,
				'poll_ID': article_id,
				'item_ID': post_url
			}
		)
		return True
	except Exception as e:
		logger.info(e)
		logger.error(e)
		return False
