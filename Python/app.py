from fastapi import FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from werkzeug.utils import secure_filename
import io
import os
import traceback
from docs import modify_and_encrypt_pdf, modify_docx, mask_pptx_file, mask_excel_file, encrypt_excel_file
from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://urushay-uxsw.vercel.app","https://urushay-main.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def health_check():
    return JSONResponse({
        'status': 'healthy',
        'message': 'Server is running'
    }, status_code=200)


@app.post('/upload')
async def upload_file(file: UploadFile):
    try:
        if not file:
            return JSONResponse({'error': 'No file part'}, status_code=400)
        
        filename = secure_filename(file.filename)
        if filename == '':
            return JSONResponse({'error': 'No selected file'}, status_code=400)

        file_content = await file.read()
        file_stream = io.BytesIO(file_content)
        processed_stream = io.BytesIO()

        if filename.lower().endswith('.pdf'):
            password = "securepassword"
            modify_and_encrypt_pdf(file_stream, processed_stream, password)
            processed_stream.seek(0)
            response = StreamingResponse(
                processed_stream,
                media_type='application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="processed_{filename}"',
                    'Content-Length': str(processed_stream.getbuffer().nbytes)
                }
            )
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
            return JSONResponse({'error': 'Unsupported file type'}, status_code=400)

        processed_stream.seek(0)
        return StreamingResponse(
            processed_stream,
            media_type=mimetype,
            headers={
                'Content-Disposition': f'attachment; filename="{processed_name}"'
            }
        )

    except Exception as e:
        print(traceback.format_exc())  # Log the full error
        return JSONResponse({'error': str(e)}, status_code=500)

    return JSONResponse({'error': 'Unknown error occurred'}, status_code=500)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, debug=True)