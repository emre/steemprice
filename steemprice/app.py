from flask import Flask, jsonify
import click
import redis
import settings

from update_rates import update, PoloniexAdapter, BittrexAdapter

app = Flask(__name__)

redis_conn = redis.Redis(**settings.REDIS_INFO)

@app.route("/")
@app.route("/api/v1/ticker")
def ticker():
    poloniex = PoloniexAdapter(redis_conn)
    bittrex = BittrexAdapter(redis_conn)
    data = {
        "poloniex": poloniex.get_rates(),
        "bittrex": bittrex.get_rates(),
        "last_update": redis_conn.get("last_update"),
    }

    return jsonify(data)


@app.cli.command()
def update_rates():
    """Update redis with the fresh rates."""
    update()
    click.echo('Updated rates.')
