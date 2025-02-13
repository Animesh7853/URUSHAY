from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import io
import os
import traceback
from docs import modify_and_encrypt_pdf, modify_docx, mask_pptx_file, mask_excel_file, encrypt_excel_file
from io import BytesIO

app = Flask(__name__)
CORS(app, resources={
    r"/*": {  # Allow CORS for all routes
        "origins": "*",  # Allow all origins
        "methods": ["GET", "POST"],  # Allow both GET and POST methods
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Disposition", "Content-Length"]
    }
})
app.config['UPLOAD_FOLDER'] = 'uploads/'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running'
    }), 200


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file:
            filename = secure_filename(file.filename)
            file_content = file.read()
            file_stream = io.BytesIO(file_content)
            processed_stream = io.BytesIO()

            if filename.lower().endswith('.pdf'):
                password = "securepassword"
                modify_and_encrypt_pdf(file_stream, processed_stream, password)
                processed_stream.seek(0)
                response = send_file(
                    processed_stream,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"processed_{filename}",
                    max_age=0
                )
                # Set correct content length
                response.headers['Content-Length'] = processed_stream.getbuffer().nbytes
                return response
            elif filename.lower().endswith(('.doc', '.docx')):
                modify_docx(file_stream, processed_stream)
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                processed_name = filename.replace('.docx', '_processed.docx')
            elif filename.lower().endswith(('.ppt', '.pptx')):
                mask_pptx_file(file_stream, processed_stream)
                mimetype = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                processed_name = 'processed.pptx'
            elif filename.lower().endswith(('.xls', '.xlsx')):
                mask_excel_file(file_stream, processed_stream)
                encrypt_excel_file(processed_stream)
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                processed_name = 'processed.xlsx'
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

            processed_stream.seek(0)
            return send_file(
                processed_stream,
                mimetype=mimetype,
                as_attachment=True,
                download_name=processed_name
            )

    except Exception as e:
        print(traceback.format_exc())  # Log the full error
        return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Unknown error occurred'}), 500

@app.route('/uploads/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)