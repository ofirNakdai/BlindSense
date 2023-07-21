import requests
from flask import Flask, request, send_file, url_for, jsonify
from gtts import gTTS
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'audio_files'

def convert_coordinates(longitude, latitude):
    try:
        
        #longitude = request.args.get('lon')
        #latitude = request.args.get('lat')
        if not longitude or not latitude:
            return jsonify({'error': 'Invalid coordinates.'}), 400

        # Make a request to the Geocoding API
        google_api_key = 'AIzaSyBPggICP_7W1DWoLv39wRRm4EzPqmVngUQ'
        positionstack_api_key = '17e8081f0ef58dcc6c446eac3bc308f3'
        
        #url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}'
        positionstack_url = f'http://api.positionstack.com/v1/reverse?access_key={positionstack_api_key}&query={latitude},{longitude}'
        rapidai_url = "https://forward-reverse-geocoding.p.rapidapi.com/v1/reverse"
        headers = {"X-RapidAPI-Key": "2f63e18054msh8b8d55ed08454a2p1de428jsn9604cdda36e7", "X-RapidAPI-Host": "forward-reverse-geocoding.p.rapidapi.com"}
        querystring = {"lat":latitude,"lon":longitude,"accept-language":"en","polygon_threshold":"0.0"}            
        response = requests.get(rapidai_url, headers=headers, params=querystring)
        json_data = response.json()
        
        # Parse the response to get the address
        if response.status_code == 200:
            address = ""
            if json_data['address']['road'] is not None:
                address = address + json_data['address']['road'] + ','
            elif json_data['address']['street'] is not None:
                address = address + json_data['address']['street'] + ','
            if json_data['address']['house_number'] is not None: 
                address = address + json_data['address']['house_number'] + ','
            if json_data['address']['city'] is not None: 
                address = address + json_data['address']['city'] + ','
            if json_data['address']['country'] is not None: 
                address = address + json_data['address']['country']
            #return jsonify({'address': address}), 200
            return address
        
        return jsonify({'error': 'Address not found.', 'res_status': f'{response.status_code}'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/convert', methods=['GET'])
def convert_to_speech():
    text = request.args.get('text')
    
    longtitute = request.args.get('lon')
    latitude = request.args.get('lat')
    
    adress = convert_coordinates(longtitute, latitude)
    text = f'Hello Ofir, your current location is {adress}'
    #textHeb = f'שלום אופיר, המיקום הנוכחי שלך הוא {adress}'
    
    if longtitute is not None and latitude is not None:
        tts = gTTS(text, lang='en')
        audio_file = 'output.mp3'
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file)
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Create the directory if it doesn't exist
        
        tts.save(file_path)
        
        # Generate the play request URL
        play_url = url_for('play_audio', filename=audio_file, _external=True)
        
        return play_url, 200
        #return file_path
    else:
        return 'No text provided.', 400

@app.route('/play/<path:filename>', methods=['GET'])
def play_audio(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 3011)
