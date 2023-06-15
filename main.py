from flask import Flask, request, render_template, session, redirect, url_for
from flask_dropzone import Dropzone
from werkzeug.utils import secure_filename
from PIL import Image
from sklearn.cluster import KMeans
import numpy as np
import webcolors
import os


UPLOAD_FOLDER = 'static/images/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)

app.config.update(
    UPLOAD_FOLDER_PATH=UPLOAD_FOLDER,
    DROPZONE_MAX_FILE_SIZE=4*1024*1024,
    DROPZONE_TIMEOUT=0.5*60*1000,
    SECRET_KEY="my_secret_key",
)

app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image'

dropzone = Dropzone(app)

# ----- / functions area / -----

# returns the extension of the loaded file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# if image is too large for the webpage
def resize_image(file):
    img = Image.open(file)
    width, height = img.size

    if width > height:
        # Calculate the new height while maintaining the aspect ratio
        new_width = 600
        new_height = int(height * (new_width / width))
    else:
        # Calculate the new width while maintaining the aspect ratio
        new_height = 400
        new_width = int(width * (new_height / height))

    desire_size = (new_width, new_height)
    r_image = img.resize(desire_size, Image.LANCZOS)
    return r_image

# process the image once is dropped in the dropzone
def process_image(file_path):

    img = Image.open(file_path)
    # Convert Image object to ndarray
    pixel_array = np.array(img)
    print(pixel_array.shape)
    # Remove the alpha channel if it exists ( avoids the error when photo has 4 channels, i.e. alpha channel )
    if pixel_array.shape[2] == 4:
        pixel_array = pixel_array[:, :, :3]
    pixel_array = pixel_array.reshape(-1, 3)
    # process photo
    num_clusters = 10
    kmeans = KMeans(n_clusters=num_clusters, random_state=0, n_init="auto")
    kmeans.fit(pixel_array)
    color_palette = kmeans.cluster_centers_.astype(int).tolist()
    hex_codes = [webcolors.rgb_to_hex(tuple(color)) for color in color_palette]
    hex_codes = [hex_code.strip() for hex_code in hex_codes]

    return color_palette, hex_codes


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    print("INITIATING UPLOAD FUNCTION")  # can be deleted only for testing
    file = request.files.get('file')

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER_PATH'], filename)
        # file_path = UPLOAD_FOLDER + filename

        resized_img = resize_image(file)
        resized_img.save(file_path)  # Save the resized image

        color_palette, hex_codes = process_image(file_path)

        # Clear the old session variables
        session.pop('output_path', None)
        session.pop('color_palette', None)
        session.pop('hex_codes', None)

        # load new Session
        session['output_path'] = file_path
        session['color_palette'] = color_palette
        session['hex_codes'] = hex_codes

        return redirect(url_for('result'))

    return redirect(url_for('index'))

# renders a new webpage with the results of processing the photo
@app.route('/result', methods=['GET', 'POST'])
def result():
    print('SHOWING RESULTS')
    file_path = session.get('output_path')
    print("the file path from result is : ", file_path)
    color_palette = session.get('color_palette')
    hex_codes = session.get('hex_codes')

    return render_template('result.html', file_path=file_path, color_palette=color_palette, hex_codes=hex_codes)


if __name__ == '__main__':
    app.run(debug=True)
