import waitress
from api import app
import click

@click.command()
@click.option('--port', default=8080, help='Port to listen on')
def run(port):
    waitress.serve(app, listen=f'*:{port}')

if __name__ == '__main__':
    run()