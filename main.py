import os
from flask import Flask, request, send_file, url_for, jsonify
from gtts import gTTS
import requests


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'audio_files'


def convert_coordinates(longitude, latitude):
    try:
        #longitude = request.args.get('longitude')
        #latitude = request.args.get('latitude')
        
        if not longitude or not latitude:
            return jsonify({'error': 'Invalid coordinates.'}), 400

        # Make a request to the Geocoding API
        api_key = 'AIzaSyBPggICP_7W1DWoLv39wRRm4EzPqmVngUQ'  # Replace with your actual API key
        url = f'https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}'
        response = requests.get(url)
        data = response.json()
        
        # Parse the response to get the address
        if data['status'] == 'OK':
            results = data['results']
            if results:
                address = results[0]['formatted_address']
                print(address)
                return address
                #return jsonify({'address': address})
                
        
        return jsonify({'error': 'Address not found.'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/convert', methods=['GET'])
def convert_to_speech():
    text = request.args.get('text')
    
    longtitute = request.args.get('longitude')
    latitude = request.args.get('latitude')
    adress = convert_coordinates(longtitute, latitude)
    #return adress,200
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
        
        return play_url
        #return file_path
    else:
        return 'No text provided.', 400

@app.route('/play/<path:filename>', methods=['GET'])
def play_audio(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    app.run()
