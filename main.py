

from google.cloud import secretmanager
import http.client
import json
import pprint
import os
import pyrebase
import random
import string
import uuid


# Code for APP

def get_started(request):

    request_args = request.get_json(silent=True)
    vehicle_token= None
    if request_args and "client_token" in request_args:
        client_token = request_args['client_token']
        refresh_token=get_refresh_token(client_token)
        if refresh_token is None:
            return {"error":"client token not found"}
        vehicle_token=access_refresh(refresh_token)
        REFRESH_TOKEN = vehicle_token['REFRESH_TOKEN']
    if request_args and  "authorization_code" in request_args:
        CODE = request_args["authorization_code"]
        vehicle_token = get_access_token(CODE)
        REFRESH_TOKEN = vehicle_token['REFRESH_TOKEN']
        client_token = create_client_token()
    if vehicle_token is not None:
        ACCESS_TOKEN = vehicle_token['ACCESS_TOKEN']
        save_vehicle(client_token, REFRESH_TOKEN)
        vehicle_info = get_vehicle_info(ACCESS_TOKEN)

        dic_vehicle_info=dict(zip(range(len(vehicle_info)),vehicle_info))
        client_vehicles ={}
        client_vehicles['client_token'] = client_token
        client_vehicles['vehicles']=dic_vehicle_info
        return client_vehicles
    else:
        return {"error":"authorization code wrong or issue with api"}



def get_secrets(secret_name):
    project_id = "cloud-function-learn-318812"
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=name)
    my_secret_value = response.payload.data.decode("UTF-8")
    return my_secret_value



def get_access_token(CODE):
    
    CLIENT_ID = get_secrets("CLIENT_ID")
    CLIENT_SECRETS=get_secrets('CLIENT_SECRETS')
    conn = http.client.HTTPSConnection("dah2vb2cprod.b2clogin.com")
    payload = f"grant_type=authorization_code&client_id={CLIENT_ID}&client_secret={CLIENT_SECRETS}&code={CODE}&redirect_uri=https%3A%2F%2Flocalhost%3A3000"
    headers = { 'content-type': "application/x-www-form-urlencoded" }
    conn.request("POST", "/914d88b1-3523-4bf6-9be4-1b96b4f6f919/oauth2/v2.0/token?p=B2C_1A_signup_signin_common", body=payload, headers=headers)

    res = conn.getresponse()
    data = res.read()
    token=json.loads(data.decode("utf-8"))
    if 'refresh_token' in token.keys():
        REFRESH_TOKEN = token['refresh_token']
        ACCESS_TOKEN= token['access_token']
        data = {"ACCESS_TOKEN": ACCESS_TOKEN, "REFRESH_TOKEN":REFRESH_TOKEN}
        return data
    else:
        return None




       


def get_vehicle_info(ACCESS_TOKEN):
    conn = http.client.HTTPSConnection("api.mps.ford.com")
    headers = {
                'Application-id': "afdc085b-377a-4351-b23e-5e1d35fb3700",
                'authorization': "Bearer "+ACCESS_TOKEN,
                'api-version' : "2020-06-01"
        }
        
    vehicles = get_vehical_list(ACCESS_TOKEN)
        
    vehicle_info=[]
    
    for vehicle in vehicles:
        vehicleid=vehicle["vehicleId"]
        conn.request("GET", f"/api/fordconnect/vehicles/v1/{vehicleid}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        vehicle_dic=json.loads(data.decode("utf-8"))
        
        if "vehicle" in vehicle_dic.keys():        
            distance=vehicle_dic['vehicle']['vehicleDetails']['fuelLevel']['distanceToEmpty']
            vehicleid=vehicle_dic['vehicle']['vehicleId']
            vehicle_info.append({"vehicle_id":vehicleid,"distance_to_empty":distance})
    return vehicle_info   


config = {
    "apiKey": get_secrets("firebase_apikey"),
    "authDomain":"25787380523-8l83kcv1gq70g083tc8bbjl9j00oingd.apps.googleusercontent.com",  
    "databaseURL": "https://cloud-function-learn-318812-default-rtdb.firebaseio.com/",
    "storageBucket": "cloud-function-learn-318812.appspot.com" 
     }
firebase = pyrebase.initialize_app(config)

def save_vehicle(client_token,refresh_token):
    
    db = firebase.database()
    result=db.child("vehicle").child(client_token).get()
    if result.val() is not None:
        db.child("vehicle").child(client_token).update({'vehicleRefreshToken':refresh_token})
    else:
        data = {'vehicleRefreshToken':refresh_token}
        db.child("vehicle").child(client_token).set(data)

    

def get_refresh_token(client_token):

    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
    token=db.child("vehicle").child(client_token).get()  
    refresh_token=token.val()['vehicleRefreshToken']
    return refresh_token




def get_vehical_list(ACCESS_TOKEN):

    conn = http.client.HTTPSConnection("api.mps.ford.com")
    headers = {
                'Application-id': "afdc085b-377a-4351-b23e-5e1d35fb3700",
                'authorization': "Bearer "+ACCESS_TOKEN,
                'api-version' : "2020-06-01"
        }
    conn.request("GET", "/api/fordconnect/vehicles/v1", headers=headers)
    res = conn.getresponse()
    data = res.read()
    vehicle_dic=json.loads(data.decode("utf-8"))
    vehicles = vehicle_dic['vehicles']
    return vehicles

def create_client_token():
    
    client_token =  uuid.uuid1() ## make a UUID based on the host ID and current time
    return client_token



def access_refresh(refresh_token):

    CLIENT_ID = get_secrets("CLIENT_ID")
    CLIENT_SECRETS=get_secrets('CLIENT_SECRETS')
    conn = http.client.HTTPSConnection("dah2vb2cprod.b2clogin.com")    
    payload = f"grant_type=refresh_token&refresh_token={refresh_token}&client_id={CLIENT_ID}&client_secret={CLIENT_SECRETS}"
    headers = { 'content-type': "application/x-www-form-urlencoded" }

    conn.request("POST", "/914d88b1-3523-4bf6-9be4-1b96b4f6f919/oauth2/v2.0/token?p=B2C_1A_signup_signin_common", body=payload, headers=headers)
    res = conn.getresponse()
    data = res.read()
    token=json.loads(data.decode("utf-8"))
    if 'refresh_token' in token.keys():
        REFRESH_TOKEN = token['refresh_token']
        ACCESS_TOKEN= token['access_token']
        data = {"ACCESS_TOKEN": ACCESS_TOKEN, "REFRESH_TOKEN":REFRESH_TOKEN}
        return data
    else:
        return None

