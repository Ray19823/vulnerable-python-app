from flask import Flask, request
import subprocess
import pickle
import yaml

app = Flask(__name__)

# Deliberately vulnerable code for demonstration
@app.route('/')
def index():
    return '''
    <h1>Vulnerable Python Demo App</h1>
    <p>This app contains intentional vulnerabilities for security scanning demonstration.</p>
    <ul>
        <li><a href="/execute?cmd=ls">Command Execution Demo</a></li>
        <li><a href="/yaml">YAML Processing Demo</a></li>
    </ul>
    '''

@app.route('/execute')
def execute():
    # VULNERABILITY: Command injection
    cmd = request.args.get('cmd', 'echo "No command"')
    result = subprocess.call(cmd, shell=True)
    return f'Command executed: {cmd}'

@app.route('/yaml')
def yaml_process():
    # VULNERABILITY: Unsafe YAML loading
    data = request.args.get('data', 'key: value')
    parsed = yaml.load(data, Loader=yaml.FullLoader)
    return f'Parsed YAML: {parsed}'

@app.route('/pickle')
def pickle_load():
    # VULNERABILITY: Unsafe pickle loading
    data = request.args.get('data', '')
    if data:
        obj = pickle.loads(data.encode())
        return f'Unpickled: {obj}'
    return 'No data provided'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
