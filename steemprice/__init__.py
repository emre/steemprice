from flask import Flask
import click

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello World!"


@app.cli.command()
def update_rates():
    """Initialize the database."""
    click.echo('Updated rates.')