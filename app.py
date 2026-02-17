from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
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
