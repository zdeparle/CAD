import os
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
import cadquery as cq
from cadquery import exporters

app = Flask(__name__)
GEN_DIR = os.path.join(os.path.dirname(__file__), 'generated')
os.makedirs(GEN_DIR, exist_ok=True)


def build_model(desc: str) -> cq.Workplane:
    tokens = desc.lower().split()
    if not tokens:
        raise ValueError('Empty description')
    shape = tokens[0]
    args = list(map(float, tokens[1:]))
    if shape in ('box', 'cube'):
        if len(args) == 1:
            w = h = d = args[0]
        elif len(args) == 3:
            w, h, d = args
        else:
            raise ValueError('box requires 1 or 3 dimensions')
        return cq.Workplane('XY').box(w, h, d)
    elif shape == 'cylinder':
        if len(args) != 2:
            raise ValueError('cylinder requires radius and height')
        r, h = args
        return cq.Workplane('XY').cylinder(h, r)
    elif shape == 'sphere':
        if len(args) != 1:
            raise ValueError('sphere requires radius')
        r = args[0]
        return cq.Workplane('XY').sphere(r)
    else:
        raise ValueError(f'Unknown shape {shape}')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json(force=True)
    desc = data.get('description', '')
    try:
        model = build_model(desc)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    file_id = str(uuid.uuid4())
    stl_name = f'{file_id}.stl'
    step_name = f'{file_id}.step'
    stl_path = os.path.join(GEN_DIR, stl_name)
    step_path = os.path.join(GEN_DIR, step_name)
    exporters.export(model, stl_path)
    exporters.export(model, step_path)
    return jsonify({'preview': f'/generated/{stl_name}', 'step': f'/generated/{step_name}'})


@app.route('/generated/<path:filename>')
def serve_generated(filename: str):
    return send_from_directory(GEN_DIR, filename, as_attachment=filename.endswith('.step'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
