'''
Lambda function to perform checking on vote based on article_id provided by client.
'''
from os import environ
import json
import logging
import boto3
from boto3.dynamodb.conditions import Key, Attr
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
        status = vote_check_db(request["body"]["user_id"], request["body"]["poll_id"])

        response["statusCode"] = 200
        response["headers"]={}
        response["headers"]["Access-Control-Allow-Origin"]="*"        
        response["body"] = {}
        response["body"]["user_vote"] = status
    except Exception as e:
        logger.error(e)
        response["statusCode"] = 500
        response["body"] = {}
    return response_proxy(response)

def validate_request(data):
    '''
    Challenge the data request with the validation scheme using Cerberus
    '''
    schema = {'user_id':{'type':'string', 'maxlength':100, 'required': True}, 'poll_id':{'type':'string', 'maxlength':100, 'required': True}}
    validator = Validator(schema)
    if validator.validate(data):
        return True
    logger.error('Request did not pass validation.')
    return False

def vote_check_db(user_id, poll_id):
    '''
    Check to database
    '''
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(environ["DB_VOTE_SCORE"])
        response = table.query(
            IndexName="poll_ID_index",
            Select="COUNT",
            KeyConditionExpression=Key('poll_ID').eq(poll_id),
            FilterExpression=Attr('user_ID').eq(user_id),
        )
        logger.info(response)

        if response["Count"]>0:
            return True
        else:
            return False
    except Exception as e:
        logger.info(e)
        logger.error(e)
        return False
