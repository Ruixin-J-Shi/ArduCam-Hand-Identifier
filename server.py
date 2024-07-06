from asyncio import sleep
import numpy as np
import serial
import time
import cv2
import mediapipe as mp
from flask import Flask, send_file, Response, stream_with_context, render_template_string

app = Flask(__name__)
ser = serial.Serial('COM7', 115200, timeout=1)  # Adjust the COM port and baud rate as necessary

# Initialize mediapipe
mp_hands = mp.solutions.hands

# hands = mp_hands.Hands(static_image_mode=False,
#                        max_num_hands=1,
#                        min_detection_confidence=0.5)

hands = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,  # Increase detection confidence
    min_tracking_confidence=0.7    # Increase tracking confidence
)

image_path = 'image.jpg'

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
    <title>Gesture Stream</title>
    <style>
        body, html {
            height: 100%;
            margin: 0;
            font-family: Arial, sans-serif;
        }
        #data {
            position: absolute;
            width: 100%;
            bottom: 10px;
        }
    </style>
    <script type="text/javascript">
        window.onload = function() {
            var elem = document.getElementById('data');
            var source = new EventSource('/stream');

            source.onmessage = function(e) {
                elem.innerHTML += e.data + '<br>';
            };

            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                });
            });

            observer.observe(elem, {
                childList: true
            });
        };
    </script>
</head>
<body>
    <div id="data"></div>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/a_image')
def process_image():
    global image_path  # This ensures that the function uses the global variable 'image_path'
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            tip_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
            mcp_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y

            if tip_y < mcp_y:
                time.sleep(1)
                print("write u")
                ser.write(b'u')
                return "Gesture Detected: Up"
            elif tip_y > mcp_y:
                ser.write(b'd')  # Send 'd' for down to Arduino
                time.sleep(1)
                print("write d")
                return "Gesture Detected: Down"
                
    ser.write(b'n')
    return "No hand detected"



@app.route('/u')
def writeu():
    ser.write(b'u')
    sleep(0.1)  # give Arduino time to process
    return "u"

@app.route('/d')
def writed():
    ser.write(b'd')
    sleep(0.1)  # give Arduino time to process
    return "d"

@app.route('/l')
def writel():
    ser.write(b'l')
    sleep(0.1)  # give Arduino time to process
    return "l"

@app.route('/r')
def writer():
    ser.write(b'r')
    sleep(0.1)  # give Arduino time to process
    return "r"


@app.route('/n')
def writen():
    ser.write(b'n')
    sleep(0.1)  # give Arduino time to process
    return "n"


@app.route('/take_picture')
def take_picture():
    
    image_data = bytearray()
    timeout_start = time.time()
    timeout = 2  # seconds

    while time.time() < timeout_start + timeout:
        if ser.inWaiting() > 0:
            image_data.extend(ser.read(ser.inWaiting()))
            time.sleep(1)  # Allow buffer to fill
        else:
            time.sleep(1)  # Prevent tight loop if data transmission is complete

    if not image_data:
        print("No data received from Arduino.")
        return Response("No data received from Arduino", status=500)

    filename = 'image.jpg'
    with open(filename, 'wb') as f:
        f.write(image_data)
        print(f"Image saved as {filename}, {len(image_data)} bytes.")

    return send_file(filename, mimetype='image/jpeg')



@app.route('/stream')
def stream():
    def generate():
        while True:
            image_data = bytearray()
            while ser.inWaiting() > 0:
                image_data += ser.read(ser.inWaiting())
            if image_data:
                image = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if image is not None:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    results = hands.process(image)
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            gesture = process_gestures(hand_landmarks)
                            ser.write(gesture.encode())  # Send gesture command to Arduino
                            yield f"Gesture Detected: {gesture.upper()}\n"
                    else:
                        ser.write(b'n')
                        yield "No hand detected\n"
            time.sleep(1)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


def process_gestures(hand_landmarks):
    # Extract coordinates
    wrist_x = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x
    tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x
    tip_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y
    mcp_y = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y

    # Determine gestures based on landmark positions
    if abs(tip_x - wrist_x) > abs(tip_y - mcp_y):
        if tip_x < wrist_x:
            ser.write(b'r')
            return 'r'  # Left gesture
        else:
            ser.write(b'l')
            return 'l'  # Right gesture
    else:
        if tip_y < mcp_y:
            ser.write(b'u')
            return 'u'  # Up gesture
        else:
            ser.write(b'd')
            return 'd'  # Down gesture
    return 'n'  # No gesture detected










def count_fingers(hand_landmarks):
    """ Counts the number of fingers extended using Mediapipe hand landmarks. """
    # Definitions for fingertips and PIPs (second joint of each finger)
    finger_tips = {
        'thumb': mp_hands.HandLandmark.THUMB_TIP,
        'index': mp_hands.HandLandmark.INDEX_FINGER_TIP,
        'middle': mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        'ring': mp_hands.HandLandmark.RING_FINGER_TIP,
        'pinky': mp_hands.HandLandmark.PINKY_TIP
    }
    finger_pips = {
        'thumb': mp_hands.HandLandmark.THUMB_IP,
        'index': mp_hands.HandLandmark.INDEX_FINGER_PIP,
        'middle': mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        'ring': mp_hands.HandLandmark.RING_FINGER_PIP,
        'pinky': mp_hands.HandLandmark.PINKY_PIP
    }
    
    count = 0
    for finger, tip in finger_tips.items():
        tip_pos = hand_landmarks.landmark[tip]
        pip_pos = hand_landmarks.landmark[finger_pips[finger]]

        if finger == 'thumb':
            # Thumb is considered extended if the tip is above the IP joint horizontally (for right hand)
            if abs(tip_pos.x - pip_pos.x) > abs(tip_pos.y - pip_pos.y):
                if tip_pos.x > pip_pos.x:
                    count += 1
        else:
            # Other fingers are considered extended if the tip is above the PIP joint vertically
            if tip_pos.y < pip_pos.y:
                count += 1

    return count

@app.route('/stream1')
def stream_fingers():
    def generate():
        while True:
            if ser.inWaiting() > 0:
                image_data = bytearray(ser.read(ser.inWaiting()))
                if image_data:  # Check if there is data before decoding
                    image = cv2.imdecode(np.frombuffer(image_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if image is not None:
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        results = hands.process(image)
                        if results.multi_hand_landmarks:
                            for hand_landmarks in results.multi_hand_landmarks:
                                finger_count = count_fingers(hand_landmarks)
                                ser.write(str(finger_count).encode())
                                yield f"Fingers Detected: {finger_count}\n"
                        else:
                            ser.write(b'0')
                            yield "No hand detected\n"
            time.sleep(1)  # Use time.sleep() for a synchronous delay
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)