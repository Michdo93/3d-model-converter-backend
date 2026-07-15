import os
import io
import trimesh
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Mime-Types für 3D-Modelle
MIME_TYPES = {
    'stl': 'model/stl',
    'obj': 'model/obj',
    'ply': 'model/ply',
    'off': 'text/plain'
}

@app.route('/convert', methods=['POST'])
def convert_3d_model():
    if 'file' not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format', '').lower().strip()
    
    if file.filename == '' or not target_format:
        return jsonify({"error": "Ungültige Parameter"}), 400

    filename, file_extension = os.path.splitext(file.filename)
    source_format = file_extension.lower().replace('.', '')

    if source_format == target_format:
        return jsonify({"error": "Quell- und Zielformat sind identisch."}), 400

    try:
        # 1. Datei in BytesIO-Buffer laden
        file_bytes = file.read()
        input_buffer = io.BytesIO(file_bytes)

        # 2. 3D-Mesh mit trimesh laden
        # Wir übergeben das Quellformat explizit, damit trimesh weiß, wie es den Buffer parsen soll
        mesh = trimesh.load(input_buffer, file_type=source_format)

        # Falls es sich um eine Szene (mehrere Objekte) handelt, konvertieren wir sie in ein einzelnes Mesh
        if isinstance(mesh, trimesh.Scene):
            mesh = mesh.dump(concatenate=True)

        # 3. In das Zielformat exportieren
        output_buffer = io.BytesIO()
        
        # trimesh exportiert STL standardmäßig im Binärformat (platzsparend)
        exported_data = mesh.export(file_type=target_format)
        
        # Sicherstellen, dass wir Bytes vorliegen haben (manche Formate exportieren als String)
        if isinstance(exported_data, str):
            output_buffer.write(exported_data.encode('utf-8'))
        else:
            output_buffer.write(exported_data)
            
        output_buffer.seek(0)
        mime = MIME_TYPES.get(target_format, 'application/octet-stream')

        return send_file(
            output_buffer,
            mimetype=mime,
            as_attachment=True,
            download_name=f"{filename}.{target_format}"
        )

    except Exception as e:
        return jsonify({"error": f"Fehler bei der 3D-Konvertierung: {str(e)}. Ist die hochgeladene Geometrie beschädigt?"}), 500

if __name__ == '__main__':
    app.run(port=8080)
