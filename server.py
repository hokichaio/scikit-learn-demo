from binascii import a2b_base64
import os
from tempfile import TemporaryFile
from urllib.parse import urlparse

from flask import Flask, json, render_template, request
from PIL import Image
import psycopg2
from psycopg2.extras import RealDictCursor as Cursor
from sklearn import svm


app = Flask(__name__)
app.config.update(dict(
    DATABASE_URL=os.environ.get('DATABASE_URL')
))

url = urlparse(app.config.get('DATABASE_URL'))
db_conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)


def flatten(arr):
    """Flatten N-dimension array and return a (N-1)-dimension array"""
    return sum(arr, [])


def chunkify(arr, per_chunk=8):
    for i in range(0, len(arr), per_chunk):
        yield arr[i:(i+per_chunk)]


def data_uri_to_temp_image_file(uri):
    """Generates a temp image from data URI string"""
    binary_data = a2b_base64(uri.split(",")[1])
    img = TemporaryFile()
    img.write(binary_data)
    return img


def parse_rgba_int(rgba_tuple):
    """Returns an integer value from 0 - 16 based on RGBA tuple

    Assumption: RGBA tuple is in shade of grey (ie., RGB is 0,0,0)
    """
    R, G, B, A = rgba_tuple
    return A // 16


def get_img_pixel_arrays(data_uri):
    """Returns an array of 64 RGBA tuples from provided data URI"""
    img_file = data_uri_to_temp_image_file(data_uri)
    img_file.seek(0)
    with Image.open(img_file) as img:
        img = img.resize((8, 8), Image.ANTIALIAS)
        arr = list(img.getdata())
        # each item in arr is expressed as RGBA tuple
        return [parse_rgba_int(pixel) for pixel in arr]


class NumberDrawingPredictor:
    """Service that predicts a digit (0-9) based on an 8x8 pixel art.

    The service utilizes machine learning to make informed decision.
    """
    def __init__(self):
        self.classifier = svm.SVC(gamma=0.001, C=100.0)
        self._train()

    def _train(self):
        """load training data and feed classification engine"""
        with db_conn.cursor(cursor_factory=Cursor) as cursor:
            cursor.execute("SELECT digit, pixels FROM numbers;")
            data = cursor.fetchall()
            labels, images = zip(
                *map(lambda r: (r['digit'], flatten(r['pixels'])), data)
            )
            self.classifier.fit(list(images), list(labels))

    @staticmethod
    def update(drawing_id, digit):
        with db_conn.cursor(cursor_factory=Cursor) as cursor:
            cursor.execute(
                "UPDATE numbers SET digit = %(digit)s WHERE id = %(id)s",
                {'digit': digit, 'id': drawing_id})
            db_conn.commit()

    def predict(self, pixels):
        # NOTE: pixels is a 64 integer array
        guess = int(self.classifier.predict([pixels])[0])
        with db_conn.cursor(cursor_factory=Cursor) as cursor:
            cursor.execute(
                "INSERT INTO numbers (digit, pixels) VALUES (%(digit)s, %(pixels)s) RETURNING id",
                dict(digit=guess, pixels=list(chunkify(pixels)))
            )
            res = cursor.fetchone()
            db_conn.commit()
            return guess, res.get('id')


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/api/drawings', methods=['POST'])
def draw_digit():
    payload = request.get_json()
    drawn_pixels = get_img_pixel_arrays(payload['img'])
    predictor = NumberDrawingPredictor()
    guess, identifier = predictor.predict(drawn_pixels)
    return json.jsonify(guess=guess, id=identifier), 201


@app.route('/api/drawings/<int:id>', methods=['PATCH'])
def update_result(id):
    correct_digit = int(request.get_json().get('digit'))
    NumberDrawingPredictor.update(id, correct_digit)
    return "", 204
