from flask import Flask, request, render_template, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import requests
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['COMPRESSED_FOLDER'] = 'compressed/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB limit

# Ensure upload and compressed folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['COMPRESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def compress_image(filepath, output_path, quality=85):
    try:
        img = Image.open(filepath)
        # Convert to RGB if it's RGBA or P to avoid issues with some formats when saving as JPEG
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=quality)
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['GET', 'POST'])
def weather():
    if request.method == 'POST':
        city = request.form.get('city')
        if not city:
            return jsonify({'error': 'Please enter a city name'}), 400
        
        try:
            # 1. Get coordinates for the city using Open-Meteo Geocoding API
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_response = requests.get(geo_url)
            geo_data = geo_response.json()
            
            if 'results' not in geo_data or len(geo_data['results']) == 0:
                return jsonify({'error': 'City not found'}), 404
            
            lat = geo_data['results'][0]['latitude']
            lon = geo_data['results'][0]['longitude']
            location_name = geo_data['results'][0]['name']
            country = geo_data['results'][0].get('country', '')

            # 2. Get weather data using Open-Meteo Weather API
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()
            
            if 'current_weather' not in weather_data:
                return jsonify({'error': 'Could not fetch weather data'}), 500
            
            temp = weather_data['current_weather']['temperature']
            wind_speed = weather_data['current_weather']['windspeed']
            weather_code = weather_data['current_weather']['weathercode']
            
            # Simple mapping of weather code to description
            weather_desc = "Clear sky" if weather_code == 0 else "Partly cloudy" if weather_code in [1,2,3] else "Cloudy" if weather_code in [45,48] else "Rainy" if weather_code in [51,53,55,61,63,65,80,81,82] else "Snowy" if weather_code in [71,73,75,77,85,86] else "Unknown"

            return jsonify({
                'city': location_name,
                'country': country,
                'temperature': temp,
                'wind_speed': wind_speed,
                'description': weather_desc
            })
            
        except Exception as e:
            print(f"Weather API Error: {e}")
            return jsonify({'error': 'An error occurred while fetching weather data'}), 500
            
    return render_template('index.html', active_tab='weather')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        compressed_filename = f"compressed_{filename}"
        compressed_filepath = os.path.join(app.config['COMPRESSED_FOLDER'], compressed_filename)

        if compress_image(filepath, compressed_filepath, quality=80): # Compressing with 80% quality
            return redirect(url_for('view_compressed', filename=compressed_filename))
        else:
            return "Error compressing image. Please try again with a valid image file."
    else:
        return "Invalid file type. Please upload an image (png, jpg, jpeg, gif)."

@app.route('/compressed/<filename>')
def view_compressed(filename):
    return send_from_directory(app.config['COMPRESSED_FOLDER'], filename)

if __name__ == '__main__':
    # This is for local development. For production, use a proper WSGI server.
    # Ensure you have Flask and Pillow installed: pip install Flask Pillow
    app.run(debug=True)
