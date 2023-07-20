import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/convert', methods=['GET'])
def convert_coordinates():
    try:
        longitude = request.args.get('lon')
        latitude = request.args.get('lat')
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
            return jsonify({'address': address}), 200
        
        return jsonify({'error': 'Address not found.', 'res_status': f'{response.status_code}'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host = '54.174.34.157')
