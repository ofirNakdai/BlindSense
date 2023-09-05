import requests
from flask import Flask, request, send_file, url_for, jsonify
from gtts import gTTS
import os
import logging
import pymongo
from twilio.rest import Client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'audio_files'

log_file = os.path.join(os.path.dirname(__file__), 'app.log')

# Configure the logger
logging.basicConfig(filename=log_file, level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


client = pymongo.MongoClient("mongodb://mongo:27017/")
db = client["blindSenseDB"]
registryCollection = db["registry"]

message_service_sid = 'MG496c156df0604232a3adca70d4e5403d'
account_sid = "AC8fd9a3078755856172774ae1a019f239"
#auth_token = "8c30544d97b7373251c5a8500edf2121"
phone_number = '+12518424307'

gmail_pass = 'fsbtiqrrrwyheysw'
gmail_acount = 'blindsense2023@gmail.com'


def convert_coordinates(longitude, latitude):
    app.logger.info(f'Converting coordinates: {longitude}, {latitude}')
    
    try:
        
        #longitude = request.args.get('lon')
        #latitude = request.args.get('lat')
        if not longitude or not latitude:
            app.logger.error('Invalid coordinates.')
            return jsonify({'error': 'Invalid coordinates.'}), 400

        # Make a request to the Geocoding API
        google_api_key = 'AIzaSyBPggICP_7W1DWoLv39wRRm4EzPqmVngUQ'
        positionstack_api_key = '17e8081f0ef58dcc6c446eac3bc308f3'
        
        rapidai_url = "https://forward-reverse-geocoding.p.rapidapi.com/v1/reverse"
        headers = {"X-RapidAPI-Key": "2f63e18054msh8b8d55ed08454a2p1de428jsn9604cdda36e7", "X-RapidAPI-Host": "forward-reverse-geocoding.p.rapidapi.com"}
        querystring = {"lat":latitude,"lon":longitude,"accept-language":"en","polygon_threshold":"0.0"}            
        response = requests.get(rapidai_url, headers=headers, params=querystring)
        json_data = response.json()
        
        # Parse the response to get the address
        if response.status_code == 200:
            address = ""
            addressKeys = json_data['address'].keys()
            if 'road' in addressKeys:
                address = address + json_data['address']['road'] + ','
            elif 'street' in addressKeys:
                address = address + json_data['address']['street'] + ','
            if 'house_number' in addressKeys:                 
                address = address + json_data['address']['house_number'] + ','
            if 'city' in addressKeys: 
                address = address + json_data['address']['city'] + ','
            if 'country' in addressKeys: 
                address = address + json_data['address']['country']
            #return jsonify({'address': address}), 200
            app.logger.info(f'Address: {address}')
            return address
        
        app.logger.error(f'Address not found. Response status code: {response.status_code}')
        return jsonify({'error': 'Address not found.', 'res_status': f'{response.status_code}'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def create_google_maps_url(latitude, longitude):
    base_url = "https://www.google.com/maps/place"
    location = f"{latitude},{longitude}"
    return f"{base_url}/{location}"


def send_phone_message(phoneNumber, messageBody):
    #client = Client(account_sid, auth_token) 
    app.logger.info(f'Sending message to {phoneNumber}')
    message = client.messages.create( 
                                #from_=phone_number, 
                                messaging_service_sid=message_service_sid, 
                                body=messageBody,      
                                to=phoneNumber 
                            ) 
    
    
 
    print(message.sid)

def send_email_message(recipient_email, messageBody):
    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)
    
    # start TLS for security
    s.starttls()
    
    # Authentication
    s.login("blindsense2023@gmail.com", "fsbtiqrrrwyheysw")
    
    # message to be sent
    message = messageBody
    
    # sending the mail
    s.sendmail("blindsense2023@gmail.com", recipient_email, message)
    
    # terminating the session
    s.quit()

def send_email_message2(recipient_email, messageBody):
    # Set up the sender and recipient addresses
    app.logger.info(f'Sending email to {recipient_email}')
    # Create the email message
    message = MIMEMultipart()
    message["From"] = gmail_acount
    message["To"] = recipient_email
    message["Subject"] = "Subject of the email"

    # Body of the email
    message.attach(MIMEText(messageBody, "plain"))

    # Connect to the email server and send the email
    smtp_server = "smtp.gmail.com"  # Use the appropriate SMTP server
    smtp_port = 587  # Use the appropriate port for your email provider

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Encrypt the connection
        server.login(gmail_acount, gmail_pass)
        server.sendmail(gmail_acount, recipient_email, message.as_string())

    print("Email sent successfully.")
    
###############################Text to speech#############################################
@app.route('/convert', methods=['GET'])
def convert_to_speech():
    text = request.args.get('text')
    
    
    clientID = request.args.get('clientID')
    longtitute = request.args.get('lon')
    latitude = request.args.get('lat')
    
    result = registryCollection.find_one({"_id": clientID}, {"_id": 0})
    clientName = result['clientName'];
    app.logger.info(f'Converting text to speech, for client: {clientName}, lon: {longtitute}, lat: {latitude}')
    
    if float(longtitute) != -1.0 and float(latitude) != -1.0:
        ifi = (longtitute != "-1.000000" )
        app.logger.info(f'Converting coordinates: {longtitute}, {latitude}, if:{ifi}')
        adress = convert_coordinates(longtitute, latitude)    
        text = f'Hello {clientName}, your current location is {adress}'
    else:
        app.logger.info(f'Coordinates are -1')
        text = f'Hello {clientName}, your current location is not available'
    
    if longtitute != None and latitude != None:
        tts = gTTS(text, lang='en')
        audio_file = 'output.mp3'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create the directory if it doesn't exist
        
        tts.save(file_path)
        
        # Generate the play request URL
        play_url = url_for('play_audio', filename=audio_file, _external=True)
        return play_url, 200
    else:
        return 'No text provided.', 400


@app.route('/play/<path:filename>', methods=['GET'])
def play_audio(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))



############################### registry #############################################

@app.route('/register', methods=['POST'])
def register():
    docID = request.args.get('clientID')
    doc = registryCollection.find_one({"_id": docID}, {"_id" : 0}) 
    isUpdate = False
    
    data = {
            "clientName": request.args.get('clientName'),
            "contactName": request.args.get('contactName'),
            "contactPhone": request.args.get('contactPhone'),
            "contactEmail": request.args.get('contactEmail'),
            "_id": request.args.get('clientID')
        }

    if doc is None:
    # Insert the data into the MongoDB collection
        result = registryCollection.insert_one(data)
        app.logger.info(f'Registering new client: {data}')
    else:
        result = registryCollection.update_one({"_id": docID}, {"$set": data})
        app.logger.info(f'Updating client: {data}')
        isUpdate = True

    if isUpdate:
        return jsonify({"message": "Data updated successfully"}), 200
    else:
        return jsonify({"message": "Data inserted successfully"}), 201
    
    
@app.route('/register', methods=['GET'])
def get_register():
    # Get the data from the request
    client_id = request.args.get('clientID')
    
    # Get data from the MongoDB collection
    result = registryCollection.find_one({"_id": client_id}, {"_id": 0})
    
    if result:
        return jsonify(result), 200
    else:
        return jsonify({"message": "Client not found"}), 404

############################### SOS #############################################
@app.route('/sos', methods=['POST'])
def send_sos():
    app.logger.info(f'Sending SOS')
    # Get the data from the request
    clientID = request.args.get('clientID')
    longtitute = request.args.get('lon')
    latitude = request.args.get('lat')
    
    app.logger.info(f'ClientID: {clientID}, longtitute: {longtitute}, latitude: {latitude}')
    
       # Get data from the MongoDB collection
    result = registryCollection.find_one({"_id": clientID}, {"_id": 0})
    clientName = result['clientName'];
    contactName = result['contactName'];
    contactPhone = result['contactPhone'];
    contactEmail = result['contactEmail'];
    locationLink = create_google_maps_url(latitude, longtitute);
    
    
    if longtitute != -1.000000 and latitude != -1.000000:
        # Convert coordinates to address
        adress = convert_coordinates(longtitute, latitude); 
        message = f"Hello {contactName}, {clientName} triggered the SOS button on BlindSense. His current location is: {adress}." \
                    "Please contact him as soon as possible. " \
                    f"link to his current location: {locationLink}"
    else:
        message = f"Hello {contactName}, {clientName} triggered the SOS button on BlindSense. His current location is not available." \
                    "Please contact him as soon as possible. " 
                
                
    app.logger.info(f'Sending message: {message}, to {contactName}')            
    send_email_message2(contactEmail, message)
    send_phone_message(contactPhone, message)
    
    if result:
        return jsonify(message), 200
    else:
        return jsonify({"message": "Client not found"}), 404




if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 3011)
