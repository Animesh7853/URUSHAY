from flask import Flask, request, jsonify, send_file, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
import io
import os
import traceback
from docs import modify_and_encrypt_pdf, modify_docx, mask_pptx_file, mask_excel_file, encrypt_excel_file
from io import BytesIO

app = Flask(__name__)
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:3000", "https://urushay-uxsw.vercel.app"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "expose_headers": ["Content-Disposition", "Content-Length", "Content-Type"],
        "supports_credentials": True
    }
})

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'message': 'Server is running'
    }), 200


@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

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
            response = make_response(send_file(
                processed_stream,
                mimetype=mimetype,
                as_attachment=True,
                download_name=processed_name
            ))
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

    except Exception as e:
        print(traceback.format_exc())  # Log the full error
        return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Unknown error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)